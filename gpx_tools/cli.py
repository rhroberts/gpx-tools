import sys
from pathlib import Path

import click

from .constants import DEFAULT_HR_VARIATION
from .formatting import print_gpx_stats
from .heart_rate import replace_heart_rate_data, strip_heart_rate_data
from .parser import GPXParser
from .tcx_converter import convert_gpx_to_tcx
from .visualization import (
    create_heart_rate_chart,
    create_pace_chart,
    create_speed_chart,
    validate_heart_rate_data,
    validate_pace_data,
    validate_speed_data,
)


@click.group()
def main() -> None:
    """GPX file tools for processing outdoor activity data."""
    pass


@main.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
def parse(file: Path) -> None:
    """Parse and display GPX file information."""
    parser = GPXParser(file)

    try:
        parser.parse()
        stats = parser.get_stats()
        print_gpx_stats(file, parser, stats)

    except Exception as e:
        click.echo(f"Error parsing GPX file: {e}", err=True)
        sys.exit(1)


@main.command("strip-hr")
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.argument("output_file", type=click.Path(path_type=Path))
def strip_heart_rate(input_file: Path, output_file: Path) -> None:
    """Strip heart rate data from a GPX file."""
    try:
        strip_heart_rate_data(input_file, output_file)
        click.echo(f"Heart rate data stripped from {input_file} -> {output_file}")

    except Exception as e:
        click.echo(f"Error stripping heart rate data: {e}", err=True)
        sys.exit(1)


@main.command("replace-hr")
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.argument("output_file", type=click.Path(path_type=Path))
@click.argument("avg_hr", type=int)
@click.option(
    "--variation",
    type=int,
    default=DEFAULT_HR_VARIATION,
    help=f"Heart rate variation around average (default: {DEFAULT_HR_VARIATION} bpm)",
)
def replace_heart_rate(
    input_file: Path, output_file: Path, avg_hr: int, variation: int
) -> None:
    """Replace heart rate data with custom average and realistic variation.

    AVG_HR is your perceived average heart rate for the activity.
    Variation creates realistic fluctuations (±VARIATION bpm around average).
    """
    try:
        replace_heart_rate_data(input_file, output_file, avg_hr, variation)
        click.echo(
            f"Heart rate data replaced with {avg_hr}±{variation} bpm: {input_file} -> {output_file}"
        )

    except Exception as e:
        click.echo(f"Error replacing heart rate data: {e}", err=True)
        sys.exit(1)


@main.command("convert-to-tcx")
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.argument("output_file", type=click.Path(path_type=Path))
def convert_to_tcx(input_file: Path, output_file: Path) -> None:
    """Convert a GPX file to TCX format.

    Converts GPX track data to Garmin TCX format, preserving GPS coordinates,
    elevation, timestamps, and heart rate data when available.
    """
    try:
        convert_gpx_to_tcx(input_file, output_file)
        click.echo(f"GPX file converted to TCX format: {input_file} -> {output_file}")

    except Exception as e:
        click.echo(f"Error converting to TCX format: {e}", err=True)
        sys.exit(1)


@main.group()
def plot() -> None:
    """Visualization commands for GPX data."""
    pass


@plot.command("heart-rate")
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option("--width", default=80, help="Chart width in characters (default: 80)")
@click.option("--height", default=20, help="Chart height in lines (default: 20)")
@click.option(
    "--time-unit",
    type=click.Choice(["auto", "seconds", "minutes"]),
    default="auto",
    help="Time axis unit (default: auto)",
)
def plot_heart_rate(file: Path, width: int, height: int, time_unit: str) -> None:
    """Show heart rate (BPM) over time as an ASCII graph."""
    try:
        parser = GPXParser(file)
        parser.parse()

        time_series = parser.get_heart_rate_time_series()

        # Validate heart rate data
        error_msg = validate_heart_rate_data(time_series)
        if error_msg:
            click.echo(f"Error: {error_msg}", err=True)
            sys.exit(1)

        # Create and display chart
        chart = create_heart_rate_chart(time_series, width, height, time_unit)
        click.echo(chart)

    except Exception as e:
        click.echo(f"Error creating heart rate chart: {e}", err=True)
        sys.exit(1)


@plot.command("pace")
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option("--width", default=80, help="Chart width in characters (default: 80)")
@click.option("--height", default=20, help="Chart height in lines (default: 20)")
@click.option(
    "--time-unit",
    type=click.Choice(["auto", "seconds", "minutes"]),
    default="auto",
    help="Time axis unit (default: auto)",
)
def plot_pace(file: Path, width: int, height: int, time_unit: str) -> None:
    """Show pace (min/mile) over time as an ASCII graph."""
    try:
        parser = GPXParser(file)
        parser.parse()

        time_series = parser.get_pace_time_series()

        # Validate pace data
        error_msg = validate_pace_data(time_series)
        if error_msg:
            click.echo(f"Error: {error_msg}", err=True)
            sys.exit(1)

        # Create and display chart
        chart = create_pace_chart(time_series, width, height, time_unit)
        click.echo(chart)

    except Exception as e:
        click.echo(f"Error creating pace chart: {e}", err=True)
        sys.exit(1)


@plot.command("speed")
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option("--width", default=80, help="Chart width in characters (default: 80)")
@click.option("--height", default=20, help="Chart height in lines (default: 20)")
@click.option(
    "--time-unit",
    type=click.Choice(["auto", "seconds", "minutes"]),
    default="auto",
    help="Time axis unit (default: auto)",
)
def plot_speed(file: Path, width: int, height: int, time_unit: str) -> None:
    """Show speed (mph) over time as an ASCII graph."""
    try:
        parser = GPXParser(file)
        parser.parse()

        time_series = parser.get_speed_time_series()

        # Validate speed data
        error_msg = validate_speed_data(time_series)
        if error_msg:
            click.echo(f"Error: {error_msg}", err=True)
            sys.exit(1)

        # Create and display chart
        chart = create_speed_chart(time_series, width, height, time_unit)
        click.echo(chart)

    except Exception as e:
        click.echo(f"Error creating speed chart: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
