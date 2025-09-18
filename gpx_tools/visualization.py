from datetime import datetime
from typing import List, Tuple, Optional

import asciichartpy as asciichart  # type: ignore[import-untyped]
from .formatting import format_time, format_heart_rate


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
        _ = "minutes" if max_elapsed > 300 else "seconds"  # 5+ minutes
    else:
        _ = time_unit

    # Create the chart
    chart_config = {
        "height": height,
        "format": "{:8.0f} ",  # Format as integer with no decimals
    }

    chart: str = asciichart.plot(hr_values, chart_config)  # type: ignore[arg-type]

    # Add title and summary statistics
    title = "Heart Rate over Time"
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
