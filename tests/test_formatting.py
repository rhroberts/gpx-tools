import pytest
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from gpx_tools.formatting import (
    format_distance,
    format_time,
    format_speed,
    format_elevation,
    format_datetime,
    format_heart_rate,
    format_activity_type,
    format_gpx_stats,
    print_gpx_stats,
)
from gpx_tools.parser import GPXParser, GPXStats


class TestFormatting:
    def test_format_distance_miles(self):
        result = format_distance(2000.0)  # > 1 mile
        assert "mi" in result and result.endswith(" mi")

    def test_format_distance_feet(self):
        result = format_distance(100.0)  # < 1 mile
        assert result == "328 ft"

    def test_format_time_with_hours(self):
        result = format_time(3661)  # 1:01:01
        assert result == "1:01:01"

    def test_format_time_without_hours(self):
        result = format_time(125)  # 2:05
        assert result == "2:05"

    def test_format_speed(self):
        result = format_speed(44.704)  # ~100 mph
        assert result == "100.0 mph"

    def test_format_elevation(self):
        result = format_elevation(100.0)
        assert result == "328 ft"

    def test_format_datetime(self):
        dt = datetime(2024, 1, 15, 18, 0, 0, tzinfo=ZoneInfo("UTC"))
        result = format_datetime(dt)
        assert result is not None
        assert "2024-01-15 10:00:00 AM PST" in result

    def test_format_datetime_none(self):
        assert format_datetime(None) is None

    def test_format_heart_rate(self):
        assert format_heart_rate(150.7) == "151 bpm"

    def test_format_activity_type(self):
        assert format_activity_type("cycling") == "Cycling"
        assert format_activity_type("trail_running") == "Trail Running"
        assert format_activity_type("") == "Unknown"
        assert format_activity_type(None) == "Unknown"


class TestStatsFormatter:
    @pytest.fixture
    def simple_ride_path(self) -> Path:
        return Path(__file__).parent / "test_data" / "simple_ride.gpx"

    @pytest.fixture
    def sample_stats(self) -> GPXStats:
        return GPXStats(
            total_distance=1000.0,
            total_time=600.0,
            max_speed=10.0,
            avg_speed=5.0,
            max_elevation=100.0,
            min_elevation=50.0,
            total_uphill=25.0,
            total_downhill=15.0,
            start_time=datetime(2024, 1, 15, 10, 0, 0),
            end_time=datetime(2024, 1, 15, 10, 10, 0),
            avg_heart_rate=150.0,
            max_heart_rate=170.0,
            activity_type="cycling",
        )

    def test_format_gpx_stats_with_complete_data(
        self, simple_ride_path: Path, sample_stats: GPXStats
    ) -> None:
        parser = GPXParser(simple_ride_path)
        parser.parse()

        lines = format_gpx_stats(simple_ride_path, parser, sample_stats)

        # Check basic file info
        assert f"GPX File: {simple_ride_path}" in lines
        assert "Tracks: 1" in lines
        assert "Waypoints: 0" in lines
        assert "Activity: Cycling" in lines

        # Check that we have distance and time
        distance_line = next((line for line in lines if "Distance:" in line), None)
        assert distance_line is not None

        time_line = next((line for line in lines if "Time:" in line), None)
        assert time_line is not None

        # Check heart rate data
        avg_hr_line = next(
            (line for line in lines if "Average Heart Rate:" in line), None
        )
        assert avg_hr_line is not None
        assert "150 bpm" in avg_hr_line

    def test_format_gpx_stats_minimal_data(self, simple_ride_path: Path) -> None:
        # Stats with minimal data
        minimal_stats = GPXStats(
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

        parser = GPXParser(simple_ride_path)
        parser.parse()

        lines = format_gpx_stats(simple_ride_path, parser, minimal_stats)

        # Should still have basic file info
        assert f"GPX File: {simple_ride_path}" in lines
        assert "Tracks: 1" in lines

        # Should not have optional data
        assert not any("Distance:" in line for line in lines)
        assert not any("Average Heart Rate:" in line for line in lines)

    def test_print_gpx_stats(
        self,
        simple_ride_path: Path,
        sample_stats: GPXStats,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        parser = GPXParser(simple_ride_path)
        parser.parse()

        print_gpx_stats(simple_ride_path, parser, sample_stats)

        captured = capsys.readouterr()
        assert f"GPX File: {simple_ride_path}" in captured.out
        assert "Activity: Cycling" in captured.out
