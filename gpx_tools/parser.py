import gpxpy
import gpxpy.gpx
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from datetime import datetime
from .heart_rate import calculate_average_heart_rate, calculate_max_heart_rate


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
                    # Don't use gpxpy's max_speed as it filters out legitimate high speeds
                    # stats.max_speed = moving_data.max_speed

                # Calculate our own max speed from raw GPS data
                segment_max_speed = self._calculate_max_speed(segment)
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

        # Calculate heart rate statistics
        stats.avg_heart_rate = calculate_average_heart_rate(self.gpx)
        stats.max_heart_rate = calculate_max_heart_rate(self.gpx)

        # Extract activity type
        stats.activity_type = self._extract_activity_type()

        return stats

    def _extract_activity_type(self) -> Optional[str]:
        """Extract activity type from GPX metadata."""
        if not self.gpx:
            return None

        # Check track types first
        for track in self.gpx.tracks:
            if hasattr(track, "type") and track.type:
                return track.type

        # Check for activity type in extensions or metadata
        # This could be extended to look in specific namespaces for different devices
        if hasattr(self.gpx, "extensions") and self.gpx.extensions:
            for ext in self.gpx.extensions:
                if hasattr(ext, "tag"):
                    tag_name = ext.tag.split("}")[-1] if "}" in ext.tag else ext.tag
                    if "sport" in tag_name.lower() or "activity" in tag_name.lower():
                        if hasattr(ext, "text") and ext.text:
                            return ext.text

        return None

    def _calculate_max_speed(
        self, segment: gpxpy.gpx.GPXTrackSegment
    ) -> Optional[float]:
        """Calculate max speed from raw GPS data without filtering outliers."""
        max_speed = None

        for i in range(1, len(segment.points)):
            prev_point = segment.points[i - 1]
            curr_point = segment.points[i]

            if prev_point.time and curr_point.time:
                time_diff = (curr_point.time - prev_point.time).total_seconds()
                # Only consider reasonable time intervals (1-60 seconds)
                if 1 <= time_diff <= 60:
                    distance = curr_point.distance_2d(prev_point) or 0
                    speed_mps = distance / time_diff

                    # Only consider reasonable speeds (up to ~200 mph / 90 m/s)
                    # This filters out obvious GPS errors while keeping legitimate high speeds
                    if 0 <= speed_mps <= 90:
                        if max_speed is None or speed_mps > max_speed:
                            max_speed = speed_mps

        return max_speed

    def get_track_count(self) -> int:
        if not self.gpx:
            self.parse()
        return len(self.gpx.tracks) if self.gpx else 0

    def get_waypoint_count(self) -> int:
        if not self.gpx:
            self.parse()
        return len(self.gpx.waypoints) if self.gpx else 0
