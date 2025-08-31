"""
Logging configuration for Midscene Python
"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger


def setup_logger(
    level: str = "INFO",
    log_file: Optional[str] = None,
    rotation: str = "10 MB",
    retention: str = "7 days",
    format_string: Optional[str] = None
) -> None:
    """Setup logging configuration
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Log file path
        rotation: Log rotation size/time
        retention: Log retention period
        format_string: Custom format string
    """
    # Remove default logger
    logger.remove()
    
    # Default format
    if not format_string:
        format_string = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
    
    # Add console handler
    logger.add(
        sys.stderr,
        level=level,
        format=format_string,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_path,
            level=level,
            format=format_string,
            rotation=rotation,
            retention=retention,
            backtrace=True,
            diagnose=True
        )
    
    logger.info(f"Logger configured with level: {level}")


def get_logger(name: str):
    """Get logger instance
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logger.bind(name=name)