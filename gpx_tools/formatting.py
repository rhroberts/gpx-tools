from datetime import datetime
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


def convert_to_la_timezone(dt: datetime) -> datetime:
    """Convert datetime to America/Los_Angeles timezone."""
    if dt is None:
        return None

    la_tz = ZoneInfo("America/Los_Angeles")

    # If datetime is naive (no timezone), assume it's UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))

    return dt.astimezone(la_tz)


def format_distance(distance_meters: float) -> str:
    """Format distance in imperial units (miles/feet)."""
    miles = meters_to_miles(distance_meters)
    if miles >= 1:
        return f"{miles:.2f} mi"
    feet = meters_to_feet(distance_meters)
    return f"{feet:.0f} ft"


def format_time(seconds: float) -> str:
    """Format time duration as HH:MM:SS or MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_speed(speed_mps: float) -> str:
    """Format speed in miles per hour."""
    mph = mps_to_mph(speed_mps)
    return f"{mph:.1f} mph"


def format_elevation(elevation_meters: float) -> str:
    """Format elevation in feet."""
    feet = meters_to_feet(elevation_meters)
    return f"{feet:.0f} ft"


def format_datetime(dt: datetime) -> str:
    """Format datetime in LA timezone with 12-hour format and timezone abbreviation."""
    if dt is None:
        return None

    la_dt = convert_to_la_timezone(dt)
    return la_dt.strftime("%Y-%m-%d %I:%M:%S %p %Z")


def format_heart_rate(heart_rate: float) -> str:
    """Format heart rate in beats per minute."""
    return f"{heart_rate:.0f} bpm"


def format_activity_type(activity_type: str) -> str:
    """Format activity type with proper capitalization."""
    if not activity_type:
        return "Unknown"
    return activity_type.replace("_", " ").title()
