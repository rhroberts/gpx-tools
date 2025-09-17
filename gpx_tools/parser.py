import gpxpy
import gpxpy.gpx
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from datetime import datetime


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
                    stats.max_speed = moving_data.max_speed

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

        return stats

    def get_track_count(self) -> int:
        if not self.gpx:
            self.parse()
        return len(self.gpx.tracks) if self.gpx else 0

    def get_waypoint_count(self) -> int:
        if not self.gpx:
            self.parse()
        return len(self.gpx.waypoints) if self.gpx else 0
