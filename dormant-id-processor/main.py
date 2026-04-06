"""
Main CLI Application - Orchestrates the dormant ID processing pipeline.

This is the entry point that:
- Parses command-line arguments
- Initializes all components
- Manages the processing workflow
- Handles errors and cleanup
"""

import asyncio
import sys
from pathlib import Path
from typing import List
import click
from tqdm import tqdm
import aiofiles

from config import Config
from logger import setup_logger, get_logger
from api_service import APIService
from file_processor import FileProcessor
from checkpoint_manager import CheckpointManager
from output_writer import OutputWriter


# Setup logger
logger = setup_logger(
    log_dir=Config.LOG_DIR,
    console_level=20,  # INFO
    file_level=10      # DEBUG
)


class DormantIDProcessor:
    """Main processor that orchestrates the entire pipeline."""

    def __init__(
        self,
        input_dir: Path,
        batch_size: int = 50,
        concurrency: int = 5,
        resume: bool = True
    ):
        """
        Initialize processor.

        Args:
            input_dir: Directory containing input JSONL files
            batch_size: Number of IDs to process per batch
            concurrency: Number of concurrent API calls
            resume: Whether to resume from checkpoints
        """
        self.input_dir = Path(input_dir)
        self.batch_size = batch_size
        self.concurrency = concurrency
        self.resume = resume

        # Initialize components
        self.file_processor = FileProcessor(self.input_dir)
        self.checkpoint_manager = CheckpointManager(Config.CHECKPOINT_DIR)
        self.semaphore = asyncio.Semaphore(concurrency)

        # Statistics
        self.total_processed = 0
        self.total_active = 0
        self.total_dormant = 0
        self.total_errors = 0

    async def process_file(
        self,
        file_path: Path,
        api_service: APIService,
        writer_active: OutputWriter,
        writer_dormant: OutputWriter
    ) -> None:
        """
        Process a single input file and write to two separate output files.

        Args:
            file_path: Path to input JSONL file
            api_service: API service instance
            writer_active: Output writer for active users (to-not-be-deleted)
            writer_dormant: Output writer for dormant users (to-be-deleted)
        """
        logger.info(f"Processing file: {file_path.name}")

        # Check for checkpoint
        skip_lines = 0
        if self.resume:
            skip_lines = self.checkpoint_manager.get_resume_position(file_path)
            if skip_lines > 0:
                logger.info(f"Resuming from line {skip_lines}")

        # Count total lines for progress bar
        total_lines = await self.file_processor.count_lines(file_path)
        remaining_lines = total_lines - skip_lines

        # Process file in batches
        batch_count = 0
        records_active = 0
        records_dormant = 0

        with tqdm(
            total=remaining_lines,
            desc=f"Processing {file_path.name}",
            unit="records"
        ) as pbar:
            async for batch in self.file_processor.process_file_in_batches(
                file_path,
                self.batch_size,
                skip_lines
            ):
                batch_count += 1

                # Process batch with API
                try:
                    async with self.semaphore:
                        results = await api_service.process_batch(batch)

                    # Write to appropriate files
                    if results["active"]:
                        await writer_active.write_batch(results["active"])
                        records_active += len(results["active"])
                        self.total_active += len(results["active"])
                    
                    if results["dormant"]:
                        await writer_dormant.write_batch(results["dormant"])
                        records_dormant += len(results["dormant"])
                        self.total_dormant += len(results["dormant"])

                    self.total_processed += len(batch)

                    # Save checkpoint
                    lines_processed = skip_lines + (batch_count * self.batch_size)
                    self.checkpoint_manager.save_checkpoint(
                        file_path,
                        lines_processed,
                        records_active + records_dormant,
                        last_user_id=batch[-1][0] if batch else None
                    )

                    # Update progress bar
                    pbar.update(len(batch))

                except Exception as e:
                    logger.error(f"Error processing batch {batch_count}: {e}")
                    self.total_errors += len(batch)
                    continue

        # Delete checkpoint (processing complete)
        self.checkpoint_manager.delete_checkpoint(file_path)

        logger.info(
            f"Completed {file_path.name}: "
            f"{records_active} active, {records_dormant} dormant"
        )

    async def process_all_files(self) -> None:
        """Process all JSONL files in input directory."""
        # Validate configuration
        Config.validate()
        Config.ensure_directories()

        # Find all JSONL files
        input_files = list(self.input_dir.glob("*.jsonl"))

        if not input_files:
            logger.error(f"No JSONL files found in {self.input_dir}")
            return

        logger.info(f"Found {len(input_files)} files to process")

        # Initialize API service and two output writers
        async with APIService(Config) as api_service:
            writer_active = OutputWriter(Config.OUTPUT_DIR)
            writer_dormant = OutputWriter(Config.OUTPUT_DIR)

            try:
                # Open output files with specific names
                active_file = Config.OUTPUT_DIR / "to-not-be-deleted.jsonl"
                dormant_file = Config.OUTPUT_DIR / "to-be-deleted.jsonl"
                
                # Open writers manually with specific filenames
                writer_active._current_file = active_file
                writer_active._file_handle = await aiofiles.open(active_file, 'w')
                writer_active._records_written = 0
                writer_active._buffer = []
                
                writer_dormant._current_file = dormant_file
                writer_dormant._file_handle = await aiofiles.open(dormant_file, 'w')
                writer_dormant._records_written = 0
                writer_dormant._buffer = []
                
                logger.info(f"Writing active users to: {active_file.name}")
                logger.info(f"Writing dormant users to: {dormant_file.name}")

                # Process each file
                for file_path in input_files:
                    try:
                        await self.process_file(file_path, api_service, writer_active, writer_dormant)
                    except Exception as e:
                        logger.error(f"Error processing {file_path.name}: {e}")
                        continue

            finally:
                await writer_active.close()
                await writer_dormant.close()

        # Print final statistics
        self._print_statistics()

    def _print_statistics(self) -> None:
        """Print final processing statistics."""
        logger.info("=" * 60)
        logger.info("PROCESSING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total IDs Processed: {self.total_processed}")
        logger.info(f"Active Users: {self.total_active}")
        logger.info(f"Dormant Users: {self.total_dormant}")
        logger.info(f"Errors/Not Found: {self.total_errors}")
        logger.info("=" * 60)


