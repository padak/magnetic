"""Logging configuration for the application."""

import logging
import sys

def setup_logging():
    """Configure logging for the application."""
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    # Set specific loggers to DEBUG
    logging.getLogger('magnetic').setLevel(logging.DEBUG)
    logging.getLogger('sqlalchemy').setLevel(logging.INFO) 