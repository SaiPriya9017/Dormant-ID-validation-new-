"""Job persistence for maintaining history across restarts."""
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

from backend.config import config

logger = logging.getLogger(__name__)


class JobPersistence:
    """Handles saving and loading job history."""
    
    def __init__(self):
        """Initialize persistence."""
        self.history_file = config.DATA_DIR / "job_history.json"
        
    async def save_job(self, job_data: Dict):
        """
        Save a job to history.
        
        Args:
            job_data: Job dictionary
        """
        try:
            # Load existing history
            history = await self.load_history()
            
            # Update or add job
            job_id = job_data.get("job_id")
            existing_index = next((i for i, j in enumerate(history) if j.get("job_id") == job_id), None)
            
            if existing_index is not None:
                history[existing_index] = job_data
            else:
                history.append(job_data)
            
            # Save to file
            await self._write_history(history)
            
        except Exception as e:
            logger.error(f"Error saving job: {e}")
            
    async def load_history(self) -> List[Dict]:
        """
        Load job history from file.
        
        Returns:
            List of job dictionaries
        """
        try:
            if not self.history_file.exists():
                return []
                
            async with asyncio.Lock():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    return history if isinstance(history, list) else []
                    
        except Exception as e:
            logger.error(f"Error loading history: {e}")
            return []
            
    async def _write_history(self, history: List[Dict]):
        """Write history to file."""
        try:
            async with asyncio.Lock():
                with open(self.history_file, 'w', encoding='utf-8') as f:
                    json.dump(history, f, indent=2, default=str)
                    
        except Exception as e:
            logger.error(f"Error writing history: {e}")
            
    async def delete_job(self, job_id: str):
        """
        Delete a job from history.
        
        Args:
            job_id: Job identifier
        """
        try:
            history = await self.load_history()
            history = [j for j in history if j.get("job_id") != job_id]
            await self._write_history(history)
            
        except Exception as e:
            logger.error(f"Error deleting job: {e}")


# Global persistence instance
persistence = JobPersistence()

# Made with Bob
