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

        click.echo(f"GPX File: {file}")
        click.echo(f"Tracks: {parser.get_track_count()}")
        click.echo(f"Waypoints: {parser.get_waypoint_count()}")
        click.echo()

        if stats.total_distance > 0:
            click.echo(f"Distance: {format_distance(stats.total_distance)}")

        if stats.total_time:
            click.echo(f"Time: {format_time(stats.total_time)}")

        if stats.avg_speed:
            click.echo(f"Average Speed: {format_speed(stats.avg_speed)}")

        if stats.max_speed:
            click.echo(f"Max Speed: {format_speed(stats.max_speed)}")

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


if __name__ == "__main__":
    main()
