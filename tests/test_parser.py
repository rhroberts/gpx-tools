import pytest
from pathlib import Path
from gpx_tools.parser import GPXParser, GPXStats


class TestGPXParser:
    @pytest.fixture
    def simple_ride_path(self) -> Path:
        return Path(__file__).parent / "test_data" / "simple_ride.gpx"

    @pytest.fixture
    def no_hr_ride_path(self) -> Path:
        return Path(__file__).parent / "test_data" / "no_hr_ride.gpx"

    @pytest.fixture
    def simple_parser(self, simple_ride_path: Path) -> GPXParser:
        return GPXParser(simple_ride_path)

    @pytest.fixture
    def no_hr_parser(self, no_hr_ride_path: Path) -> GPXParser:
        return GPXParser(no_hr_ride_path)

    def test_parser_initialization(self, simple_ride_path: Path) -> None:
        parser = GPXParser(simple_ride_path)
        assert parser.file_path == simple_ride_path
        assert parser.gpx is None

    def test_parse_file(self, simple_parser: GPXParser) -> None:
        gpx = simple_parser.parse()
        assert gpx is not None
        assert len(gpx.tracks) == 1
        assert len(gpx.tracks[0].segments) == 1
        assert len(gpx.tracks[0].segments[0].points) == 3

    def test_get_track_count(self, simple_parser: GPXParser) -> None:
        assert simple_parser.get_track_count() == 1

    def test_get_waypoint_count(self, simple_parser: GPXParser) -> None:
        assert simple_parser.get_waypoint_count() == 0

    def test_get_stats_with_heart_rate(self, simple_parser: GPXParser) -> None:
        stats = simple_parser.get_stats()

        assert isinstance(stats, GPXStats)
        assert stats.total_distance > 0
        assert stats.avg_heart_rate == pytest.approx(155.0)  # type: ignore[arg-type]
        assert stats.max_heart_rate == 160.0
        assert stats.activity_type == "cycling"
        assert stats.start_time is not None
        assert stats.end_time is not None

    def test_get_stats_without_heart_rate(self, no_hr_parser: GPXParser) -> None:
        stats = no_hr_parser.get_stats()

        assert isinstance(stats, GPXStats)
        assert stats.total_distance > 0
        assert stats.avg_heart_rate is None
        assert stats.max_heart_rate is None
        assert stats.activity_type == "running"

    def test_heart_rate_extraction(self, simple_parser: GPXParser) -> None:
        simple_parser.parse()  # Need to parse first
        heart_rates = simple_parser.extract_heart_rate_data()
        assert len(heart_rates) == 3
        assert heart_rates == [150.0, 155.0, 160.0]

    def test_extract_activity_type(self, simple_parser: GPXParser) -> None:
        simple_parser.parse()  # Need to parse first
        activity_type = simple_parser.extract_activity_type()
        assert activity_type == "cycling"

    def test_max_speed_calculation(self, simple_parser: GPXParser) -> None:
        simple_parser.parse()
        assert simple_parser.gpx is not None
        segment = simple_parser.gpx.tracks[0].segments[0]
        max_speed = simple_parser.calculate_max_speed(segment)
        assert max_speed is not None
        assert max_speed > 0

    def test_get_pace_time_series(self, simple_parser: GPXParser) -> None:
        """Test extraction of pace time series data."""
        time_series = simple_parser.get_pace_time_series()

        # The simple_ride.gpx file has only 3 points, so we might get 2 pace values
        # or none if the points are too close/far apart in time
        assert isinstance(time_series, list)

        # If we have pace data, verify its structure and values
        if len(time_series) > 0:
            for timestamp, pace in time_series:
                assert timestamp is not None
                assert isinstance(pace, float)
                # Reasonable pace range (2-60 min/mile)
                assert 2.0 <= pace <= 60.0

    def test_get_pace_time_series_no_data(self, no_hr_parser: GPXParser) -> None:
        """Test pace extraction when there might be insufficient data."""
        time_series = no_hr_parser.get_pace_time_series()

        assert isinstance(time_series, list)
        # The no_hr_ride.gpx might have pace data even without heart rate

    def test_get_pace_time_series_with_window(self, simple_parser: GPXParser) -> None:
        """Test pace extraction with different window sizes."""
        # Test with small window
        time_series_small = simple_parser.get_pace_time_series(window_size=3)
        assert isinstance(time_series_small, list)

        # Test with larger window
        time_series_large = simple_parser.get_pace_time_series(window_size=7)
        assert isinstance(time_series_large, list)

        # Larger window should produce smoother (potentially fewer) values
        # Both should be valid pace data if present
        for ts in [time_series_small, time_series_large]:
            for timestamp, pace in ts:
                assert timestamp is not None
                assert isinstance(pace, float)
                assert 2.0 <= pace <= 60.0
