from datetime import datetime
from typing import List, Optional, Tuple

import asciichartpy as asciichart  # type: ignore[import-untyped]

from .constants import (
    MIN_ELEVATION_FEET,
    MAX_ELEVATION_FEET,
    TIME_UNIT_THRESHOLD_SECONDS,
)
from .formatting import format_heart_rate, format_time


def downsample_time_series(
    time_series: List[Tuple[datetime, float]], target_points: int
) -> List[Tuple[datetime, float]]:
    """Downsample time series data to a target number of points."""
    if len(time_series) <= target_points:
        return time_series

    # Simple even downsampling
    step = len(time_series) / target_points
    sampled_indices: List[int] = []

    for i in range(target_points):
        index = int(i * step)
        if index < len(time_series):
            sampled_indices.append(index)

    # Ensure we include the last point
    if sampled_indices[-1] != len(time_series) - 1:
        sampled_indices[-1] = len(time_series) - 1

    return [time_series[i] for i in sampled_indices]


def create_heart_rate_chart(
    time_series: List[Tuple[datetime, float]],
    width: int = 80,
    height: int = 20,
    time_unit: str = "auto",
) -> str:
    """Create an ASCII chart of heart rate over time."""
    if not time_series:
        return "No heart rate data available in the GPX file."

    # Downsample data if we have too many points for the chart width
    sampled_series = downsample_time_series(time_series, width)

    # Extract heart rate values and calculate time offsets
    start_time = sampled_series[0][0]
    hr_values: List[float] = []
    time_labels: List[float] = []

    for timestamp, hr in sampled_series:
        hr_values.append(hr)
        elapsed_seconds = (timestamp - start_time).total_seconds()
        time_labels.append(elapsed_seconds)

    # Determine time unit for display
    max_elapsed = max(time_labels) if time_labels else 0
    if time_unit == "auto":
        _ = "minutes" if max_elapsed > TIME_UNIT_THRESHOLD_SECONDS else "seconds"
    else:
        _ = time_unit

    # Create the chart
    chart_config = {
        "height": height,
        "format": "{:8.0f} ",  # Format as integer with no decimals
    }

    chart: str = asciichart.plot(hr_values, chart_config)  # type: ignore[arg-type]

    # Add title and summary statistics
    title = "Heart Rate (BPM) over Time"
    avg_hr = sum(hr_values) / len(hr_values)
    max_hr = max(hr_values)
    min_hr = min(hr_values)
    duration_str = format_time(max_elapsed)

    summary = (
        f"Duration: {duration_str}, "
        f"Avg HR: {format_heart_rate(avg_hr)}, "
        f"Max HR: {format_heart_rate(max_hr)}, "
        f"Min HR: {format_heart_rate(min_hr)}"
    )

    return f"{title}\n\n{chart}\n\n{summary}"


# Removed unused time axis functions since we simplified the chart


def validate_heart_rate_data(
    time_series: List[Tuple[datetime, float]],
) -> Optional[str]:
    """Validate heart rate data and return error message if invalid."""
    if not time_series:
        return "No heart rate data found in GPX file"

    if len(time_series) < 2:
        return "Insufficient heart rate data points for visualization"

    # Check for reasonable heart rate values
    hr_values = [hr for _, hr in time_series]
    max_hr = max(hr_values)
    min_hr = min(hr_values)

    if max_hr > 220 or min_hr < 30:
        return "Heart rate data appears to be invalid (outside normal range)"

    return None


