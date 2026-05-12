"""Centralized timezone-aware datetime utilities.

All runtime modules should use `utcnow()` from this module instead of the
deprecated `datetime.datetime.now(timezone.utc)`.  The returned datetime objects are
timezone-aware (UTC), which avoids the Python 3.12+ deprecation warning and
ensures correct behavior in environments with non-UTC system clocks.
"""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)
