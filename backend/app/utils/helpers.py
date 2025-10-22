"""
LetterOn Server - Helper Utility Functions
Purpose: Common utility functions used across the application
Testing: Import and use in any module
AWS Deployment: No special configuration needed

This module provides:
- UUID generation
- Date/time utilities
- String manipulation
- Validation helpers
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
import re


def generate_uuid() -> str:
    """
    Generate a unique UUID string.

    Returns:
        str: UUID4 string without hyphens
    """
    return str(uuid.uuid4())


def generate_short_id(prefix: str = "") -> str:
    """
    Generate a short unique ID with optional prefix.

    Args:
        prefix: Optional prefix for the ID

    Returns:
        str: Short unique ID (e.g., "letter_abc123")
    """
    short_uuid = str(uuid.uuid4())[:8]
    return f"{prefix}{short_uuid}" if prefix else short_uuid


def get_current_timestamp() -> int:
    """
    Get current Unix timestamp in seconds.

    Returns:
        int: Current timestamp
    """
    return int(datetime.now(timezone.utc).timestamp())


def get_current_iso_timestamp() -> str:
    """
    Get current timestamp in ISO 8601 format.

    Returns:
        str: ISO formatted timestamp
    """
    return datetime.now(timezone.utc).isoformat()


def parse_iso_timestamp(iso_string: str) -> Optional[datetime]:
    """
    Parse ISO 8601 timestamp string to datetime object.

    Args:
        iso_string: ISO formatted timestamp string

    Returns:
        datetime: Parsed datetime object or None if invalid
    """
    try:
        return datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None


def is_valid_email(email: str) -> bool:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        bool: True if valid email format
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing special characters.

    Args:
        filename: Original filename

    Returns:
        str: Sanitized filename safe for S3
    """
    # Remove special characters, keep alphanumeric, dots, hyphens, underscores
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    # Remove multiple consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    return sanitized


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to maximum length with suffix.

    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to append if truncated

    Returns:
        str: Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def get_file_extension(filename: str) -> str:
    """
    Extract file extension from filename.

    Args:
        filename: Filename with extension

    Returns:
        str: File extension without dot (e.g., 'jpg', 'png')
    """
    return filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in bytes to human-readable format.

    Args:
        size_bytes: File size in bytes

    Returns:
        str: Formatted file size (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def safe_get(dictionary: dict, *keys, default=None):
    """
    Safely get nested dictionary value.

    Args:
        dictionary: Dictionary to search
        *keys: Keys to traverse
        default: Default value if key not found

    Returns:
        Value at nested key or default
    """
    result = dictionary
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key)
        else:
            return default
        if result is None:
            return default
    return result
