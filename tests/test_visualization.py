import pytest
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple
from gpx_tools.visualization import (
    create_heart_rate_chart,
    validate_heart_rate_data,
    downsample_time_series,
)
from gpx_tools.parser import GPXParser


class TestVisualization:
    @pytest.fixture
    def sample_time_series(self) -> List[Tuple[datetime, float]]:
        """Create sample heart rate time series data."""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        time_series: List[Tuple[datetime, float]] = []

        # Create 10 data points over 5 minutes with varying HR
        hr_values = [150, 155, 160, 165, 170, 168, 162, 158, 155, 152]

        for i, hr in enumerate(hr_values):
            timestamp = start_time + timedelta(seconds=i * 30)  # Every 30 seconds
            time_series.append((timestamp, float(hr)))

        return time_series

    @pytest.fixture
    def simple_ride_path(self) -> Path:
        return Path(__file__).parent / "test_data" / "simple_ride.gpx"

    def test_create_heart_rate_chart_basic(
        self, sample_time_series: List[Tuple[datetime, float]]
    ):
        """Test basic heart rate chart creation."""
        chart = create_heart_rate_chart(sample_time_series)

        assert "Heart Rate (BPM) over Time" in chart
        assert "Duration:" in chart
        assert "Avg HR:" in chart
        assert "Max HR:" in chart
        assert "Min HR:" in chart
        assert "bpm" in chart

    def test_create_heart_rate_chart_custom_dimensions(
        self, sample_time_series: List[Tuple[datetime, float]]
    ):
        """Test chart creation with custom width and height."""
        chart = create_heart_rate_chart(sample_time_series, width=60, height=15)

        assert "Heart Rate (BPM) over Time" in chart
        # Chart should be generated without errors

    def test_create_heart_rate_chart_time_units(
        self, sample_time_series: List[Tuple[datetime, float]]
    ):
        """Test chart creation with different time units."""
        # Since we simplified the chart to not show time axis labels,
        # just test that different time units don't break the chart generation
        chart_auto = create_heart_rate_chart(sample_time_series, time_unit="auto")
        assert "Heart Rate (BPM) over Time" in chart_auto

        chart_seconds = create_heart_rate_chart(sample_time_series, time_unit="seconds")
        assert "Heart Rate (BPM) over Time" in chart_seconds

        chart_minutes = create_heart_rate_chart(sample_time_series, time_unit="minutes")
        assert "Heart Rate (BPM) over Time" in chart_minutes

    def test_create_heart_rate_chart_empty_data(self):
        """Test chart creation with empty data."""
        chart = create_heart_rate_chart([])
        assert "No heart rate data available" in chart

    def test_create_heart_rate_chart_long_duration(self):
        """Test chart with long duration."""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        time_series: List[Tuple[datetime, float]] = []

        # Create data over 20 minutes
        for i in range(20):
            timestamp = start_time + timedelta(minutes=i)
            hr = 150 + (i % 10)  # Varying HR
            time_series.append((timestamp, float(hr)))

        chart = create_heart_rate_chart(time_series, time_unit="auto")
        assert "Heart Rate (BPM) over Time" in chart
        assert "Duration: 19:00" in chart  # Should show the correct duration

    def test_validate_heart_rate_data_valid(
        self, sample_time_series: List[Tuple[datetime, float]]
    ):
        """Test validation with valid heart rate data."""
        result = validate_heart_rate_data(sample_time_series)
        assert result is None  # No error

    def test_validate_heart_rate_data_empty(self):
        """Test validation with empty data."""
        result = validate_heart_rate_data([])
        assert result is not None and "No heart rate data found" in result

    def test_validate_heart_rate_data_insufficient(self):
        """Test validation with insufficient data points."""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        time_series = [(start_time, 150.0)]  # Only one point

        result = validate_heart_rate_data(time_series)
        assert result is not None and "Insufficient heart rate data points" in result

    def test_validate_heart_rate_data_invalid_values(self):
        """Test validation with invalid heart rate values."""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        time_series = [
            (start_time, 10.0),  # Too low
            (start_time + timedelta(seconds=30), 250.0),  # Too high
        ]

        result = validate_heart_rate_data(time_series)
        assert result is not None and "invalid" in result.lower()

    # Removed time axis tests since we simplified the chart to not show x-axis labels

    def test_integration_with_real_gpx(self, simple_ride_path: Path):
        """Test integration with real GPX file."""
        parser = GPXParser(simple_ride_path)
        parser.parse()

        time_series = parser.get_heart_rate_time_series()
        assert len(time_series) > 0

        # Should be able to create chart without errors
        chart = create_heart_rate_chart(time_series)
        assert "Heart Rate (BPM) over Time" in chart
        assert "bpm" in chart

    def test_heart_rate_statistics_accuracy(
        self, sample_time_series: List[Tuple[datetime, float]]
    ):
        """Test that chart statistics are accurate."""
        chart = create_heart_rate_chart(sample_time_series)

        # Extract HR values for verification
        hr_values = [hr for _, hr in sample_time_series]
        expected_avg = sum(hr_values) / len(hr_values)
        expected_max = max(hr_values)
        expected_min = min(hr_values)

        # Chart should contain correct statistics (using format_heart_rate which rounds)
        from gpx_tools.formatting import format_heart_rate

        expected_avg_str = format_heart_rate(expected_avg)
        expected_max_str = format_heart_rate(expected_max)
        expected_min_str = format_heart_rate(expected_min)

        assert f"Avg HR: {expected_avg_str}" in chart
        assert f"Max HR: {expected_max_str}" in chart
        assert f"Min HR: {expected_min_str}" in chart

    def test_downsample_time_series_no_downsampling_needed(self):
        """Test downsampling when no downsampling is needed."""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        time_series = [
            (start_time + timedelta(seconds=i), float(150 + i)) for i in range(5)
        ]

        result = downsample_time_series(time_series, 10)
        assert len(result) == 5  # Should return original series
        assert result == time_series

    def test_downsample_time_series_with_downsampling(self):
        """Test downsampling when downsampling is needed."""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        # Create 100 data points
        time_series = [
            (start_time + timedelta(seconds=i), float(150 + i % 20)) for i in range(100)
        ]

        result = downsample_time_series(time_series, 10)
        assert len(result) == 10
        # Should include first and last points
        assert result[0] == time_series[0]
        assert result[-1] == time_series[-1]

    def test_large_dataset_chart_creation(self):
        """Test chart creation with a large dataset that needs downsampling."""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        # Create a large dataset (1000 points over ~16 minutes)
        time_series: List[Tuple[datetime, float]] = []
        for i in range(1000):
            timestamp = start_time + timedelta(seconds=i)
            # Create some realistic variation
            hr = 150 + 20 * (0.5 + 0.3 * (i % 30) / 30)  # Varies between 150-170
            time_series.append((timestamp, hr))

        # Should not crash and should produce reasonable output
        chart = create_heart_rate_chart(time_series, width=80, height=20)
        assert "Heart Rate (BPM) over Time" in chart
        assert "Duration:" in chart
        assert "bpm" in chart