def create_pace_chart(
    time_series: List[Tuple[datetime, float]],
    width: int = 80,
    height: int = 20,
    time_unit: str = "auto",
) -> str:
    """Create an ASCII chart of pace over time (min/mile)."""
    if not time_series:
        return "No pace data available in the GPX file."

    # Downsample data if we have too many points for the chart width
    sampled_series = downsample_time_series(time_series, width)

    # Extract pace values and calculate time offsets
    start_time = sampled_series[0][0]
    pace_values: List[float] = []
    time_labels: List[float] = []

    for timestamp, pace in sampled_series:
        pace_values.append(pace)
        elapsed_seconds = (timestamp - start_time).total_seconds()
        time_labels.append(elapsed_seconds)

    # Find the range of pace values
    min_pace = min(pace_values)  # Fastest pace (lower number)
    max_pace = max(pace_values)  # Slowest pace (higher number)

    # To invert the y-axis (lower values higher), we need to negate the values
    inverted_values = [-pace for pace in pace_values]

    # Determine time unit for display
    max_elapsed = max(time_labels) if time_labels else 0
    if time_unit == "auto":
        _ = "minutes" if max_elapsed > TIME_UNIT_THRESHOLD_SECONDS else "seconds"
    else:
        _ = time_unit

    # Create the chart with inverted values
    # Use a custom format that will show the absolute value
    chart_config = {
        "height": height,
        "format": "{:8.1f} ",
    }

    chart: str = asciichart.plot(inverted_values, chart_config)  # type: ignore[arg-type]

    # Simple approach: just remove the minus signs from the y-axis labels
    chart_lines = chart.split("\n")
    fixed_lines: List[str] = []

    for line in chart_lines:
        # Replace any minus sign that appears before a digit at the start of the line
        # This preserves alignment by replacing '-' with ' '
        if line and len(line) > 0:
            # Check if this line starts with spaces followed by a negative number
            import re

            # Match leading spaces, optional minus, and a number
            pattern = r"^(\s*)-(\d+\.?\d*\s+[┤┼])"
            replacement = r"\1 \2"
            new_line = re.sub(pattern, replacement, line)
            fixed_lines.append(new_line)
        else:
            fixed_lines.append(line)

    chart = "\n".join(fixed_lines)

    # Add title and summary statistics
    title = "Pace (min/mile) over Time"
    avg_pace = sum(pace_values) / len(pace_values)
    duration_str = format_time(max_elapsed)

    from .formatting import format_pace

    summary = (
        f"Duration: {duration_str}, "
        f"Avg Pace: {format_pace(avg_pace)}, "
        f"Fastest: {format_pace(min_pace)}, "
        f"Slowest: {format_pace(max_pace)}"
    )

    return f"{title}\n\n{chart}\n\n{summary}"


def validate_pace_data(
    time_series: List[Tuple[datetime, float]],
) -> Optional[str]:
    """Validate pace data and return error message if invalid."""
    if not time_series:
        return "No pace data found in GPX file"

    if len(time_series) < 2:
        return "Insufficient pace data points for visualization"

    # Check for reasonable pace values (2-60 min/mile)
    pace_values = [pace for _, pace in time_series]
    max_pace = max(pace_values)
    min_pace = min(pace_values)

    if max_pace > 60 or min_pace < 2:
        return "Pace data appears to be invalid (outside normal range)"

    return None


def create_speed_chart(
    time_series: List[Tuple[datetime, float]],
    width: int = 80,
    height: int = 20,
    time_unit: str = "auto",
) -> str:
    """Create an ASCII chart of speed over time (mph)."""
    if not time_series:
        return "No speed data available in the GPX file."

    # Downsample data if we have too many points for the chart width
    sampled_series = downsample_time_series(time_series, width)

    # Extract speed values and calculate time offsets
    start_time = sampled_series[0][0]
    speed_values: List[float] = []
    time_labels: List[float] = []

    for timestamp, speed in sampled_series:
        speed_values.append(speed)
        elapsed_seconds = (timestamp - start_time).total_seconds()
        time_labels.append(elapsed_seconds)

    # Determine time unit for display
    max_elapsed = max(time_labels) if time_labels else 0
    if time_unit == "auto":
        _ = "minutes" if max_elapsed > TIME_UNIT_THRESHOLD_SECONDS else "seconds"
    else:
        _ = time_unit

    # Create the chart
    chart_config = {
        "height": height,
        "format": "{:8.1f} ",  # Format with one decimal
    }

    chart: str = asciichart.plot(speed_values, chart_config)  # type: ignore[arg-type]

    # Add title and summary statistics
    title = "Speed (mph) over Time"
    avg_speed = sum(speed_values) / len(speed_values)
    max_speed = max(speed_values)
    min_speed = min(speed_values)
    duration_str = format_time(max_elapsed)

    summary = (
        f"Duration: {duration_str}, "
        f"Avg Speed: {avg_speed:.1f} mph, "
        f"Max: {max_speed:.1f} mph, "
        f"Min: {min_speed:.1f} mph"
    )

    return f"{title}\n\n{chart}\n\n{summary}"


