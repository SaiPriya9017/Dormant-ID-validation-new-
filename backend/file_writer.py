"""Streaming file writer with checkpointing for high-performance data storage."""
import asyncio
import aiofiles
import gzip
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging

from backend.config import config

logger = logging.getLogger(__name__)


class StreamingFileWriter:
    """Async file writer with streaming and checkpointing."""
    
    def __init__(self, job_id: str, start_date: str, end_date: str, compress: bool = False):
        """
        Initialize writer.
        
        Args:
            job_id: Unique job identifier
            start_date: Start date for filename
            end_date: End date for filename
            compress: Whether to use gzip compression
        """
        self.job_id = job_id
        self.compress = compress
        self.extension = ".jsonl.gz" if compress else ".jsonl"
        
        # Generate filename with month and year
        from datetime import datetime
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            filename = f"{start_dt.strftime('%Y-%m')}_{end_dt.strftime('%Y-%m')}_{job_id}{self.extension}"
        except:
            filename = f"{job_id}{self.extension}"
            
        self.filepath = config.DATA_DIR / filename
        self.checkpoint_path = config.CHECKPOINT_DIR / f"{job_id}.checkpoint"
        self.records_written = 0
        self.last_bookmark: Optional[str] = None
        
    async def write_batch(self, records: List[Dict]) -> int:
        """
        Write a batch of records to file (append mode).
        
        Args:
            records: List of record dictionaries
            
        Returns:
            Number of records written
        """
        if not records:
            return 0
            
        try:
            if self.compress:
                await self._write_compressed(records)
            else:
                await self._write_uncompressed(records)
                
            self.records_written += len(records)
            return len(records)
            
        except Exception as e:
            logger.error(f"Error writing batch: {e}")
            raise
            
    async def _write_uncompressed(self, records: List[Dict]):
        """Write records to uncompressed JSONL file."""
        async with aiofiles.open(self.filepath, mode='a', encoding='utf-8') as f:
            for record in records:
                line = json.dumps(record, ensure_ascii=False) + '\n'
                await f.write(line)
                
    async def _write_compressed(self, records: List[Dict]):
        """Write records to gzip-compressed JSONL file."""
        # For gzip, we need to use sync operations in executor
        def write_sync():
            with gzip.open(self.filepath, mode='at', encoding='utf-8') as f:
                for record in records:
                    line = json.dumps(record, ensure_ascii=False) + '\n'
                    f.write(line)
                    
        await asyncio.get_event_loop().run_in_executor(None, write_sync)
        
    async def save_checkpoint(self, bookmark: Optional[str]):
        """
        Save checkpoint for resume capability.
        
        Args:
            bookmark: Current pagination bookmark
        """
        self.last_bookmark = bookmark
        checkpoint_data = {
            "job_id": self.job_id,
            "records_written": self.records_written,
            "bookmark": bookmark,
            "timestamp": datetime.utcnow().isoformat(),
            "filepath": str(self.filepath)
        }
        
        async with aiofiles.open(self.checkpoint_path, mode='w', encoding='utf-8') as f:
            await f.write(json.dumps(checkpoint_data, indent=2))
            
    async def load_checkpoint(self) -> Optional[Dict]:
        """
        Load checkpoint if exists.
        
        Returns:
            Checkpoint data or None
        """
        if not self.checkpoint_path.exists():
            return None
            
        try:
            async with aiofiles.open(self.checkpoint_path, mode='r', encoding='utf-8') as f:
                content = await f.read()
                checkpoint = json.loads(content)
                self.records_written = checkpoint.get("records_written", 0)
                self.last_bookmark = checkpoint.get("bookmark")
                return checkpoint
        except Exception as e:
            logger.error(f"Error loading checkpoint: {e}")
            return None
            
    def get_stats(self) -> Dict:
        """Get current writer statistics."""
        return {
            "job_id": self.job_id,
            "records_written": self.records_written,
            "filepath": str(self.filepath),
            "file_exists": self.filepath.exists(),
            "file_size": self.filepath.stat().st_size if self.filepath.exists() else 0,
            "compressed": self.compress
        }

# Made with Bob
