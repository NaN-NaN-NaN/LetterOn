"""
LetterOn Server - Structured Logging Configuration
Purpose: Configure JSON-formatted logging for CloudWatch compatibility
Testing: Logs to stdout, viewable in terminal
AWS Deployment: Automatically captured by CloudWatch Logs

This module sets up structured logging that:
- Outputs JSON format for easy parsing
- Includes contextual information (timestamps, levels, etc.)
- Works well with CloudWatch Logs Insights
"""

import logging
import sys
from pythonjsonlogger import jsonlogger

from app.settings import settings


def setup_logging():
    """
    Configure application-wide structured logging.

    Creates a JSON formatter that outputs to stdout for CloudWatch.
    Log level is controlled by the LOG_LEVEL environment variable.
    """

    # Create JSON formatter
    class CustomJsonFormatter(jsonlogger.JsonFormatter):
        """Custom JSON formatter with additional fields."""

        def add_fields(self, log_record, record, message_dict):
            super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)

            # Add standard fields
            log_record['timestamp'] = self.formatTime(record, self.datefmt)
            log_record['level'] = record.levelname
            log_record['logger'] = record.name
            log_record['environment'] = settings.environment

            # Add exception info if present
            if record.exc_info:
                log_record['exception'] = self.formatException(record.exc_info)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Remove existing handlers
    root_logger.handlers = []

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level.upper()))

    # Set formatter
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    # Add handler to root logger
    root_logger.addHandler(console_handler)

    # Suppress noisy loggers
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("s3transfer").setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)
