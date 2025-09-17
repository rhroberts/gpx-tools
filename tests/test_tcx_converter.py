import pytest
import tempfile
from pathlib import Path
from lxml import etree  # type: ignore
from gpx_tools.tcx_converter import (
    convert_gpx_to_tcx,
    _map_activity_type,
    _extract_heart_rate_from_point,
)
from gpx_tools.parser import GPXParser


class TestTcxConverter:
    @pytest.fixture
    def simple_ride_path(self) -> Path:
        return Path(__file__).parent / "test_data" / "simple_ride.gpx"

    @pytest.fixture
    def no_hr_ride_path(self) -> Path:
        return Path(__file__).parent / "test_data" / "no_hr_ride.gpx"

    def test_convert_gpx_to_tcx_basic(self, simple_ride_path: Path) -> None:
        with tempfile.NamedTemporaryFile(suffix=".tcx", delete=False) as tmp_file:
            output_path = Path(tmp_file.name)

        try:
            convert_gpx_to_tcx(simple_ride_path, output_path)

            # Verify the output file was created and has content
            assert output_path.exists()
            assert output_path.stat().st_size > 0

            # Parse and validate the TCX file structure
            tree = etree.parse(str(output_path))
            root = tree.getroot()

            # Check namespace
            assert "TrainingCenterDatabase" in root.tag
            assert (
                "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2" in root.tag
            )

            # Check for Activities element
            activities = root.find(
                ".//{http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2}Activities"
            )
            assert activities is not None

            # Check for at least one Activity
            activity = activities.find(
                ".//{http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2}Activity"
            )
            assert activity is not None
            assert activity.get("Sport") in ["Running", "Biking", "Other"]

        finally:
            output_path.unlink(missing_ok=True)

    def test_convert_gpx_to_tcx_with_heart_rate(self, simple_ride_path: Path) -> None:
        with tempfile.NamedTemporaryFile(suffix=".tcx", delete=False) as tmp_file:
            output_path = Path(tmp_file.name)

        try:
            convert_gpx_to_tcx(simple_ride_path, output_path)

            # Parse and check for heart rate data
            tree = etree.parse(str(output_path))

            # Look for heart rate elements
            hr_elements = tree.findall(
                ".//{http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2}HeartRateBpm"
            )
            assert len(hr_elements) > 0

            # Verify heart rate values are reasonable
            for hr_elem in hr_elements:
                value_elem = hr_elem.find(
                    ".//{http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2}Value"
                )
                if value_elem is not None and value_elem.text:
                    hr_value = int(value_elem.text)
                    assert 50 <= hr_value <= 250  # Reasonable heart rate range

        finally:
            output_path.unlink(missing_ok=True)

    def test_convert_gpx_to_tcx_no_heart_rate(self, no_hr_ride_path: Path) -> None:
        with tempfile.NamedTemporaryFile(suffix=".tcx", delete=False) as tmp_file:
            output_path = Path(tmp_file.name)

        try:
            convert_gpx_to_tcx(no_hr_ride_path, output_path)

            # Verify the output file was created
            assert output_path.exists()
            assert output_path.stat().st_size > 0

            # Parse and verify no heart rate data
            tree = etree.parse(str(output_path))
            hr_elements = tree.findall(
                ".//{http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2}HeartRateBpm"
            )
            assert len(hr_elements) == 0

        finally:
            output_path.unlink(missing_ok=True)

    def test_tcx_structure_elements(self, simple_ride_path: Path) -> None:
        with tempfile.NamedTemporaryFile(suffix=".tcx", delete=False) as tmp_file:
            output_path = Path(tmp_file.name)

        try:
            convert_gpx_to_tcx(simple_ride_path, output_path)

            tree = etree.parse(str(output_path))
            tcx_ns = "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"

            # Check for required TCX elements
            activities = tree.find(f".//{{{tcx_ns}}}Activities")
            assert activities is not None

            activity = tree.find(f".//{{{tcx_ns}}}Activity")
            assert activity is not None

            lap = tree.find(f".//{{{tcx_ns}}}Lap")
            assert lap is not None

            track = tree.find(f".//{{{tcx_ns}}}Track")
            assert track is not None

            trackpoints = tree.findall(f".//{{{tcx_ns}}}Trackpoint")
            assert len(trackpoints) > 0

            # Check for position data in trackpoints
            positions = tree.findall(f".//{{{tcx_ns}}}Position")
            assert len(positions) > 0

            # Check for time data
            times = tree.findall(f".//{{{tcx_ns}}}Time")
            assert len(times) > 0

        finally:
            output_path.unlink(missing_ok=True)

    def test_map_activity_type(self) -> None:
        assert _map_activity_type("cycling") == "Biking"
        assert _map_activity_type("running") == "Running"
        assert _map_activity_type("walking") == "Other"
        assert _map_activity_type("hiking") == "Other"
        assert _map_activity_type(None) == "Biking"
        assert _map_activity_type("unknown") == "Biking"

    def test_extract_heart_rate_from_point(self, simple_ride_path: Path) -> None:
        # Parse the GPX file to get points with heart rate data
        parser = GPXParser(simple_ride_path)
        parser.parse()

        assert parser.gpx is not None
        track = parser.gpx.tracks[0]
        segment = track.segments[0]
        point = segment.points[0]

        # Test heart rate extraction
        hr_value = _extract_heart_rate_from_point(point)
        assert hr_value is not None
        assert isinstance(hr_value, float)
        assert 50 <= hr_value <= 250  # Reasonable heart rate range

    def test_extract_heart_rate_from_point_no_hr(self, no_hr_ride_path: Path) -> None:
        # Parse the GPX file without heart rate data
        parser = GPXParser(no_hr_ride_path)
        parser.parse()

        assert parser.gpx is not None
        track = parser.gpx.tracks[0]
        segment = track.segments[0]
        point = segment.points[0]

        # Test that no heart rate is extracted
        hr_value = _extract_heart_rate_from_point(point)
        assert hr_value is None

    def test_convert_nonexistent_file(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".tcx", delete=False) as tmp_file:
            output_path = Path(tmp_file.name)

        try:
            nonexistent_path = Path("nonexistent.gpx")
            with pytest.raises(FileNotFoundError):
                convert_gpx_to_tcx(nonexistent_path, output_path)

        finally:
            output_path.unlink(missing_ok=True)
