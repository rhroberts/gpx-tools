import click
import sys
from pathlib import Path
from .parser import GPXParser
from .formatting import print_gpx_stats
from .heart_rate import strip_heart_rate_data, replace_heart_rate_data
from .tcx_converter import convert_gpx_to_tcx
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


if __name__ == "__main__":
    main()
