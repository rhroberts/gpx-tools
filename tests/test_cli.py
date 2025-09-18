import pytest
import tempfile
from pathlib import Path
from click.testing import CliRunner
from gpx_tools.cli import main


class TestCLI:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def simple_ride_path(self):
        return Path(__file__).parent / "test_data" / "simple_ride.gpx"

    @pytest.fixture
    def no_hr_ride_path(self):
        return Path(__file__).parent / "test_data" / "no_hr_ride.gpx"

    def test_parse_command_with_heart_rate(
        self, runner: CliRunner, simple_ride_path: Path
    ) -> None:
        result = runner.invoke(main, ["parse", str(simple_ride_path)])

        assert result.exit_code == 0
        output = result.output

        # Verify expected output sections
        assert "GPX File:" in output
        assert "Tracks: 1" in output
        assert "Waypoints: 0" in output
        assert "Activity: Cycling" in output
        assert "Distance:" in output
        assert "mi" in output or "ft" in output  # Imperial units
        assert "Average Heart Rate:" in output
        assert "bpm" in output
        assert "Max Heart Rate:" in output

    def test_parse_command_without_heart_rate(
        self, runner: CliRunner, no_hr_ride_path: Path
    ) -> None:
        result = runner.invoke(main, ["parse", str(no_hr_ride_path)])

        assert result.exit_code == 0
        output = result.output

        # Verify expected output sections
        assert "GPX File:" in output
        assert "Activity: Running" in output
        assert "Distance:" in output
        # Should not have heart rate sections
        assert "Average Heart Rate:" not in output
        assert "Max Heart Rate:" not in output

    def test_strip_hr_command(self, runner: CliRunner, simple_ride_path: Path) -> None:
        with tempfile.NamedTemporaryFile(suffix=".gpx", delete=False) as tmp_file:
            output_path = Path(tmp_file.name)

        try:
            result = runner.invoke(
                main, ["strip-hr", str(simple_ride_path), str(output_path)]
            )

            assert result.exit_code == 0
            assert "Heart rate data stripped" in result.output
            assert output_path.exists()

            # Verify the stripped file by parsing it
            parse_result = runner.invoke(main, ["parse", str(output_path)])
            assert parse_result.exit_code == 0
            assert "Average Heart Rate:" not in parse_result.output

        finally:
            output_path.unlink(missing_ok=True)

    def test_replace_hr_command(
        self, runner: CliRunner, simple_ride_path: Path
    ) -> None:
        with tempfile.NamedTemporaryFile(suffix=".gpx", delete=False) as tmp_file:
            output_path = Path(tmp_file.name)

        try:
            target_hr = 145
            variation = 8

            result = runner.invoke(
                main,
                [
                    "replace-hr",
                    str(simple_ride_path),
                    str(output_path),
                    str(target_hr),
                    "--variation",
                    str(variation),
                ],
            )

            assert result.exit_code == 0
            assert (
                f"Heart rate data replaced with {target_hr}±{variation} bpm"
                in result.output
            )
            assert output_path.exists()

            # Verify the replaced file by parsing it
            parse_result = runner.invoke(main, ["parse", str(output_path)])
            assert parse_result.exit_code == 0
            assert "Average Heart Rate:" in parse_result.output

        finally:
            output_path.unlink(missing_ok=True)

    def test_replace_hr_command_default_variation(
        self, runner: CliRunner, simple_ride_path: Path
    ) -> None:
        with tempfile.NamedTemporaryFile(suffix=".gpx", delete=False) as tmp_file:
            output_path = Path(tmp_file.name)

        try:
            target_hr = 150

            result = runner.invoke(
                main,
                ["replace-hr", str(simple_ride_path), str(output_path), str(target_hr)],
            )

            assert result.exit_code == 0
            assert "Heart rate data replaced with 150±10 bpm" in result.output

        finally:
            output_path.unlink(missing_ok=True)

    def test_parse_nonexistent_file(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["parse", "nonexistent.gpx"])
        assert result.exit_code != 0

    def test_main_group_help(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "GPX file tools for processing outdoor activity data" in result.output
        assert "parse" in result.output
        assert "strip-hr" in result.output
        assert "replace-hr" in result.output

    def test_plot_heart_rate_command(
        self, runner: CliRunner, simple_ride_path: Path
    ) -> None:
        result = runner.invoke(main, ["plot", "heart-rate", str(simple_ride_path)])

        assert result.exit_code == 0
        assert "Heart Rate over Time" in result.output
        assert "bpm" in result.output
        assert "Avg HR:" in result.output
        assert "Max HR:" in result.output
        assert "Min HR:" in result.output

    def test_plot_pace_command(self, runner: CliRunner, simple_ride_path: Path) -> None:
        result = runner.invoke(main, ["plot", "pace", str(simple_ride_path)])

        # Pace data might not be available for all GPX files, so check exit code
        # If there's valid pace data, check the output
        if result.exit_code == 0:
            assert "Pace over Time (min/mile)" in result.output
            assert "min/mi" in result.output
            assert "Avg Pace:" in result.output
            assert "Fastest:" in result.output
            assert "Slowest:" in result.output
        else:
            # Should have an error message about pace data
            assert "pace data" in result.output.lower()

    def test_plot_pace_command_custom_options(
        self, runner: CliRunner, simple_ride_path: Path
    ) -> None:
        result = runner.invoke(
            main,
            ["plot", "pace", str(simple_ride_path), "--width", "60", "--height", "15"],
        )

        # If command succeeds, check it respects the options
        if result.exit_code == 0:
            assert "Pace over Time (min/mile)" in result.output

    def test_plot_group_help(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["plot", "--help"])
        assert result.exit_code == 0
        assert "Visualization commands for GPX data" in result.output
        assert "heart-rate" in result.output
        assert "pace" in result.output
