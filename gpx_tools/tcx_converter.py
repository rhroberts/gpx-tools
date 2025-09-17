from pathlib import Path
from datetime import datetime
from typing import Optional, Any
import gpxpy
from lxml import etree  # type: ignore


def convert_gpx_to_tcx(input_file: Path, output_file: Path) -> None:
    """Convert a GPX file to TCX format."""
    with open(input_file, "r") as gpx_file:
        gpx = gpxpy.parse(gpx_file)

    # Create TCX root element with namespaces
    tcx_ns = "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"
    activityext_ns = "http://www.garmin.com/xmlschemas/ActivityExtension/v2"

    nsmap = {None: tcx_ns, "ns3": activityext_ns}

    root = etree.Element("{%s}TrainingCenterDatabase" % tcx_ns, nsmap=nsmap)
    activities = etree.SubElement(root, "{%s}Activities" % tcx_ns)

    # Process each track as an activity
    for track in gpx.tracks:
        activity = etree.SubElement(activities, "{%s}Activity" % tcx_ns)

        # Determine sport type from track type or default to cycling
        sport_type = _map_activity_type(track.type if hasattr(track, "type") else None)
        activity.set("Sport", sport_type)

        # Add activity ID (start time of first segment)
        activity_id = _get_activity_start_time(track)
        if activity_id:
            id_elem = etree.SubElement(activity, "{%s}Id" % tcx_ns)
            id_elem.text = activity_id.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        # Process each segment as a lap
        for segment in track.segments:
            if not segment.points:
                continue

            lap = etree.SubElement(activity, "{%s}Lap" % tcx_ns)

            # Lap start time
            start_time = segment.points[0].time
            if start_time:
                lap.set("StartTime", start_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"))

            # Calculate lap statistics
            lap_stats = _calculate_lap_stats(segment)

            # Add lap elements
            _add_lap_elements(lap, lap_stats, tcx_ns)

            # Add track data
            track_elem = etree.SubElement(lap, "{%s}Track" % tcx_ns)

            # Process each point as a trackpoint
            for point in segment.points:
                trackpoint = etree.SubElement(track_elem, "{%s}Trackpoint" % tcx_ns)

                # Time
                if point.time:
                    time_elem = etree.SubElement(trackpoint, "{%s}Time" % tcx_ns)
                    time_elem.text = point.time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

                # Position
                if point.latitude is not None and point.longitude is not None:
                    position = etree.SubElement(trackpoint, "{%s}Position" % tcx_ns)
                    lat_elem = etree.SubElement(
                        position, "{%s}LatitudeDegrees" % tcx_ns
                    )
                    lat_elem.text = str(point.latitude)
                    lon_elem = etree.SubElement(
                        position, "{%s}LongitudeDegrees" % tcx_ns
                    )
                    lon_elem.text = str(point.longitude)

                # Altitude
                if point.elevation is not None:
                    alt_elem = etree.SubElement(
                        trackpoint, "{%s}AltitudeMeters" % tcx_ns
                    )
                    alt_elem.text = str(point.elevation)

                # Heart Rate
                hr_value = _extract_heart_rate_from_point(point)
                if hr_value:
                    hr_elem = etree.SubElement(trackpoint, "{%s}HeartRateBpm" % tcx_ns)
                    value_elem = etree.SubElement(hr_elem, "{%s}Value" % tcx_ns)
                    value_elem.text = str(int(hr_value))

        # Add creator information
        creator = etree.SubElement(activity, "{%s}Creator" % tcx_ns)
        creator.set("{http://www.w3.org/2001/XMLSchema-instance}type", "Device_t")
        name_elem = etree.SubElement(creator, "{%s}Name" % tcx_ns)
        name_elem.text = "GPX Tools"

    # Write TCX file
    tree = etree.ElementTree(root)
    tree.write(
        str(output_file), encoding="utf-8", xml_declaration=True, pretty_print=True
    )


def _map_activity_type(gpx_type: Optional[str]) -> str:
    """Map GPX activity type to TCX sport type."""
    if not gpx_type:
        return "Biking"

    gpx_type_lower = gpx_type.lower()

    # Map common activity types
    if "run" in gpx_type_lower:
        return "Running"
    elif "bike" in gpx_type_lower or "cycl" in gpx_type_lower:
        return "Biking"
    elif "walk" in gpx_type_lower or "hik" in gpx_type_lower:
        return "Other"
    elif "swim" in gpx_type_lower:
        return "Other"
    else:
        return "Biking"  # Default to biking


def _get_activity_start_time(track: Any) -> Optional[datetime]:
    """Get the start time of a track."""
    for segment in track.segments:
        if segment.points and segment.points[0].time:
            return segment.points[0].time
    return None


def _calculate_lap_stats(segment: Any) -> dict[str, Any]:
    """Calculate statistics for a lap/segment."""
    stats = {
        "total_time": 0.0,
        "distance": 0.0,
        "max_speed": 0.0,
        "calories": 0,
        "avg_hr": None,
        "max_hr": None,
        "intensity": "Active",
    }

    if not segment.points:
        return stats

    # Calculate distance
    stats["distance"] = segment.length_2d() or 0.0

    # Calculate time
    time_bounds = segment.get_time_bounds()
    if time_bounds and time_bounds.start_time and time_bounds.end_time:
        stats["total_time"] = (
            time_bounds.end_time - time_bounds.start_time
        ).total_seconds()

    # Calculate heart rate stats
    heart_rates = []
    prev_point = None
    max_speed = 0.0

    for point in segment.points:
        # Heart rate
        hr_value = _extract_heart_rate_from_point(point)
        if hr_value:
            heart_rates.append(hr_value)

        # Speed calculation
        if prev_point and point.time and prev_point.time:
            time_diff = (point.time - prev_point.time).total_seconds()
            if time_diff > 0:
                distance = point.distance_2d(prev_point) or 0
                speed = distance / time_diff
                max_speed = max(max_speed, speed)

        prev_point = point

    if heart_rates:
        stats["avg_hr"] = sum(heart_rates) / len(heart_rates)
        stats["max_hr"] = max(heart_rates)

    stats["max_speed"] = max_speed

    # Estimate calories (very rough approximation)
    if stats["total_time"] > 0:
        stats["calories"] = int(stats["total_time"] * 0.1)  # Very rough estimate

    return stats


def _add_lap_elements(lap_elem: Any, stats: dict[str, Any], tcx_ns: str) -> None:
    """Add lap statistic elements to the lap element."""
    # Total time
    if stats["total_time"] > 0:
        time_elem = etree.SubElement(lap_elem, "{%s}TotalTimeSeconds" % tcx_ns)
        time_elem.text = str(stats["total_time"])

    # Distance
    if stats["distance"] > 0:
        dist_elem = etree.SubElement(lap_elem, "{%s}DistanceMeters" % tcx_ns)
        dist_elem.text = str(stats["distance"])

    # Max speed
    if stats["max_speed"] > 0:
        speed_elem = etree.SubElement(lap_elem, "{%s}MaximumSpeed" % tcx_ns)
        speed_elem.text = str(stats["max_speed"])

    # Calories
    calories_elem = etree.SubElement(lap_elem, "{%s}Calories" % tcx_ns)
    calories_elem.text = str(stats["calories"])

    # Average heart rate
    if stats["avg_hr"]:
        avg_hr_elem = etree.SubElement(lap_elem, "{%s}AverageHeartRateBpm" % tcx_ns)
        value_elem = etree.SubElement(avg_hr_elem, "{%s}Value" % tcx_ns)
        value_elem.text = str(int(stats["avg_hr"]))

    # Maximum heart rate
    if stats["max_hr"]:
        max_hr_elem = etree.SubElement(lap_elem, "{%s}MaximumHeartRateBpm" % tcx_ns)
        value_elem = etree.SubElement(max_hr_elem, "{%s}Value" % tcx_ns)
        value_elem.text = str(int(stats["max_hr"]))

    # Intensity
    intensity_elem = etree.SubElement(lap_elem, "{%s}Intensity" % tcx_ns)
    intensity_elem.text = stats["intensity"]

    # Trigger method
    trigger_elem = etree.SubElement(lap_elem, "{%s}TriggerMethod" % tcx_ns)
    trigger_elem.text = "Manual"


def _extract_heart_rate_from_point(point: Any) -> Optional[float]:
    """Extract heart rate from a GPX point's extensions."""
    if not point.extensions:
        return None

    for ext in point.extensions:
        # Handle Garmin TrackPointExtension
        if hasattr(ext, "tag") and len(list(ext)) > 0:
            for child in ext:
                if hasattr(child, "tag") and hasattr(child, "text"):
                    tag_name = (
                        child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    )
                    if "hr" in tag_name.lower() and child.text:
                        try:
                            return float(child.text.strip())
                        except ValueError:
                            continue

        # Handle direct heart rate elements
        if hasattr(ext, "tag") and hasattr(ext, "text"):
            tag_name = ext.tag.split("}")[-1] if "}" in ext.tag else ext.tag
            if "hr" in tag_name.lower() and ext.text:
                try:
                    return float(ext.text.strip())
                except ValueError:
                    continue

    return None
