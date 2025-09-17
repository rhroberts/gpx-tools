from pathlib import Path
from typing import Any, List
import random
import gpxpy
from .constants import (
    HEART_RATE_INDICATORS,
    MIN_HEART_RATE,
    MAX_HEART_RATE,
    RANDOM_SEED,
    DEFAULT_HR_VARIATION,
)


def strip_heart_rate_data(input_file: Path, output_file: Path) -> None:
    """Strip heart rate data from a GPX file and save to output file."""
    with open(input_file, "r") as gpx_file:
        gpx = gpxpy.parse(gpx_file)

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                if point.extensions:
                    point.extensions = _clean_extensions(point.extensions)

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
                        indicator in tag_lower for indicator in HEART_RATE_INDICATORS
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


def replace_heart_rate_data(
    input_file: Path,
    output_file: Path,
    avg_hr: int,
    variation: int = DEFAULT_HR_VARIATION,
) -> None:
    """Replace heart rate data with custom average and realistic variation."""
    with open(input_file, "r") as gpx_file:
        gpx = gpxpy.parse(gpx_file)

    random.seed(RANDOM_SEED)

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                if point.extensions:
                    point.extensions = _replace_hr_in_extensions(
                        point.extensions, avg_hr, variation
                    )
    with open(output_file, "w") as f:
        f.write(gpx.to_xml())


def _replace_hr_in_extensions(
    extensions: List[Any], avg_hr: int, variation: int
) -> List[Any]:
    """Replace heart rate data in extensions with custom values."""
    import xml.etree.ElementTree as ET

    modified_extensions = []

    for extension in extensions:
        if hasattr(extension, "tag") and len(list(extension)) > 0:
            # This is a container extension (like TrackPointExtension)
            new_extension = ET.Element(extension.tag, extension.attrib)
            new_extension.text = extension.text
            new_extension.tail = extension.tail

            # Copy all children, replacing heart rate elements
            for child in extension:
                if hasattr(child, "tag"):
                    tag_name = (
                        child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    )
                    tag_lower = tag_name.lower()

                    # Replace heart rate elements with custom value
                    if any(
                        indicator in tag_lower for indicator in HEART_RATE_INDICATORS
                    ):
                        new_child = ET.Element(child.tag, child.attrib)
                        hr_value = avg_hr + random.randint(-variation, variation)
                        hr_value = max(MIN_HEART_RATE, min(MAX_HEART_RATE, hr_value))
                        new_child.text = str(hr_value)
                        new_child.tail = child.tail
                        new_extension.append(new_child)
                    else:
                        # Copy non-HR elements unchanged
                        new_child = ET.Element(child.tag, child.attrib)
                        new_child.text = child.text
                        new_child.tail = child.tail
                        # Copy any grandchildren
                        for grandchild in child:
                            new_child.append(grandchild)
                        new_extension.append(new_child)

            modified_extensions.append(new_extension)

        elif _is_heart_rate_extension(extension):
            # This is a direct heart rate extension - replace it
            new_extension = ET.Element(extension.tag, extension.attrib)
            hr_value = avg_hr + random.randint(-variation, variation)
            hr_value = max(MIN_HEART_RATE, min(MAX_HEART_RATE, hr_value))
            new_extension.text = str(hr_value)
            new_extension.tail = extension.tail
            modified_extensions.append(new_extension)
        else:
            # This is a non-HR extension - keep unchanged
            modified_extensions.append(extension)

    return modified_extensions


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
                if any(indicator in tag_lower for indicator in HEART_RATE_INDICATORS):
                    return True

    # Check if it's a direct heart rate element
    if hasattr(extension, "tag"):
        # Extract tag name without namespace
        tag_name = (
            extension.tag.split("}")[-1] if "}" in extension.tag else extension.tag
        )
        tag_lower = tag_name.lower()
        if any(indicator in tag_lower for indicator in HEART_RATE_INDICATORS):
            return True

    # Check string representation for heart rate indicators
    ext_str = str(extension).lower()
    return any(indicator in ext_str for indicator in HEART_RATE_INDICATORS)
