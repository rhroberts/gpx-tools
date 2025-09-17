import click
import sys
from pathlib import Path
from .parser import GPXParser
from .formatting import (
    format_distance,
    format_time,
    format_speed,
    format_elevation,
    format_datetime,
    format_heart_rate,
    format_activity_type,
)
from .heart_rate import strip_heart_rate_data, replace_heart_rate_data
from .constants import DEFAULT_HR_VARIATION


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

        click.echo(f"GPX File: {file}")
        click.echo(f"Tracks: {parser.get_track_count()}")
        click.echo(f"Waypoints: {parser.get_waypoint_count()}")

        if stats.activity_type:
            click.echo(f"Activity: {format_activity_type(stats.activity_type)}")

        click.echo()

        if stats.total_distance > 0:
            click.echo(f"Distance: {format_distance(stats.total_distance)}")

        if stats.total_time:
            click.echo(f"Time: {format_time(stats.total_time)}")

        if stats.avg_speed:
            click.echo(f"Average Speed: {format_speed(stats.avg_speed)}")

        if stats.max_speed:
            click.echo(f"Max Speed: {format_speed(stats.max_speed)}")

        if stats.avg_heart_rate:
            click.echo(f"Average Heart Rate: {format_heart_rate(stats.avg_heart_rate)}")

        if stats.max_heart_rate:
            click.echo(f"Max Heart Rate: {format_heart_rate(stats.max_heart_rate)}")

        if stats.max_elevation is not None and stats.min_elevation is not None:
            click.echo(
                f"Elevation: {format_elevation(stats.min_elevation)} - {format_elevation(stats.max_elevation)}"
            )

        if stats.total_uphill:
            click.echo(f"Uphill: {format_elevation(stats.total_uphill)}")

        if stats.total_downhill:
            click.echo(f"Downhill: {format_elevation(stats.total_downhill)}")

        if stats.start_time:
            click.echo(f"Start: {format_datetime(stats.start_time)}")

        if stats.end_time:
            click.echo(f"End: {format_datetime(stats.end_time)}")

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


if __name__ == "__main__":
    main()
