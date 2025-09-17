from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo
from .constants import METERS_TO_FEET, METERS_TO_MILES, MPS_TO_MPH


def meters_to_feet(meters: float) -> float:
    """Convert meters to feet."""
    return meters * METERS_TO_FEET


def meters_to_miles(meters: float) -> float:
    """Convert meters to miles."""
    return meters * METERS_TO_MILES


def mps_to_mph(mps: float) -> float:
    """Convert meters per second to miles per hour."""
    return mps * MPS_TO_MPH


def convert_to_la_timezone(dt: Optional[datetime]) -> Optional[datetime]:
    """Convert datetime to America/Los_Angeles timezone."""
    if dt is None:
        return None

    la_tz = ZoneInfo("America/Los_Angeles")

    # If datetime is naive (no timezone), assume it's UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))

    # Convert to LA timezone
    return dt.astimezone(la_tz)
