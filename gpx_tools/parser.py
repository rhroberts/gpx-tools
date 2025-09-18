from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Tuple

import gpxpy
import gpxpy.gpx

from .constants import (
    HEART_RATE_INDICATORS,
    MAX_HEART_RATE,
    MAX_PACE_MINUTES_PER_MILE,
    MAX_REASONABLE_SPEED_MPS,
    MAX_TIME_INTERVAL_SECONDS,
    MIN_HEART_RATE,
    MIN_PACE_MINUTES_PER_MILE,
    MIN_SPEED_THRESHOLD_MPS,
    MIN_TIME_INTERVAL_SECONDS,
    SECONDS_PER_MINUTE,
)


@dataclass
class GPXStats:
    total_distance: float
    total_time: Optional[float]
    max_speed: Optional[float]
    avg_speed: Optional[float]
    max_elevation: Optional[float]
    min_elevation: Optional[float]
    total_uphill: Optional[float]
    total_downhill: Optional[float]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    avg_heart_rate: Optional[float]
    max_heart_rate: Optional[float]
    activity_type: Optional[str]


class GPXParser:
    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        self.gpx: Optional[gpxpy.gpx.GPX] = None

    def parse(self):
        with open(self.file_path, "r") as gpx_file:
            self.gpx = gpxpy.parse(gpx_file)
        return self.gpx

    def get_stats(self) -> GPXStats:
        if not self.gpx:
            self.parse()

        stats = GPXStats(
            total_distance=0,
            total_time=None,
            max_speed=None,
            avg_speed=None,
            max_elevation=None,
            min_elevation=None,
            total_uphill=None,
            total_downhill=None,
            start_time=None,
            end_time=None,
            avg_heart_rate=None,
            max_heart_rate=None,
            activity_type=None,
        )

        if not self.gpx:
            return stats

        for track in self.gpx.tracks:
            for segment in track.segments:
                length_2d = segment.length_2d()
                if length_2d:
                    stats.total_distance += length_2d

                moving_data = segment.get_moving_data()
                if moving_data:
                    stats.total_time = moving_data.moving_time
                segment_max_speed = self.calculate_max_speed(segment)
                if segment_max_speed is not None:
                    if stats.max_speed is None or segment_max_speed > stats.max_speed:
                        stats.max_speed = segment_max_speed

                uphill_downhill = segment.get_uphill_downhill()
                if uphill_downhill:
                    stats.total_uphill = uphill_downhill.uphill
                    stats.total_downhill = uphill_downhill.downhill

                elevation_extremes = segment.get_elevation_extremes()
                if elevation_extremes:
                    stats.max_elevation = elevation_extremes.maximum
                    stats.min_elevation = elevation_extremes.minimum

                time_bounds = segment.get_time_bounds()
                if time_bounds:
                    stats.start_time = time_bounds.start_time
                    stats.end_time = time_bounds.end_time

        if stats.total_distance > 0 and stats.total_time:
            stats.avg_speed = stats.total_distance / stats.total_time

        stats.avg_heart_rate = self._calculate_average_heart_rate()
        stats.max_heart_rate = self._calculate_max_heart_rate()
        stats.activity_type = self.extract_activity_type()

        return stats

    def extract_activity_type(self) -> Optional[str]:
        """Extract activity type from GPX metadata."""
        if not self.gpx:
            return None

        for track in self.gpx.tracks:
            if hasattr(track, "type") and track.type:
                return track.type
        if hasattr(self.gpx, "extensions") and self.gpx.extensions:
            for ext in self.gpx.extensions:
                if hasattr(ext, "tag"):
                    tag_name = ext.tag.split("}")[-1] if "}" in ext.tag else ext.tag
                    if "sport" in tag_name.lower() or "activity" in tag_name.lower():
                        if hasattr(ext, "text") and ext.text:
                            return ext.text

        return None

    def calculate_max_speed(
        self, segment: gpxpy.gpx.GPXTrackSegment
    ) -> Optional[float]:
        """Calculate max speed from raw GPS data without filtering outliers."""
        max_speed = None

        for i in range(1, len(segment.points)):
            prev_point = segment.points[i - 1]
            curr_point = segment.points[i]

            if prev_point.time and curr_point.time:
                time_diff = (curr_point.time - prev_point.time).total_seconds()
                if MIN_TIME_INTERVAL_SECONDS <= time_diff <= MAX_TIME_INTERVAL_SECONDS:
                    distance = curr_point.distance_2d(prev_point) or 0
                    speed_mps = distance / time_diff

                    if 0 <= speed_mps <= MAX_REASONABLE_SPEED_MPS:
                        if max_speed is None or speed_mps > max_speed:
                            max_speed = speed_mps

        return max_speed

    def extract_heart_rate_data(self) -> List[float]:
        """Extract all heart rate values from the GPX data."""
        heart_rates: List[float] = []

        if not self.gpx:
            return heart_rates

        for track in self.gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    if point.extensions:
                        for ext in point.extensions:
                            hr_value = self._extract_heart_rate_from_extension(ext)
                            if hr_value is not None:
                                heart_rates.append(hr_value)

        return heart_rates

    def _calculate_average_heart_rate(self) -> Optional[float]:
        """Calculate average heart rate from GPX data."""
        heart_rates = self.extract_heart_rate_data()

        if not heart_rates:
            return None

        return sum(heart_rates) / len(heart_rates)

    def _calculate_max_heart_rate(self) -> Optional[float]:
        """Calculate maximum heart rate from GPX data."""
        heart_rates = self.extract_heart_rate_data()

        if not heart_rates:
            return None

        return max(heart_rates)

    def _extract_heart_rate_from_extension(self, extension: Any) -> Optional[float]:
        """Extract heart rate value from an extension."""
        try:
            # Check if it's an XML element with children (like Garmin TrackPointExtension)
            if hasattr(extension, "tag") and len(list(extension)) > 0:
                # Look through child elements for heart rate
                for child in extension:
                    if hasattr(child, "tag") and hasattr(child, "text"):
                        # Extract tag name without namespace
                        tag_name = (
                            child.tag.split("}")[-1] if "}" in child.tag else child.tag
                        )
                        tag_lower = tag_name.lower()

                        if any(
                            indicator in tag_lower
                            for indicator in HEART_RATE_INDICATORS
                        ):
                            if child.text and child.text.strip():
                                value = float(child.text.strip())
                                # Validate heart rate range
                                if MIN_HEART_RATE <= value <= MAX_HEART_RATE:
                                    return value

            # Check if it's a direct heart rate element
            if hasattr(extension, "tag") and hasattr(extension, "text"):
                # Extract tag name without namespace
                tag_name = (
                    extension.tag.split("}")[-1]
                    if "}" in extension.tag
                    else extension.tag
                )
                tag_lower = tag_name.lower()

                if any(indicator in tag_lower for indicator in HEART_RATE_INDICATORS):
                    if extension.text and extension.text.strip():
                        value = float(extension.text.strip())
                        # Validate heart rate range
                        if MIN_HEART_RATE <= value <= MAX_HEART_RATE:
                            return value

            # Check string representation for heart rate value
            ext_str = str(extension).lower()
            if any(indicator in ext_str for indicator in HEART_RATE_INDICATORS):
                # Try to extract numeric value from string
                import re

                numbers = re.findall(r"\d+\.?\d*", ext_str)
                if numbers:
                    # Take the first reasonable heart rate value (30-220 bpm)
                    for num_str in numbers:
                        value = float(num_str)
                        if MIN_HEART_RATE <= value <= MAX_HEART_RATE:
                            return value

        except (ValueError, AttributeError):
            pass

        return None

    def get_track_count(self) -> int:
        if not self.gpx:
            self.parse()
        return len(self.gpx.tracks) if self.gpx else 0

    def get_waypoint_count(self) -> int:
        if not self.gpx:
            self.parse()
        return len(self.gpx.waypoints) if self.gpx else 0

    def get_heart_rate_time_series(self) -> List[Tuple[datetime, float]]:
        """Extract heart rate data with timestamps as a time series."""
        time_series: List[Tuple[datetime, float]] = []

        if not self.gpx:
            self.parse()

        if not self.gpx:
            return time_series

        for track in self.gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    if point.time and point.extensions:
                        for ext in point.extensions:
                            hr_value = self._extract_heart_rate_from_extension(ext)
                            if hr_value is not None:
                                time_series.append((point.time, hr_value))
                                break  # Only take first HR value per point

        return time_series

    def get_pace_time_series(
        self, window_size: int = 5
    ) -> List[Tuple[datetime, float]]:
        """Extract pace data with timestamps as a time series (min/mile).

        Uses a moving window to smooth pace calculations and reduce noise,
        especially at activity start/end.

        Args:
            window_size: Number of points to use for pace calculation (default: 5)
        """
        time_series: List[Tuple[datetime, float]] = []

        if not self.gpx:
            self.parse()

        if not self.gpx:
            return time_series

        for track in self.gpx.tracks:
            for segment in track.segments:
                points_with_time = [p for p in segment.points if p.time]

                if len(points_with_time) < 2:
                    continue

                # Calculate pace using a moving window
                for i in range(len(points_with_time)):
                    # Define window boundaries
                    start_idx = max(0, i - window_size // 2)
                    end_idx = min(len(points_with_time), i + window_size // 2 + 1)

                    # Need at least 2 points for calculation
                    if end_idx - start_idx < 2:
                        continue

                    # Calculate total distance and time over the window
                    total_distance_meters = 0.0
                    total_time_seconds = 0.0

                    for j in range(start_idx + 1, end_idx):
                        prev_point = points_with_time[j - 1]
                        curr_point = points_with_time[j]

                        # Skip if times are None (should not happen after filtering)
                        if not prev_point.time or not curr_point.time:
                            continue

                        dist = curr_point.distance_2d(prev_point) or 0
                        time_diff = (curr_point.time - prev_point.time).total_seconds()

                        # Only include valid segments
                        if (
                            MIN_TIME_INTERVAL_SECONDS
                            <= time_diff
                            <= MAX_TIME_INTERVAL_SECONDS
                            and dist > 0
                        ):
                            total_distance_meters += dist
                            total_time_seconds += time_diff

                    # Calculate average pace over the window
                    if total_distance_meters > 0 and total_time_seconds > 0:
                        speed_mps = total_distance_meters / total_time_seconds

                        if (
                            MIN_SPEED_THRESHOLD_MPS
                            <= speed_mps
                            <= MAX_REASONABLE_SPEED_MPS
                        ):
                            from .conversion import meters_to_miles

                            distance_miles = meters_to_miles(total_distance_meters)
                            pace_seconds_per_mile = total_time_seconds / distance_miles
                            pace_minutes_per_mile = (
                                pace_seconds_per_mile / SECONDS_PER_MINUTE
                            )

                            if (
                                MIN_PACE_MINUTES_PER_MILE
                                <= pace_minutes_per_mile
                                <= MAX_PACE_MINUTES_PER_MILE
                            ):
                                # Current point time should exist (we filtered for it)
                                point_time = points_with_time[i].time
                                if point_time:
                                    time_series.append(
                                        (point_time, pace_minutes_per_mile)
                                    )

        return time_series

    def get_speed_time_series(
        self, window_size: int = 5
    ) -> List[Tuple[datetime, float]]:
        """Extract speed data with timestamps as a time series (mph).

        Uses a moving window to smooth speed calculations and reduce noise.

        Args:
            window_size: Number of points to use for speed calculation (default: 5)
        """
        time_series: List[Tuple[datetime, float]] = []

        if not self.gpx:
            self.parse()

        if not self.gpx:
            return time_series

        for track in self.gpx.tracks:
            for segment in track.segments:
                points_with_time = [p for p in segment.points if p.time]

                if len(points_with_time) < 2:
                    continue

                # Calculate speed using a moving window
                for i in range(len(points_with_time)):
                    # Define window boundaries
                    start_idx = max(0, i - window_size // 2)
                    end_idx = min(len(points_with_time), i + window_size // 2 + 1)

                    # Need at least 2 points for calculation
                    if end_idx - start_idx < 2:
                        continue

                    # Calculate total distance and time over the window
                    total_distance_meters = 0.0
                    total_time_seconds = 0.0

                    for j in range(start_idx + 1, end_idx):
                        prev_point = points_with_time[j - 1]
                        curr_point = points_with_time[j]

                        # Skip if times are None (should not happen after filtering)
                        if not prev_point.time or not curr_point.time:
                            continue

                        dist = curr_point.distance_2d(prev_point) or 0
                        time_diff = (curr_point.time - prev_point.time).total_seconds()

                        # Only include valid segments
                        if (
                            MIN_TIME_INTERVAL_SECONDS
                            <= time_diff
                            <= MAX_TIME_INTERVAL_SECONDS
                            and dist > 0
                        ):
                            total_distance_meters += dist
                            total_time_seconds += time_diff

                    # Calculate average speed over the window
                    if total_distance_meters > 0 and total_time_seconds > 0:
                        speed_mps = total_distance_meters / total_time_seconds

                        if (
                            MIN_SPEED_THRESHOLD_MPS
                            <= speed_mps
                            <= MAX_REASONABLE_SPEED_MPS
                        ):
                            from .conversion import mps_to_mph

                            speed_mph = mps_to_mph(speed_mps)

                            # Current point time should exist (we filtered for it)
                            point_time = points_with_time[i].time
                            if point_time:
                                time_series.append((point_time, speed_mph))

        return time_series
