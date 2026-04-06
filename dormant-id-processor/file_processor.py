"""
File Processor - Handles streaming reading of multiple JSONL files.

Features:
- Streaming line-by-line reading (no full file load)
- Multi-file processing
- Memory efficient
- Progress tracking
"""
import asyncio
import aiofiles
import json
import logging
from pathlib import Path
from typing import AsyncIterator, List
from tqdm import tqdm

from config import config

logger = logging.getLogger(__name__)


class FileProcessor:
    """Handles streaming processing of JSONL files."""
    
    def __init__(self, input_dir: Path = None):
        """
        Initialize file processor.
        
        Args:
            input_dir: Directory containing JSONL files
        """
        self.input_dir = input_dir or config.INPUT_DIR
        
    def get_jsonl_files(self) -> List[Path]:
        """
        Get all JSONL files from input directory.
        
        Returns:
            List of Path objects for JSONL files
        """
        if not self.input_dir.exists():
            logger.warning(f"Input directory does not exist: {self.input_dir}")
            return []
            
        files = list(self.input_dir.glob("*.jsonl"))
        logger.info(f"Found {len(files)} JSONL files in {self.input_dir}")
        
        return sorted(files)
        
    async def count_lines(self, filepath: Path) -> int:
        """
        Count total lines in a file (for progress tracking).
        
        Args:
            filepath: Path to JSONL file
            
        Returns:
            Number of lines in file
        """
        count = 0
        try:
            async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
                async for _ in f:
                    count += 1
        except Exception as e:
            logger.error(f"Error counting lines in {filepath}: {e}")
            
        return count
        
    async def stream_records(
        self,
        filepath: Path,
        skip_lines: int = 0
    ) -> AsyncIterator[tuple[str, dict]]:
        """
        Stream full records with user IDs from a JSONL file line by line.
        
        Args:
            filepath: Path to JSONL file
            skip_lines: Number of lines to skip (for resume)
            
        Yields:
            Tuple of (user_id, original_record_dict)
        """
        if not filepath.exists():
            logger.error(f"File not found: {filepath}")
            return
            
        logger.info(f"Streaming IDs from {filepath.name}")
        
        line_num = 0
        processed = 0
        errors = 0
        
        try:
            async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
                async for line in f:
                    line_num += 1
                    
                    # Skip lines if resuming
                    if line_num <= skip_lines:
                        continue
                        
                    line = line.strip()
                    if not line:
                        continue
                        
                    try:
                        data = json.loads(line)
                        # Support multiple field names: "value", "user_id", or "id"
                        user_id = data.get("value") or data.get("user_id") or data.get("id")
                        
                        if user_id:
                            processed += 1
                            yield (str(user_id), data)  # Return both ID and full record
                        else:
                            errors += 1
                            logger.warning(f"No 'value', 'user_id', or 'id' field in line {line_num}")
                            
                    except json.JSONDecodeError as e:
                        errors += 1
                        logger.error(f"Invalid JSON at line {line_num}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error reading file {filepath}: {e}")
            raise
            
        logger.info(
            f"Finished streaming {filepath.name}: "
            f"{processed} IDs, {errors} errors"
        )
        
    async def process_file_in_batches(
        self,
        filepath: Path,
        batch_size: int,
        skip_lines: int = 0
    ) -> AsyncIterator[List[tuple[str, dict]]]:
        """
        Process a file and yield batches of (user_id, record) tuples.
        
        Args:
            filepath: Path to JSONL file
            batch_size: Number of records per batch
            skip_lines: Number of lines to skip (for resume)
            
        Yields:
            Batches of (user_id, original_record) tuples
        """
        batch = []
        
        async for user_id, record in self.stream_records(filepath, skip_lines):
            batch.append((user_id, record))
            
            if len(batch) >= batch_size:
                yield batch
                batch = []
                
        # Yield remaining records
        if batch:
            yield batch
            
    async def get_file_info(self, filepath: Path) -> dict:
        """
        Get information about a JSONL file.
        
        Args:
            filepath: Path to JSONL file
            
        Returns:
            Dictionary with file metadata
        """
        info = {
            "filename": filepath.name,
            "path": str(filepath),
            "exists": filepath.exists(),
            "size_bytes": 0,
            "total_lines": 0
        }
        
        if filepath.exists():
            info["size_bytes"] = filepath.stat().st_size
            info["total_lines"] = await self.count_lines(filepath)
            
        return info
        
    async def validate_file(self, filepath: Path) -> bool:
        """
        Validate that a file is a proper JSONL file.
        
        Args:
            filepath: Path to JSONL file
            
        Returns:
            True if valid, False otherwise
        """
        if not filepath.exists():
            logger.error(f"File does not exist: {filepath}")
            return False
            
        if filepath.suffix != ".jsonl":
            logger.error(f"File is not a JSONL file: {filepath}")
            return False
            
        # Check first few lines
        try:
            async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
                for i in range(min(10, await self.count_lines(filepath))):
                    line = await f.readline()
                    if line.strip():
                        json.loads(line)  # Validate JSON
                        
            return True
            
        except Exception as e:
            logger.error(f"File validation failed for {filepath}: {e}")
            return False

# Made with Bob
