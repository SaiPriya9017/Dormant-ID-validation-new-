"""
Logger Configuration - Centralized logging setup.

This module provides:
- Colored console output
- File logging with rotation
- Structured log format
- Different log levels for console and file
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logger(
    name: str = "dormant-id-processor",
    log_dir: Path = Path("./logs"),
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Setup and configure logger with console and file handlers.

    Args:
        name: Logger name
        log_dir: Directory for log files
        console_level: Log level for console output
        file_level: Log level for file output
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup log files to keep

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Capture all levels
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create log directory
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Console handler with color support
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    
    # Console format - simpler, with colors
    console_format = ColoredFormatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)

    # File handler with rotation
    log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(file_level)
    
    # File format - more detailed
    file_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output."""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'

    def format(self, record):
        """Format log record with colors."""
        # Save original levelname
        levelname = record.levelname
        
        # Add color to levelname
        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}{self.BOLD}"
                f"{levelname}{self.RESET}"
            )
        
        # Format the message
        result = super().format(record)
        
        # Restore original levelname
        record.levelname = levelname
        
        return result


def get_logger(name: str = None) -> logging.Logger:
    """
    Get logger instance.

    Args:
        name: Logger name (uses root logger if None)

    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"dormant-id-processor.{name}")
    return logging.getLogger("dormant-id-processor")


# Example usage and testing
if __name__ == "__main__":
    # Setup logger
    logger = setup_logger()
    
    # Test different log levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test with module-specific logger
    module_logger = get_logger("test_module")
    module_logger.info("This is from a module-specific logger")

# Made with Bob
