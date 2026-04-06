"""
Checkpoint Manager - Handles per-file checkpointing for resume capability.

This module provides:
- Save/load checkpoint state for each input file
- Track progress (lines processed, last bookmark)
- Enable resume from last successful position
- Atomic checkpoint updates
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class CheckpointManager:
    """Manages checkpoints for resumable processing."""

    def __init__(self, checkpoint_dir: Path):
        """
        Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory to store checkpoint files
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def _get_checkpoint_path(self, input_file: Path) -> Path:
        """
        Get checkpoint file path for an input file.

        Args:
            input_file: Input file being processed

        Returns:
            Path to checkpoint file
        """
        # Create checkpoint filename based on input file
        checkpoint_name = f"{input_file.stem}_checkpoint.json"
        return self.checkpoint_dir / checkpoint_name

    def save_checkpoint(
        self,
        input_file: Path,
        lines_processed: int,
        records_written: int,
        last_user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Save checkpoint for a file.

        Args:
            input_file: Input file being processed
            lines_processed: Number of lines processed so far
            records_written: Number of records written to output
            last_user_id: Last user ID processed (optional)
            metadata: Additional metadata to store (optional)
        """
        checkpoint_path = self._get_checkpoint_path(input_file)

        checkpoint_data = {
            "input_file": str(input_file.absolute()),
            "lines_processed": lines_processed,
            "records_written": records_written,
            "last_user_id": last_user_id,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        try:
            # Write atomically using temp file
            temp_path = checkpoint_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
            
            # Atomic rename
            temp_path.replace(checkpoint_path)
            
            logger.debug(
                f"Saved checkpoint for {input_file.name}: "
                f"{lines_processed} lines, {records_written} records"
            )

        except Exception as e:
            logger.error(f"Error saving checkpoint for {input_file.name}: {e}")
            raise

    def load_checkpoint(self, input_file: Path) -> Optional[Dict[str, Any]]:
        """
        Load checkpoint for a file.

        Args:
            input_file: Input file to load checkpoint for

        Returns:
            Checkpoint data dict or None if no checkpoint exists
        """
        checkpoint_path = self._get_checkpoint_path(input_file)

        if not checkpoint_path.exists():
            logger.debug(f"No checkpoint found for {input_file.name}")
            return None

        try:
            with open(checkpoint_path, 'r') as f:
                checkpoint_data = json.load(f)
            
            logger.info(
                f"Loaded checkpoint for {input_file.name}: "
                f"{checkpoint_data['lines_processed']} lines processed"
            )
            return checkpoint_data

        except Exception as e:
            logger.error(f"Error loading checkpoint for {input_file.name}: {e}")
            return None

    def delete_checkpoint(self, input_file: Path) -> None:
        """
        Delete checkpoint for a file (called when processing completes).

        Args:
            input_file: Input file whose checkpoint should be deleted
        """
        checkpoint_path = self._get_checkpoint_path(input_file)

        if checkpoint_path.exists():
            try:
                checkpoint_path.unlink()
                logger.info(f"Deleted checkpoint for {input_file.name}")
            except Exception as e:
                logger.error(f"Error deleting checkpoint for {input_file.name}: {e}")

    def has_checkpoint(self, input_file: Path) -> bool:
        """
        Check if a checkpoint exists for a file.

        Args:
            input_file: Input file to check

        Returns:
            True if checkpoint exists, False otherwise
        """
        checkpoint_path = self._get_checkpoint_path(input_file)
        return checkpoint_path.exists()

    def list_checkpoints(self) -> Dict[str, Dict[str, Any]]:
        """
        List all existing checkpoints.

        Returns:
            Dict mapping input file path -> checkpoint data
        """
        checkpoints = {}

        for checkpoint_file in self.checkpoint_dir.glob("*_checkpoint.json"):
            try:
                with open(checkpoint_file, 'r') as f:
                    data = json.load(f)
                    input_file = data.get("input_file")
                    if input_file:
                        checkpoints[input_file] = data
            except Exception as e:
                logger.error(f"Error reading checkpoint {checkpoint_file}: {e}")

        return checkpoints

    def get_resume_position(self, input_file: Path) -> int:
        """
        Get the line number to resume from for a file.

        Args:
            input_file: Input file to check

        Returns:
            Line number to resume from (0 if no checkpoint)
        """
        checkpoint = self.load_checkpoint(input_file)
        if checkpoint:
            return checkpoint.get("lines_processed", 0)
        return 0

    def clear_all_checkpoints(self) -> int:
        """
        Clear all checkpoints (use with caution).

        Returns:
            Number of checkpoints deleted
        """
        count = 0
        for checkpoint_file in self.checkpoint_dir.glob("*_checkpoint.json"):
            try:
                checkpoint_file.unlink()
                count += 1
            except Exception as e:
                logger.error(f"Error deleting checkpoint {checkpoint_file}: {e}")

        logger.info(f"Cleared {count} checkpoints")
        return count

# Made with Bob
