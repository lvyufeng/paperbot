"""Logging configuration for PaperGen."""

import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler


def setup_logging(
    log_file: Optional[Path] = None,
    level: str = "INFO",
    enable_console: bool = True,
    enable_file: bool = True
) -> logging.Logger:
    """
    Set up logging for PaperGen.

    Args:
        log_file: Path to log file (default: .papergen/papergen.log)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_console: Whether to log to console
        enable_file: Whether to log to file

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("papergen")
    logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if enable_file and log_file:
        try:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5
            )
            file_handler.setLevel(getattr(logging, level.upper()))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # If file logging fails, just continue without it
            print(f"Warning: Could not set up file logging: {e}", file=sys.stderr)

    return logger


def get_logger(name: str = "papergen") -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (default: papergen)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_operation(operation: str, **kwargs):
    """
    Log an operation with structured data.

    Args:
        operation: Operation name
        **kwargs: Additional context data
    """
    logger = get_logger()
    context = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.info(f"Operation: {operation} | {context}")


def log_error(error: Exception, operation: str, **kwargs):
    """
    Log an error with context.

    Args:
        error: Exception that occurred
        operation: Operation that failed
        **kwargs: Additional context data
    """
    logger = get_logger()
    context = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.error(f"Error in {operation}: {str(error)} | {context}", exc_info=True)


def log_api_call(endpoint: str, model: str, tokens: Optional[int] = None, **kwargs):
    """
    Log an API call.

    Args:
        endpoint: API endpoint
        model: Model name
        tokens: Token count (if available)
        **kwargs: Additional context
    """
    logger = get_logger()
    context = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    token_info = f", tokens={tokens}" if tokens else ""
    logger.info(f"API Call: {endpoint} | model={model}{token_info} | {context}")


def enable_debug_mode():
    """Enable debug mode logging."""
    logger = get_logger()
    logger.setLevel(logging.DEBUG)
    for handler in logger.handlers:
        handler.setLevel(logging.DEBUG)
    logger.debug("Debug mode enabled")


def disable_logging():
    """Disable all logging."""
    logger = get_logger()
    logger.handlers.clear()
