from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from pathlib import Path
from .conversion import (
    meters_to_feet,
    meters_to_miles,
    mps_to_mph,
    convert_to_la_timezone,
)

if TYPE_CHECKING:
    from .parser import GPXParser, GPXStats


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


def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Format datetime in LA timezone with 12-hour format and timezone abbreviation."""
    if dt is None:
        return None

    la_dt = convert_to_la_timezone(dt)
    if la_dt is None:
        return None
    return la_dt.strftime("%Y-%m-%d %I:%M:%S %p %Z")


def format_heart_rate(heart_rate: float) -> str:
    """Format heart rate in beats per minute."""
    return f"{heart_rate:.0f} bpm"


def format_pace(pace_minutes_per_mile: float) -> str:
    """Format pace in minutes:seconds per mile."""
    minutes = int(pace_minutes_per_mile)
    seconds = int((pace_minutes_per_mile - minutes) * 60)
    return f"{minutes}:{seconds:02d} min/mi"


def format_activity_type(activity_type: Optional[str]) -> str:
    """Format activity type with proper capitalization."""
    if not activity_type:
        return "Unknown"
    return activity_type.replace("_", " ").title()


def format_gpx_stats(
    file_path: Path, parser: "GPXParser", stats: "GPXStats"
) -> List[str]:
    """Format GPX statistics into a list of display strings."""
    lines: List[str] = []

    # File information
    lines.append(f"GPX File: {file_path}")
    lines.append(f"Tracks: {parser.get_track_count()}")
    lines.append(f"Waypoints: {parser.get_waypoint_count()}")

    # Activity type
    if stats.activity_type:
        lines.append(f"Activity: {format_activity_type(stats.activity_type)}")

    lines.append("")  # Empty line separator

    # Distance
    if stats.total_distance > 0:
        lines.append(f"Distance: {format_distance(stats.total_distance)}")

    # Time
    if stats.total_time:
        lines.append(f"Time: {format_time(stats.total_time)}")

    # Speed
    if stats.avg_speed:
        lines.append(f"Average Speed: {format_speed(stats.avg_speed)}")

    if stats.max_speed:
        lines.append(f"Max Speed: {format_speed(stats.max_speed)}")

    # Heart rate
    if stats.avg_heart_rate:
        lines.append(f"Average Heart Rate: {format_heart_rate(stats.avg_heart_rate)}")

    if stats.max_heart_rate:
        lines.append(f"Max Heart Rate: {format_heart_rate(stats.max_heart_rate)}")

    # Elevation
    if stats.max_elevation is not None and stats.min_elevation is not None:
        lines.append(
            f"Elevation: {format_elevation(stats.min_elevation)} - {format_elevation(stats.max_elevation)}"
        )

    if stats.total_uphill:
        lines.append(f"Uphill: {format_elevation(stats.total_uphill)}")

    if stats.total_downhill:
        lines.append(f"Downhill: {format_elevation(stats.total_downhill)}")

    # Times
    if stats.start_time:
        lines.append(f"Start: {format_datetime(stats.start_time)}")

    if stats.end_time:
        lines.append(f"End: {format_datetime(stats.end_time)}")

    return lines


def print_gpx_stats(file_path: Path, parser: "GPXParser", stats: "GPXStats") -> None:
    """Print formatted GPX statistics to stdout."""
    import click

    lines = format_gpx_stats(file_path, parser, stats)
    for line in lines:
        click.echo(line)
