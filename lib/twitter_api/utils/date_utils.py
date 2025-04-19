"""
Date utilities for TwitterAPI.io client.

ابزارهای تاریخ برای کلاینت TwitterAPI.io - تبدیل فرمت‌های مختلف زمان در توییتر
"""

import datetime
import re
import time
from typing import Optional, Union

from lib.twitter_api.exceptions import TwitterAPIValidationError


def parse_twitter_date(date_string: str) -> datetime.datetime:
    """
    Parse Twitter date string into a datetime object.

    Handles multiple date formats used by Twitter API:
    - "Tue Dec 10 07:00:30 +0000 2024" (standard Twitter format)
    - "2024-12-10T07:00:30Z" (ISO 8601 format)
    - "2024-12-10T07:00:30+00:00" (ISO 8601 with timezone)
    - "Tue Dec 10 07:00:30 2024" (without timezone)

    Args:
        date_string: Date string in Twitter format

    Returns:
        Datetime object

    Raises:
        TwitterAPIValidationError: If date string is invalid
    """
    if not date_string:
        raise TwitterAPIValidationError("Empty date string")

    # Try different formats
    formats = [
        "%a %b %d %H:%M:%S %z %Y",  # "Tue Dec 10 07:00:30 +0000 2024"
        "%Y-%m-%dT%H:%M:%SZ",  # "2024-12-10T07:00:30Z"
        "%a %b %d %H:%M:%S %Y",  # "Tue Dec 10 07:00:30 2024" (without timezone)
    ]

    for fmt in formats:
        try:
            dt = datetime.datetime.strptime(date_string, fmt)
            # Add UTC timezone if missing
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            return dt
        except ValueError:
            continue

    # Try ISO format (handles timezone offsets like +00:00)
    try:
        dt = datetime.datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return dt
    except ValueError:
        pass

    # Try to parse without day name if that's causing the issue
    # E.g., "Dec 10 07:00:30 +0000 2024" instead of "Tue Dec 10 07:00:30 +0000 2024"
    try:
        # Extract components and reconstruct date
        parts = date_string.split()
        if len(parts) >= 6:
            # Remove day name if present
            new_date = ' '.join(parts[1:])
            dt = datetime.datetime.strptime(new_date, "%b %d %H:%M:%S %z %Y")
            return dt
    except ValueError:
        pass

    raise TwitterAPIValidationError(f"Unrecognized date format: {date_string}")


def format_twitter_date(dt: datetime.datetime) -> str:
    """
    Format datetime object into Twitter date string.

    Args:
        dt: Datetime object

    Returns:
        Date string in Twitter format
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)

    return dt.strftime("%a %b %d %H:%M:%S %z %Y")


def datetime_to_unix_timestamp(dt: datetime.datetime) -> int:
    """
    Convert datetime object to Unix timestamp (seconds since epoch).

    Args:
        dt: Datetime object

    Returns:
        Unix timestamp in seconds
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)

    return int(dt.timestamp())


def unix_timestamp_to_datetime(timestamp: Union[int, float]) -> datetime.datetime:
    """
    Convert Unix timestamp to datetime object.

    Args:
        timestamp: Unix timestamp in seconds

    Returns:
        Datetime object with UTC timezone
    """
    return datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)


def get_twitter_date_now() -> str:
    """
    Get current time in Twitter date string format.

    Returns:
        Current time as Twitter date string
    """
    return format_twitter_date(datetime.datetime.now(datetime.timezone.utc))


def validate_time_range(since_time: Optional[Union[int, str, datetime.datetime]] = None,
                       until_time: Optional[Union[int, str, datetime.datetime]] = None) -> tuple:
    """
    Validate time range parameters and convert to Unix timestamps if needed.

    Args:
        since_time: Start time (Unix timestamp, datetime object, or Twitter date string)
        until_time: End time (Unix timestamp, datetime object, or Twitter date string)

    Returns:
        Tuple of (since_time, until_time) as Unix timestamps or None

    Raises:
        TwitterAPIValidationError: If time range is invalid
    """
    since_timestamp = None
    until_timestamp = None

    # Process since_time
    if since_time is not None:
        if isinstance(since_time, (int, float)):
            since_timestamp = int(since_time)
        elif isinstance(since_time, str):
            try:
                since_timestamp = datetime_to_unix_timestamp(parse_twitter_date(since_time))
            except TwitterAPIValidationError:
                # Try parsing as Unix timestamp
                try:
                    since_timestamp = int(since_time)
                except ValueError:
                    raise TwitterAPIValidationError(f"Invalid since_time format: {since_time}")
        elif isinstance(since_time, datetime.datetime):
            since_timestamp = datetime_to_unix_timestamp(since_time)
        else:
            raise TwitterAPIValidationError(f"Invalid since_time type: {type(since_time).__name__}")

    # Process until_time
    if until_time is not None:
        if isinstance(until_time, (int, float)):
            until_timestamp = int(until_time)
        elif isinstance(until_time, str):
            try:
                until_timestamp = datetime_to_unix_timestamp(parse_twitter_date(until_time))
            except TwitterAPIValidationError:
                # Try parsing as Unix timestamp
                try:
                    until_timestamp = int(until_time)
                except ValueError:
                    raise TwitterAPIValidationError(f"Invalid until_time format: {until_time}")
        elif isinstance(until_time, datetime.datetime):
            until_timestamp = datetime_to_unix_timestamp(until_time)
        else:
            raise TwitterAPIValidationError(f"Invalid until_time type: {type(until_time).__name__}")

    # Validate that since_time is before until_time if both are provided
    if since_timestamp is not None and until_timestamp is not None and since_timestamp >= until_timestamp:
        raise TwitterAPIValidationError("since_time must be earlier than until_time")

    return since_timestamp, until_timestamp


def format_datetime_for_twitter_query(dt: datetime.datetime) -> str:
    """
    Format datetime for Twitter search query.

    Twitter's advanced search expects dates in the format: "YYYY-MM-DD_HH:MM:SS_UTC"

    Args:
        dt: Datetime object

    Returns:
        Formatted date string for Twitter query
    """
    # Ensure the datetime is in UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    else:
        dt = dt.astimezone(datetime.timezone.utc)

    return dt.strftime("%Y-%m-%d_%H:%M:%S_UTC")