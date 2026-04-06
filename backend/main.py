"""FastAPI main application with instant-start retrieval endpoints."""
import asyncio
import gzip
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from sse_starlette.sse import EventSourceResponse
import aiofiles

from backend.config import config
from backend.retrieval_worker import worker, RetrievalJob

# Initialize FastAPI app
app = FastAPI(
    title="Cloudant Retrieval System",
    description="High-performance data retrieval with instant start",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Validate configuration on startup."""
    try:
        config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please check your .env file")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Cloudant Retrieval System",
        "version": "2.0.0"
    }


@app.post("/api/retrieval/start")
async def start_retrieval(
    start_date: str = Query(..., description="ISO format start date"),
    end_date: str = Query(..., description="ISO format end date"),
    compress: bool = Query(False, description="Enable gzip compression")
):
    """
    Start a new retrieval job.
    
    CRITICAL: This endpoint returns IMMEDIATELY without waiting for data.
    The job runs in background and status is tracked via /api/retrieval/status.
    
    Args:
        start_date: Start date in ISO format
        end_date: End date in ISO format
        compress: Whether to compress output file
        
    Returns:
        Job information with job_id
    """
    try:
        # Validate dates
        datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format.")
        
    # Create job
    job = worker.create_job(start_date, end_date, compress)
    
    # Start job in background - THIS RETURNS IMMEDIATELY
    await worker.start_job(job.job_id)
    
    # Return job info instantly (before any data is fetched)
    return {
        "success": True,
        "job": job.to_dict(),
        "message": "Retrieval started"
    }


@app.get("/api/retrieval/status/{job_id}")
async def get_status(job_id: str):
    """
    Get current status of a retrieval job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Current job status and statistics
    """
    job = worker.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return job.to_dict()


@app.post("/api/retrieval/stop/{job_id}")
async def stop_retrieval(job_id: str):
    """
    Stop a running retrieval job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Success message
    """
    try:
        worker.stop_job(job_id)
        return {
            "success": True,
            "message": f"Job {job_id} stop requested"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/retrieval/stream/{job_id}")
async def stream_status(job_id: str):
    """
    Stream real-time status updates via Server-Sent Events.
    
    Args:
        job_id: Job identifier
        
    Returns:
        SSE stream of status updates
    """
    job = worker.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    async def event_generator():
        """Generate SSE events with job status."""
        while True:
            current_job = worker.get_job(job_id)
            if not current_job:
                break
                
            yield {
                "event": "status",
                "data": json.dumps(current_job.to_dict())
            }
            
            # Stop streaming if job is done
            if current_job.status in ["completed", "failed", "stopped"]:
                break
                
            await asyncio.sleep(1)
            
    return EventSourceResponse(event_generator())


@app.get("/api/retrieval/history")
async def get_history():
    """
    Get list of all retrieval jobs.
    
    Returns:
        List of job information
    """
    jobs = await worker.list_jobs()
    return {
        "jobs": [job.to_dict() for job in jobs],
        "total": len(jobs)
    }


@app.get("/api/retrieval/download/{job_id}")
async def download_file(job_id: str):
    """
    Download the data file for a completed job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        File download response
    """
    job = worker.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    extension = ".jsonl.gz" if job.compress else ".jsonl"
    filepath = config.DATA_DIR / f"{job_id}{extension}"
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File not found")
        
    media_type = "application/gzip" if job.compress else "application/x-ndjson"
    
    return FileResponse(
        path=filepath,
        media_type=media_type,
        filename=f"{job_id}{extension}"
    )


@app.get("/api/retrieval/view/{job_id}")
async def view_data(
    job_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Records per page")
):
    """
    View paginated data from a job file.
    
    Args:
        job_id: Job identifier
        page: Page number (1-based)
        page_size: Records per page
        
    Returns:
        Paginated data
    """
    job = worker.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    extension = ".jsonl.gz" if job.compress else ".jsonl"
    filepath = config.DATA_DIR / f"{job_id}{extension}"
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File not found")
        
    # Calculate skip
    skip = (page - 1) * page_size
    
    # Read paginated data
    rows = []
    line_count = 0
    
    try:
        if job.compress:
            with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                for line in f:
                    if line_count >= skip and len(rows) < page_size:
                        rows.append(json.loads(line))
                    line_count += 1
                    if len(rows) >= page_size:
                        break
        else:
            async with aiofiles.open(filepath, mode='r', encoding='utf-8') as f:
                async for line in f:
                    if line_count >= skip and len(rows) < page_size:
                        rows.append(json.loads(line))
                    line_count += 1
                    if len(rows) >= page_size:
                        break
                        
        return {
            "rows": rows,
            "page": page,
            "page_size": page_size,
            "total_lines": line_count,
            "has_more": line_count > skip + page_size
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Made with Bob