@click.command()
@click.option(
    '--input-dir',
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default='./input',
    help='Directory containing input JSONL files'
)
@click.option(
    '--batch-size',
    type=int,
    default=50,
    help='Number of IDs to process per batch'
)
@click.option(
    '--concurrency',
    type=int,
    default=5,
    help='Number of concurrent API calls'
)
@click.option(
    '--no-resume',
    is_flag=True,
    help='Start from beginning (ignore checkpoints)'
)
@click.option(
    '--clear-checkpoints',
    is_flag=True,
    help='Clear all checkpoints before starting'
)
def main(
    input_dir: str,
    batch_size: int,
    concurrency: int,
    no_resume: bool,
    clear_checkpoints: bool
):
    """
    Dormant ID Processor - Process user IDs and check ACTIVE/DORMANT status.

    This tool:
    - Reads user IDs from JSONL files
    - Retrieves emails via IBM Login API
    - Checks user status (ACTIVE/DORMANT)
    - Writes results to output JSONL files
    - Supports resume from checkpoints
    """
    logger.info("=" * 60)
    logger.info("DORMANT ID PROCESSOR")
    logger.info("=" * 60)
    logger.info(f"Input Directory: {input_dir}")
    logger.info(f"Batch Size: {batch_size}")
    logger.info(f"Concurrency: {concurrency}")
    logger.info(f"Resume: {not no_resume}")
    logger.info("=" * 60)

    # Clear checkpoints if requested
    if clear_checkpoints:
        checkpoint_manager = CheckpointManager(Config.CHECKPOINT_DIR)
        count = checkpoint_manager.clear_all_checkpoints()
        logger.info(f"Cleared {count} checkpoints")

    # Create processor
    processor = DormantIDProcessor(
        input_dir=input_dir,
        batch_size=batch_size,
        concurrency=concurrency,
        resume=not no_resume
    )

    # Run processing
    try:
        asyncio.run(processor.process_all_files())
    except KeyboardInterrupt:
        logger.warning("Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
