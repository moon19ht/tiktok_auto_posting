"""
TikTok Auto Posting - Logger Module

로깅 유틸리티 모듈
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

try:
    from colorlog import ColoredFormatter
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False

from .config import config


def setup_logger(name: str = "tiktok_auto") -> logging.Logger:
    """
    Setup and configure logger
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    # Ensure logs directory exists
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.LOG_LEVEL.upper(), logging.INFO))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    if HAS_COLORLOG:
        console_format = ColoredFormatter(
            "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s%(reset)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
    else:
        console_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler
    log_filename = f"tiktok_auto_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(
        config.LOGS_DIR / log_filename,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    
    file_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    return logger


# Default logger instance
logger = setup_logger()
