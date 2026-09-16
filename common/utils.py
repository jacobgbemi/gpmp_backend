"""Shared utility helpers used across apps."""

from django.utils import timezone


def utc_now():
    """Return the current timezone-aware UTC datetime.

    Prefer this over `datetime.utcnow()` so all timestamps generated in
    application code respect Django's `USE_TZ` configuration consistently.
    """
    return timezone.now()