def validate_speed_data(
    time_series: List[Tuple[datetime, float]],
) -> Optional[str]:
    """Validate speed data and return error message if invalid."""
    if not time_series:
        return "No speed data found in GPX file"

    if len(time_series) < 2:
        return "Insufficient speed data points for visualization"

    return None


def create_elevation_chart(
    time_series: List[Tuple[datetime, float]],
    width: int = 80,
    height: int = 20,
    time_unit: str = "auto",
) -> str:
    """Create an ASCII chart of elevation over time (feet)."""
    if not time_series:
        return "No elevation data available in the GPX file."

    # Downsample data if we have too many points for the chart width
    sampled_series = downsample_time_series(time_series, width)

    # Extract elevation values and calculate time offsets
    start_time = sampled_series[0][0]
    elevation_values: List[float] = []
    time_labels: List[float] = []

    for timestamp, elevation in sampled_series:
        elevation_values.append(elevation)
        elapsed_seconds = (timestamp - start_time).total_seconds()
        time_labels.append(elapsed_seconds)

    # Determine time unit for display
    max_elapsed = max(time_labels) if time_labels else 0
    if time_unit == "auto":
        _ = "minutes" if max_elapsed > TIME_UNIT_THRESHOLD_SECONDS else "seconds"
    else:
        _ = time_unit

    # Create the chart
    chart_config = {
        "height": height,
        "format": "{:8.0f} ",  # Format as integer (whole feet)
    }

    chart: str = asciichart.plot(elevation_values, chart_config)  # type: ignore[arg-type]

    # Add title and summary statistics
    title = "Elevation (feet) over Time"
    max_elevation = max(elevation_values)
    min_elevation = min(elevation_values)
    elevation_gain = calculate_total_elevation_gain(sampled_series)
    elevation_loss = calculate_total_elevation_loss(sampled_series)
    duration_str = format_time(max_elapsed)

    summary = (
        f"Duration: {duration_str}, "
        f"Max: {max_elevation:.0f} ft, "
        f"Min: {min_elevation:.0f} ft, "
        f"Gain: {elevation_gain:.0f} ft, "
        f"Loss: {elevation_loss:.0f} ft"
    )

    return f"{title}\n\n{chart}\n\n{summary}"


def calculate_total_elevation_gain(time_series: List[Tuple[datetime, float]]) -> float:
    """Calculate total elevation gain from time series data."""
    if len(time_series) < 2:
        return 0.0

    total_gain = 0.0
    for i in range(1, len(time_series)):
        elevation_diff = time_series[i][1] - time_series[i - 1][1]
        if elevation_diff > 0:
            total_gain += elevation_diff

    return total_gain


def calculate_total_elevation_loss(time_series: List[Tuple[datetime, float]]) -> float:
    """Calculate total elevation loss from time series data."""
    if len(time_series) < 2:
        return 0.0

    total_loss = 0.0
    for i in range(1, len(time_series)):
        elevation_diff = time_series[i][1] - time_series[i - 1][1]
        if elevation_diff < 0:
            total_loss += abs(elevation_diff)

    return total_loss


def validate_elevation_data(
    time_series: List[Tuple[datetime, float]],
) -> Optional[str]:
    """Validate elevation data and return error message if invalid."""
    if not time_series:
        return "No elevation data found in GPX file"

    if len(time_series) < 2:
        return "Insufficient elevation data points for visualization"

    # Check for reasonable elevation values (Death Valley to Everest in feet)
    elevation_values = [elev for _, elev in time_series]
    max_elev = max(elevation_values)
    min_elev = min(elevation_values)

    if min_elev < MIN_ELEVATION_FEET or max_elev > MAX_ELEVATION_FEET:
        return "Elevation data appears to be invalid (outside reasonable range)"

    return None
