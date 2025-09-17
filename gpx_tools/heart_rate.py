from pathlib import Path
from typing import Any, List, Optional
import gpxpy
import gpxpy.gpx


def strip_heart_rate_data(input_file: Path, output_file: Path) -> None:
    """Strip heart rate data from a GPX file and save to output file."""
    with open(input_file, "r") as gpx_file:
        gpx = gpxpy.parse(gpx_file)

    # Remove heart rate data from all track points
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                if point.extensions:
                    # Clean extensions by removing heart rate data
                    point.extensions = _clean_extensions(point.extensions)

    # Write the modified GPX to output file
    with open(output_file, "w") as f:
        f.write(gpx.to_xml())


def _clean_extensions(extensions: List[Any]) -> List[Any]:
    """Remove heart rate data from extensions while preserving other data."""
    import xml.etree.ElementTree as ET

    cleaned_extensions = []

    for extension in extensions:
        if hasattr(extension, "tag") and len(list(extension)) > 0:
            # This is a container extension (like TrackPointExtension)
            # Create a new extension without heart rate children
            new_extension = ET.Element(extension.tag, extension.attrib)
            new_extension.text = extension.text
            new_extension.tail = extension.tail

            # Copy all children except heart rate elements
            for child in extension:
                if hasattr(child, "tag"):
                    tag_name = (
                        child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    )
                    tag_lower = tag_name.lower()

                    # Skip heart rate elements
                    if not any(
                        indicator in tag_lower
                        for indicator in ["hr", "heartrate", "bpm"]
                    ):
                        new_child = ET.Element(child.tag, child.attrib)
                        new_child.text = child.text
                        new_child.tail = child.tail
                        # Copy any grandchildren
                        for grandchild in child:
                            new_child.append(grandchild)
                        new_extension.append(new_child)

            # Only keep extension if it still has children or content
            if len(new_extension) > 0 or new_extension.text:
                cleaned_extensions.append(new_extension)

        elif not _is_heart_rate_extension(extension):
            # This is a direct extension that's not heart rate related
            cleaned_extensions.append(extension)

    return cleaned_extensions


def extract_heart_rate_data(gpx: gpxpy.gpx.GPX) -> List[float]:
    """Extract all heart rate values from a GPX object."""
    heart_rates = []

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                if point.extensions:
                    for ext in point.extensions:
                        hr_value = _extract_heart_rate_from_extension(ext)
                        if hr_value is not None:
                            heart_rates.append(hr_value)

    return heart_rates


def calculate_average_heart_rate(gpx: gpxpy.gpx.GPX) -> Optional[float]:
    """Calculate average heart rate from GPX data."""
    heart_rates = extract_heart_rate_data(gpx)

    if not heart_rates:
        return None

    return sum(heart_rates) / len(heart_rates)


def calculate_max_heart_rate(gpx: gpxpy.gpx.GPX) -> Optional[float]:
    """Calculate maximum heart rate from GPX data."""
    heart_rates = extract_heart_rate_data(gpx)

    if not heart_rates:
        return None

    return max(heart_rates)


def _extract_heart_rate_from_extension(extension: Any) -> Optional[float]:
    """Extract heart rate value from an extension."""
    try:
        # Check if it's an XML element with children (like Garmin TrackPointExtension)
        if hasattr(extension, "tag") and len(list(extension)) > 0:
            # Look through child elements for heart rate
            for child in extension:
                if hasattr(child, "tag") and hasattr(child, "text"):
                    # Extract tag name without namespace
                    tag_name = (
                        child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    )
                    tag_lower = tag_name.lower()

                    if any(
                        indicator in tag_lower
                        for indicator in ["hr", "heartrate", "bpm"]
                    ):
                        if child.text and child.text.strip():
                            value = float(child.text.strip())
                            # Validate heart rate range
                            if 30 <= value <= 220:
                                return value

        # Check if it's a direct heart rate element
        if hasattr(extension, "tag") and hasattr(extension, "text"):
            # Extract tag name without namespace
            tag_name = (
                extension.tag.split("}")[-1] if "}" in extension.tag else extension.tag
            )
            tag_lower = tag_name.lower()

            if any(indicator in tag_lower for indicator in ["hr", "heartrate", "bpm"]):
                if extension.text and extension.text.strip():
                    value = float(extension.text.strip())
                    # Validate heart rate range
                    if 30 <= value <= 220:
                        return value

        # Check string representation for heart rate value
        ext_str = str(extension).lower()
        if any(indicator in ext_str for indicator in ["hr", "heartrate", "bpm"]):
            # Try to extract numeric value from string
            import re

            numbers = re.findall(r"\d+\.?\d*", ext_str)
            if numbers:
                # Take the first reasonable heart rate value (30-220 bpm)
                for num_str in numbers:
                    value = float(num_str)
                    if 30 <= value <= 220:
                        return value

    except (ValueError, AttributeError):
        pass

    return None


def _is_heart_rate_extension(extension: Any) -> bool:
    """Check if an extension contains heart rate data."""
    # Check if it's an XML element with children (like Garmin TrackPointExtension)
    if hasattr(extension, "tag") and len(list(extension)) > 0:
        # Look through child elements for heart rate
        for child in extension:
            if hasattr(child, "tag"):
                # Extract tag name without namespace
                tag_name = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                tag_lower = tag_name.lower()
                if any(
                    indicator in tag_lower for indicator in ["hr", "heartrate", "bpm"]
                ):
                    return True

    # Check if it's a direct heart rate element
    if hasattr(extension, "tag"):
        # Extract tag name without namespace
        tag_name = (
            extension.tag.split("}")[-1] if "}" in extension.tag else extension.tag
        )
        tag_lower = tag_name.lower()
        if any(indicator in tag_lower for indicator in ["hr", "heartrate", "bpm"]):
            return True

    # Check string representation for heart rate indicators
    ext_str = str(extension).lower()
    return any(indicator in ext_str for indicator in ["hr", "heartrate", "bpm"])