class TestSpeedVisualization:
    def test_create_speed_chart_basic(self) -> None:
        """Test basic speed chart creation."""
        from gpx_tools.visualization import create_speed_chart

        start_time = datetime(2024, 1, 1, 10, 0, 0)
        time_series = [
            (start_time, 12.0),
            (start_time + timedelta(seconds=60), 13.5),
            (start_time + timedelta(seconds=120), 14.0),
            (start_time + timedelta(seconds=180), 13.0),
        ]

        chart = create_speed_chart(time_series, width=40, height=10)

        assert "Speed (mph) over Time" in chart
        assert "mph" in chart
        assert "Duration:" in chart
        assert "Avg Speed:" in chart
        assert "Max:" in chart
        assert "Min:" in chart

    def test_validate_speed_data(self) -> None:
        """Test speed data validation."""
        from gpx_tools.visualization import validate_speed_data

        # Empty data
        assert validate_speed_data([]) == "No speed data found in GPX file"

        # Insufficient data
        single_point = [(datetime.now(), 10.0)]
        assert (
            validate_speed_data(single_point)
            == "Insufficient speed data points for visualization"
        )

        # Valid data
        valid_series = [
            (datetime.now(), 10.0),
            (datetime.now() + timedelta(seconds=60), 12.0),
        ]
        assert validate_speed_data(valid_series) is None

    def test_speed_chart_with_large_dataset(self) -> None:
        """Test speed chart with many data points."""
        from gpx_tools.visualization import create_speed_chart
        from typing import List, Tuple

        start_time = datetime.now()
        time_series: List[Tuple[datetime, float]] = []

        # Generate 500 data points
        for i in range(500):
            timestamp = start_time + timedelta(seconds=i)
            # Create some realistic speed variation
            speed = 12.0 + 3.0 * (0.5 + 0.3 * (i % 30) / 30)  # Varies between 12-15 mph
            time_series.append((timestamp, speed))

        # Should downsample and produce reasonable output
        chart = create_speed_chart(time_series, width=80, height=20)
        assert "Speed (mph) over Time" in chart
        assert "Duration:" in chart
        assert "mph" in chart


