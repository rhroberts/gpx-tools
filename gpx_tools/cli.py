import argparse
import sys
from pathlib import Path
from .parser import GPXParser


def format_distance(distance_meters: float) -> str:
    if distance_meters >= 1000:
        return f"{distance_meters / 1000:.2f} km"
    return f"{distance_meters:.1f} m"


def format_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_speed(speed_mps: float) -> str:
    kmh = speed_mps * 3.6
    return f"{kmh:.1f} km/h"


def parse_command(args):
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
            print(f"Elevation: {stats.min_elevation:.0f}m - {stats.max_elevation:.0f}m")

        if stats.total_uphill:
            print(f"Uphill: {stats.total_uphill:.0f}m")

        if stats.total_downhill:
            print(f"Downhill: {stats.total_downhill:.0f}m")

        if stats.start_time:
            print(f"Start: {stats.start_time}")

        if stats.end_time:
            print(f"End: {stats.end_time}")

    except Exception as e:
        print(f"Error parsing GPX file: {e}", file=sys.stderr)
        sys.exit(1)


def main():
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
