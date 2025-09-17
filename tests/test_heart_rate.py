import pytest
import tempfile
from pathlib import Path
from gpx_tools.heart_rate import (
    strip_heart_rate_data,
    replace_heart_rate_data,
)
from gpx_tools.parser import GPXParser


class TestHeartRateOperations:
    @pytest.fixture
    def simple_ride_path(self) -> Path:
        return Path(__file__).parent / "test_data" / "simple_ride.gpx"

    @pytest.fixture
    def no_hr_ride_path(self) -> Path:
        return Path(__file__).parent / "test_data" / "no_hr_ride.gpx"

    def test_strip_heart_rate_data(self, simple_ride_path: Path) -> None:
        with tempfile.NamedTemporaryFile(suffix=".gpx", delete=False) as tmp_file:
            output_path = Path(tmp_file.name)

        try:
            strip_heart_rate_data(simple_ride_path, output_path)

            # Verify the output file was created
            assert output_path.exists()

            # Parse the stripped file and verify no heart rate data
            parser = GPXParser(output_path)
            stats = parser.get_stats()

            assert stats.avg_heart_rate is None
            assert stats.max_heart_rate is None

            # Verify other data is preserved
            assert stats.total_distance > 0
            assert stats.activity_type == "cycling"

        finally:
            output_path.unlink(missing_ok=True)

    def test_replace_heart_rate_data(self, simple_ride_path: Path) -> None:
        with tempfile.NamedTemporaryFile(suffix=".gpx", delete=False) as tmp_file:
            output_path = Path(tmp_file.name)

        try:
            target_avg_hr = 140
            variation = 5

            replace_heart_rate_data(
                simple_ride_path, output_path, target_avg_hr, variation
            )

            # Verify the output file was created
            assert output_path.exists()

            # Parse the replaced file and verify heart rate data
            parser = GPXParser(output_path)
            stats = parser.get_stats()

            # Heart rate should be close to target
            assert stats.avg_heart_rate is not None
            assert (
                abs(stats.avg_heart_rate - target_avg_hr) <= variation + 5
            )  # Allow some tolerance

            # Verify other data is preserved
            assert stats.total_distance > 0
            assert stats.activity_type == "cycling"

        finally:
            output_path.unlink(missing_ok=True)

    def test_strip_file_without_heart_rate(self, no_hr_ride_path: Path) -> None:
        with tempfile.NamedTemporaryFile(suffix=".gpx", delete=False) as tmp_file:
            output_path = Path(tmp_file.name)

        try:
            strip_heart_rate_data(no_hr_ride_path, output_path)

            # Verify the output file was created
            assert output_path.exists()

            # Parse and verify no heart rate data (same as input)
            parser = GPXParser(output_path)
            stats = parser.get_stats()

            assert stats.avg_heart_rate is None
            assert stats.max_heart_rate is None
            assert stats.total_distance > 0
            assert stats.activity_type == "running"

        finally:
            output_path.unlink(missing_ok=True)

    def test_replace_file_without_heart_rate(self, no_hr_ride_path: Path) -> None:
        with tempfile.NamedTemporaryFile(suffix=".gpx", delete=False) as tmp_file:
            output_path = Path(tmp_file.name)

        try:
            target_avg_hr = 140

            replace_heart_rate_data(no_hr_ride_path, output_path, target_avg_hr)

            # Since original file has no HR data, output should also have none
            parser = GPXParser(output_path)
            stats = parser.get_stats()

            assert stats.avg_heart_rate is None
            assert stats.max_heart_rate is None

        finally:
            output_path.unlink(missing_ok=True)

    def test_is_heart_rate_extension(self) -> None:
        # This is a private function, but we can test it for completeness
        # Would need to create mock XML elements to properly test this
        pass  # Skip for now as it requires complex XML mocking
