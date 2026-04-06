"""Background worker for high-performance data retrieval with instant start."""
import asyncio
import time
from typing import Dict, Optional
from datetime import datetime
import logging
from uuid import uuid4

from backend.cloudant_client import CloudantClient
from backend.file_writer import StreamingFileWriter
from backend.config import config
from backend.job_persistence import persistence

logger = logging.getLogger(__name__)


class RetrievalJob:
    """Represents a single retrieval job."""
    
    def __init__(
        self,
        job_id: str,
        start_date: str,
        end_date: str,
        compress: bool = False
    ):
        self.job_id = job_id
        self.start_date = start_date
        self.end_date = end_date
        self.compress = compress
        
        # Status tracking
        self.status = "initializing"
        self.records_fetched = 0
        self.records_per_sec = 0.0
        self.progress_percent = 0.0
        self.estimated_time_remaining = 0
        self.estimated_total_records = 0
        self.error: Optional[str] = None
        
        # Timing
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        
        # Control
        self.should_stop = False
        self.task: Optional[asyncio.Task] = None
        
    def to_dict(self) -> Dict:
        """Convert job to dictionary for API responses."""
        return {
            "job_id": self.job_id,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "status": self.status,
            "records_fetched": self.records_fetched,
            "records_per_sec": round(self.records_per_sec, 2),
            "progress_percent": round(self.progress_percent, 2),
            "estimated_time_remaining": self.estimated_time_remaining,
            "estimated_total_records": self.estimated_total_records,
            "error": self.error,
            "compress": self.compress,
            "start_time": self.start_time,
            "end_time": self.end_time
        }


class RetrievalWorker:
    """Background worker for data retrieval."""
    
    def __init__(self):
        """Initialize worker."""
        self.jobs: Dict[str, RetrievalJob] = {}
        self._loaded = False
        
    async def _load_history(self):
        """Load job history from disk on first access."""
        if self._loaded:
            return
            
        try:
            history = await persistence.load_history()
            for job_data in history:
                job = RetrievalJob(
                    job_data["job_id"],
                    job_data["start_date"],
                    job_data["end_date"],
                    job_data.get("compress", False)
                )
                # Restore job state
                job.status = job_data.get("status", "unknown")
                job.records_fetched = job_data.get("records_fetched", 0)
                job.records_per_sec = job_data.get("records_per_sec", 0.0)
                job.progress_percent = job_data.get("progress_percent", 0.0)
                job.error = job_data.get("error")
                job.start_time = job_data.get("start_time")
                job.end_time = job_data.get("end_time")
                
                self.jobs[job.job_id] = job
                
            self._loaded = True
            logger.info(f"Loaded {len(history)} jobs from history")
            
        except Exception as e:
            logger.error(f"Error loading history: {e}")
            self._loaded = True
        
    def create_job(
        self,
        start_date: str,
        end_date: str,
        compress: bool = False
    ) -> RetrievalJob:
        """
        Create a new retrieval job.
        
        Args:
            start_date: ISO format start date
            end_date: ISO format end date
            compress: Whether to compress output
            
        Returns:
            Created job instance
        """
        job_id = f"job_{uuid4().hex[:12]}"
        job = RetrievalJob(job_id, start_date, end_date, compress)
        self.jobs[job_id] = job
        return job
        
    async def start_job(self, job_id: str):
        """
        Start a retrieval job in background.
        
        CRITICAL: This method returns IMMEDIATELY without waiting for first fetch.
        The actual retrieval runs in a background task.
        
        Args:
            job_id: Job identifier
        """
        job = self.jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
            
        if job.task and not job.task.done():
            raise ValueError(f"Job {job_id} is already running")
            
        # Create background task - THIS RETURNS IMMEDIATELY
        job.task = asyncio.create_task(self._run_retrieval(job))
        
        # Update status immediately (before any data is fetched)
        job.status = "running"
        job.start_time = time.time()
        
        # Save to history
        await persistence.save_job(job.to_dict())
        
    async def _run_retrieval(self, job: RetrievalJob):
        """
        Run the actual retrieval process.
        
        This runs in background and does NOT block the API response.
        
        Args:
            job: Job instance
        """
        writer = StreamingFileWriter(job.job_id, job.start_date, job.end_date, job.compress)
        
        try:
            # Load checkpoint if exists
            checkpoint = await writer.load_checkpoint()
            start_bookmark = checkpoint.get("bookmark") if checkpoint else None
            
            if checkpoint:
                job.records_fetched = checkpoint.get("records_written", 0)
                logger.info(f"Resuming job {job.job_id} from checkpoint")
                
            async with CloudantClient() as client:
                batch_count = 0
                last_update = time.time()
                
                async for batch in client.stream_all(
                    start_date=job.start_date,
                    end_date=job.end_date,
                    batch_size=config.BATCH_SIZE
                ):
                    # Check stop signal
                    if job.should_stop:
                        job.status = "stopped"
                        break
                        
                    # Write batch
                    written = await writer.write_batch(batch)
                    job.records_fetched += written
                    batch_count += 1
                    
                    # Update stats every second
                    now = time.time()
                    if now - last_update >= 1.0:
                        elapsed = now - (job.start_time or now)
                        job.records_per_sec = job.records_fetched / elapsed if elapsed > 0 else 0
                        
                        # Calculate estimated time remaining
                        if job.records_per_sec > 0 and job.estimated_total_records > 0:
                            remaining_records = job.estimated_total_records - job.records_fetched
                            job.estimated_time_remaining = int(remaining_records / job.records_per_sec)
                            job.progress_percent = (job.records_fetched / job.estimated_total_records) * 100
                        elif job.records_per_sec > 0:
                            # Estimate based on current rate (assume similar to what we've seen)
                            # This is a rough estimate when we don't know total
                            job.estimated_time_remaining = int(job.records_fetched / job.records_per_sec)
                            
                        last_update = now
                        
                    # Save checkpoint every 10 batches
                    if batch_count % 10 == 0:
                        await writer.save_checkpoint(writer.last_bookmark)
                        
                # Final checkpoint
                await writer.save_checkpoint(writer.last_bookmark)
                
                if not job.should_stop:
                    job.status = "completed"
                    
        except Exception as e:
            logger.error(f"Error in retrieval job {job.job_id}: {e}", exc_info=True)
            job.status = "failed"
            job.error = str(e)
            
        finally:
            job.end_time = time.time()
            # Save final state to history
            await persistence.save_job(job.to_dict())
            
    def stop_job(self, job_id: str):
        """
        Stop a running job.
        
        Args:
            job_id: Job identifier
        """
        job = self.jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
            
        job.should_stop = True
        
    def get_job(self, job_id: str) -> Optional[RetrievalJob]:
        """Get job by ID."""
        return self.jobs.get(job_id)
        
    async def list_jobs(self) -> list[RetrievalJob]:
        """List all jobs."""
        await self._load_history()
        return list(self.jobs.values())


# Global worker instance
worker = RetrievalWorker()

# Made with Bob