class TestElevationVisualization:
    def test_create_elevation_chart_basic(self) -> None:
        """Test basic elevation chart creation."""
        from gpx_tools.visualization import create_elevation_chart

        start_time = datetime(2024, 1, 1, 10, 0, 0)
        time_series = [
            (start_time, 1000.0),
            (start_time + timedelta(seconds=60), 1050.0),
            (start_time + timedelta(seconds=120), 1100.0),
            (start_time + timedelta(seconds=180), 1075.0),
        ]

        chart = create_elevation_chart(time_series, width=40, height=10)

        assert "Elevation (feet) over Time" in chart
        assert "ft" in chart
        assert "Duration:" in chart
        assert "Max:" in chart
        assert "Min:" in chart
        assert "Gain:" in chart
        assert "Loss:" in chart

    def test_validate_elevation_data(self) -> None:
        """Test elevation data validation."""
        from gpx_tools.visualization import validate_elevation_data
        from gpx_tools.constants import MAX_ELEVATION_FEET

        # Empty data
        assert validate_elevation_data([]) == "No elevation data found in GPX file"

        # Insufficient data
        single_point = [(datetime.now(), 1000.0)]
        assert (
            validate_elevation_data(single_point)
            == "Insufficient elevation data points for visualization"
        )

        # Valid data
        valid_series = [
            (datetime.now(), 1000.0),
            (datetime.now() + timedelta(seconds=60), 1100.0),
        ]
        assert validate_elevation_data(valid_series) is None

        # Invalid elevation (too high)
        invalid_high = [
            (datetime.now(), 1000.0),
            (datetime.now() + timedelta(seconds=60), MAX_ELEVATION_FEET + 1000),
        ]
        error_msg = validate_elevation_data(invalid_high)
        assert error_msg is not None
        assert "outside reasonable range" in error_msg

    def test_elevation_gain_loss_calculation(self) -> None:
        """Test elevation gain and loss calculations."""
        from gpx_tools.visualization import (
            calculate_total_elevation_gain,
            calculate_total_elevation_loss,
        )

        start_time = datetime.now()
        time_series = [
            (start_time, 1000.0),
            (start_time + timedelta(seconds=60), 1100.0),  # +100 gain
            (start_time + timedelta(seconds=120), 1050.0),  # -50 loss
            (start_time + timedelta(seconds=180), 1150.0),  # +100 gain
        ]

        assert calculate_total_elevation_gain(time_series) == 200.0
        assert calculate_total_elevation_loss(time_series) == 50.0

    def test_elevation_chart_with_large_dataset(self) -> None:
        """Test elevation chart with many data points."""
        from gpx_tools.visualization import create_elevation_chart
        from typing import List, Tuple

        start_time = datetime.now()
        time_series: List[Tuple[datetime, float]] = []

        # Generate 500 data points with realistic elevation changes
        base_elevation = 1000.0
        for i in range(500):
            timestamp = start_time + timedelta(seconds=i)
            # Create some realistic elevation variation
            import math

            elevation = (
                base_elevation + 200 * math.sin(i * 0.02) + 50 * math.sin(i * 0.1)
            )
            time_series.append((timestamp, elevation))

        # Should downsample and produce reasonable output
        chart = create_elevation_chart(time_series, width=80, height=20)
        assert "Elevation (feet) over Time" in chart
        assert "Duration:" in chart
        assert "Gain:" in chart
        assert "Loss:" in chart
