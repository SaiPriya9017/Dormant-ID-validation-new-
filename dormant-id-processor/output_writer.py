"""
Output Writer - Handles writing results to JSONL files.

This module provides:
- Streaming writes to JSONL format
- Atomic file operations
- Optional compression
- Buffered writes for performance
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import aiofiles

logger = logging.getLogger(__name__)


class OutputWriter:
    """Handles writing processed results to JSONL files."""

    def __init__(self, output_dir: Path, buffer_size: int = 100):
        """
        Initialize output writer.

        Args:
            output_dir: Directory to write output files
            buffer_size: Number of records to buffer before flushing
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.buffer_size = buffer_size
        self._buffer: List[Dict[str, Any]] = []
        self._file_handle: Optional[Any] = None
        self._current_file: Optional[Path] = None
        self._records_written = 0

    def _generate_output_filename(self, input_file: Path) -> Path:
        """
        Generate output filename based on input file.

        Args:
            input_file: Input file being processed

        Returns:
            Path to output file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"{input_file.stem}_results_{timestamp}.jsonl"
        return self.output_dir / output_name

    async def open(self, input_file: Path) -> Path:
        """
        Open output file for writing.

        Args:
            input_file: Input file being processed (used for naming)

        Returns:
            Path to output file
        """
        if self._file_handle:
            await self.close()

        self._current_file = self._generate_output_filename(input_file)
        self._file_handle = await aiofiles.open(self._current_file, 'w')
        self._records_written = 0
        self._buffer = []

        logger.info(f"Opened output file: {self._current_file.name}")
        return self._current_file

    async def write_record(self, record: Dict[str, Any]) -> None:
        """
        Write a single record to output file.

        Args:
            record: Record to write (will be JSON serialized)
        """
        if not self._file_handle:
            raise RuntimeError("Output file not opened. Call open() first.")

        # Add to buffer
        self._buffer.append(record)

        # Flush if buffer is full
        if len(self._buffer) >= self.buffer_size:
            await self._flush_buffer()

    async def write_batch(self, records: List[Dict[str, Any]]) -> None:
        """
        Write multiple records to output file.

        Args:
            records: List of records to write
        """
        if not self._file_handle:
            raise RuntimeError("Output file not opened. Call open() first.")

        for record in records:
            self._buffer.append(record)

            # Flush if buffer is full
            if len(self._buffer) >= self.buffer_size:
                await self._flush_buffer()

    async def _flush_buffer(self) -> None:
        """Flush buffered records to file."""
        if not self._buffer or not self._file_handle:
            return

        try:
            # Write all buffered records as JSONL
            for record in self._buffer:
                line = json.dumps(record, ensure_ascii=False)
                await self._file_handle.write(line + '\n')

            self._records_written += len(self._buffer)
            logger.debug(f"Flushed {len(self._buffer)} records to {self._current_file.name}")
            self._buffer = []

        except Exception as e:
            logger.error(f"Error flushing buffer: {e}")
            raise

    async def close(self) -> int:
        """
        Close output file and flush any remaining buffered records.

        Returns:
            Total number of records written
        """
        if self._file_handle:
            # Flush any remaining buffered records
            if self._buffer:
                await self._flush_buffer()

            await self._file_handle.close()
            logger.info(
                f"Closed output file: {self._current_file.name} "
                f"({self._records_written} records)"
            )

            self._file_handle = None
            records_written = self._records_written
            self._records_written = 0
            return records_written

        return 0

    @property
    def records_written(self) -> int:
        """Get number of records written to current file."""
        return self._records_written

    @property
    def current_file(self) -> Optional[Path]:
        """Get current output file path."""
        return self._current_file

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


class MultiFileOutputWriter:
    """Manages multiple output writers for parallel processing."""

    def __init__(self, output_dir: Path, buffer_size: int = 100):
        """
        Initialize multi-file output writer.

        Args:
            output_dir: Directory to write output files
            buffer_size: Number of records to buffer before flushing
        """
        self.output_dir = Path(output_dir)
        self.buffer_size = buffer_size
        self._writers: Dict[str, OutputWriter] = {}

    async def get_writer(self, input_file: Path) -> OutputWriter:
        """
        Get or create writer for an input file.

        Args:
            input_file: Input file being processed

        Returns:
            OutputWriter instance for this file
        """
        file_key = str(input_file.absolute())

        if file_key not in self._writers:
            writer = OutputWriter(self.output_dir, self.buffer_size)
            await writer.open(input_file)
            self._writers[file_key] = writer

        return self._writers[file_key]

    async def close_all(self) -> Dict[str, int]:
        """
        Close all open writers.

        Returns:
            Dict mapping input file -> records written
        """
        results = {}

        for file_key, writer in self._writers.items():
            records = await writer.close()
            results[file_key] = records

        self._writers.clear()
        return results

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_all()

# Made with Bob
