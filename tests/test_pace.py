import pytest
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple
from gpx_tools.visualization import (
    create_pace_chart,
    validate_pace_data,
)
from gpx_tools.parser import GPXParser
from gpx_tools.formatting import format_pace


class TestPace:
    @pytest.fixture
    def sample_pace_time_series(self) -> List[Tuple[datetime, float]]:
        """Create sample pace time series data."""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        time_series: List[Tuple[datetime, float]] = []

        # Create 10 data points over 5 minutes with varying pace
        pace_values = [8.5, 8.3, 8.1, 8.0, 7.9, 8.0, 8.2, 8.4, 8.5, 8.7]

        for i, pace in enumerate(pace_values):
            timestamp = start_time + timedelta(seconds=i * 30)  # Every 30 seconds
            time_series.append((timestamp, float(pace)))

        return time_series

    @pytest.fixture
    def simple_ride_path(self) -> Path:
        return Path(__file__).parent / "test_data" / "simple_ride.gpx"

    def test_format_pace(self):
        """Test pace formatting."""
        assert format_pace(8.5) == "8:30 min/mi"
        assert format_pace(7.0) == "7:00 min/mi"
        assert format_pace(10.25) == "10:15 min/mi"
        assert format_pace(5.75) == "5:45 min/mi"
        assert format_pace(12.167) == "12:10 min/mi"  # 12 + 0.167*60 = 12:10

    def test_create_pace_chart_basic(
        self, sample_pace_time_series: List[Tuple[datetime, float]]
    ):
        """Test basic pace chart creation."""
        chart = create_pace_chart(sample_pace_time_series)

        assert "Pace (min/mile) over Time" in chart
        assert "Duration:" in chart
        assert "Avg Pace:" in chart
        assert "Fastest:" in chart
        assert "Slowest:" in chart
        assert "min/mi" in chart

    def test_create_pace_chart_custom_dimensions(
        self, sample_pace_time_series: List[Tuple[datetime, float]]
    ):
        """Test chart creation with custom width and height."""
        chart = create_pace_chart(sample_pace_time_series, width=60, height=15)

        assert "Pace (min/mile) over Time" in chart

    def test_create_pace_chart_time_units(
        self, sample_pace_time_series: List[Tuple[datetime, float]]
    ):
        """Test chart creation with different time units."""
        chart_auto = create_pace_chart(sample_pace_time_series, time_unit="auto")
        assert "Pace (min/mile) over Time" in chart_auto

        chart_seconds = create_pace_chart(sample_pace_time_series, time_unit="seconds")
        assert "Pace (min/mile) over Time" in chart_seconds

        chart_minutes = create_pace_chart(sample_pace_time_series, time_unit="minutes")
        assert "Pace (min/mile) over Time" in chart_minutes

    def test_create_pace_chart_empty_data(self):
        """Test chart creation with empty data."""
        chart = create_pace_chart([])
        assert "No pace data available" in chart

    def test_create_pace_chart_long_duration(self):
        """Test chart with long duration."""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        time_series: List[Tuple[datetime, float]] = []

        # Create data over 20 minutes
        for i in range(20):
            timestamp = start_time + timedelta(minutes=i)
            pace = 8.0 + (i % 5) * 0.2  # Varying pace 8.0-8.8
            time_series.append((timestamp, float(pace)))

        chart = create_pace_chart(time_series, time_unit="auto")
        assert "Pace (min/mile) over Time" in chart
        assert "Duration: 19:00" in chart

    def test_validate_pace_data_valid(
        self, sample_pace_time_series: List[Tuple[datetime, float]]
    ):
        """Test validation with valid pace data."""
        result = validate_pace_data(sample_pace_time_series)
        assert result is None  # No error

    def test_validate_pace_data_empty(self):
        """Test validation with empty data."""
        result = validate_pace_data([])
        assert result is not None and "No pace data found" in result

    def test_validate_pace_data_insufficient(self):
        """Test validation with insufficient data points."""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        time_series = [(start_time, 8.0)]  # Only one point

        result = validate_pace_data(time_series)
        assert result is not None and "Insufficient pace data points" in result

    def test_validate_pace_data_invalid_values(self):
        """Test validation with invalid pace values."""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        time_series = [
            (start_time, 1.5),  # Too fast (< 2 min/mile)
            (start_time + timedelta(seconds=30), 65.0),  # Too slow (> 60 min/mile)
        ]

        result = validate_pace_data(time_series)
        assert result is not None and "invalid" in result.lower()

    def test_pace_statistics_accuracy(
        self, sample_pace_time_series: List[Tuple[datetime, float]]
    ):
        """Test that chart statistics are accurate."""
        chart = create_pace_chart(sample_pace_time_series)

        # Extract pace values for verification
        pace_values = [pace for _, pace in sample_pace_time_series]
        expected_avg = sum(pace_values) / len(pace_values)
        expected_max = max(pace_values)  # Slowest
        expected_min = min(pace_values)  # Fastest

        # Chart should contain correct statistics
        expected_avg_str = format_pace(expected_avg)
        expected_max_str = format_pace(expected_max)
        expected_min_str = format_pace(expected_min)

        assert f"Avg Pace: {expected_avg_str}" in chart
        assert f"Fastest: {expected_min_str}" in chart
        assert f"Slowest: {expected_max_str}" in chart

    def test_integration_with_real_gpx(self, simple_ride_path: Path):
        """Test integration with real GPX file."""
        if not simple_ride_path.exists():
            pytest.skip("Test GPX file not found")

        parser = GPXParser(simple_ride_path)
        parser.parse()

        time_series = parser.get_pace_time_series()
        # GPX file might not have enough data for pace calculation
        if len(time_series) > 0:
            # Should be able to create chart without errors
            chart = create_pace_chart(time_series)
            assert "Pace (min/mile) over Time" in chart
            assert "min/mi" in chart

    def test_large_dataset_pace_chart_creation(self):
        """Test chart creation with a large dataset that needs downsampling."""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        # Create a large dataset (1000 points over ~16 minutes)
        time_series: List[Tuple[datetime, float]] = []
        for i in range(1000):
            timestamp = start_time + timedelta(seconds=i)
            # Create some realistic variation (7-9 min/mile)
            pace = 8.0 + 1.0 * (0.5 + 0.3 * (i % 30) / 30)  # Varies between 7-9
            time_series.append((timestamp, pace))

        # Should not crash and should produce reasonable output
        chart = create_pace_chart(time_series, width=80, height=20)
        assert "Pace (min/mile) over Time" in chart
        assert "Duration:" in chart
        assert "min/mi" in chart
