import argparse
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


def parse_command(args: argparse.Namespace) -> None:
    parser = GPXParser(args.file)

    try:
        parser.parse()
        stats = parser.get_stats()

        print(f"GPX File: {args.file}")
        print(f"Tracks: {parser.get_track_count()}")
        print(f"Waypoints: {parser.get_waypoint_count()}")
        print()

        if stats.total_distance > 0:
            print(f"Distance: {format_distance(stats.total_distance)}")

        if stats.total_time:
            print(f"Time: {format_time(stats.total_time)}")

        if stats.avg_speed:
            print(f"Average Speed: {format_speed(stats.avg_speed)}")

        if stats.max_speed:
            print(f"Max Speed: {format_speed(stats.max_speed)}")

        if stats.max_elevation is not None and stats.min_elevation is not None:
            print(
                f"Elevation: {format_elevation(stats.min_elevation)} - {format_elevation(stats.max_elevation)}"
            )

        if stats.total_uphill:
            print(f"Uphill: {format_elevation(stats.total_uphill)}")

        if stats.total_downhill:
            print(f"Downhill: {format_elevation(stats.total_downhill)}")

        if stats.start_time:
            print(f"Start: {format_datetime(stats.start_time)}")

        if stats.end_time:
            print(f"End: {format_datetime(stats.end_time)}")

    except Exception as e:
        print(f"Error parsing GPX file: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="GPX file tools")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    parse_parser = subparsers.add_parser(
        "parse", help="Parse and display GPX file information"
    )
    parse_parser.add_argument("file", type=Path, help="GPX file to parse")

    args = parser.parse_args()

    if args.command == "parse":
        parse_command(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
