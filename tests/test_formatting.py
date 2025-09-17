import pytest
from datetime import datetime
from zoneinfo import ZoneInfo
from gpx_tools.formatting import (
    meters_to_feet,
    meters_to_miles,
    mps_to_mph,
    convert_to_la_timezone,
    format_distance,
    format_time,
    format_speed,
    format_elevation,
    format_datetime,
    format_heart_rate,
    format_activity_type,
)


class TestUnitConversions:
    def test_meters_to_feet(self):
        assert meters_to_feet(1.0) == pytest.approx(3.28084)
        assert meters_to_feet(100.0) == pytest.approx(328.084)

    def test_meters_to_miles(self):
        assert meters_to_miles(1609.344) == pytest.approx(1.0, rel=1e-4)
        assert meters_to_miles(1000.0) == pytest.approx(0.621371)

    def test_mps_to_mph(self):
        assert mps_to_mph(1.0) == pytest.approx(2.23694)
        assert mps_to_mph(44.704) == pytest.approx(100.0, rel=1e-3)


class TestTimezoneConversion:
    def test_convert_naive_utc_to_la(self):
        naive_dt = datetime(2024, 1, 15, 18, 0, 0)  # 6 PM UTC
        la_dt = convert_to_la_timezone(naive_dt)
        assert la_dt is not None
        assert la_dt.hour == 10  # 10 AM PST (UTC-8)

    def test_convert_aware_utc_to_la(self):
        utc_dt = datetime(2024, 1, 15, 18, 0, 0, tzinfo=ZoneInfo("UTC"))
        la_dt = convert_to_la_timezone(utc_dt)
        assert la_dt is not None
        assert la_dt.hour == 10  # 10 AM PST

    def test_convert_none_returns_none(self):
        assert convert_to_la_timezone(None) is None


class TestFormatting:
    def test_format_distance_miles(self):
        result = format_distance(2000.0)  # > 1 mile
        assert "mi" in result and result.endswith(" mi")

    def test_format_distance_feet(self):
        result = format_distance(100.0)  # < 1 mile
        assert result == "328 ft"

    def test_format_time_with_hours(self):
        result = format_time(3661)  # 1:01:01
        assert result == "1:01:01"

    def test_format_time_without_hours(self):
        result = format_time(125)  # 2:05
        assert result == "2:05"

    def test_format_speed(self):
        result = format_speed(44.704)  # ~100 mph
        assert result == "100.0 mph"

    def test_format_elevation(self):
        result = format_elevation(100.0)
        assert result == "328 ft"

    def test_format_datetime(self):
        dt = datetime(2024, 1, 15, 18, 0, 0, tzinfo=ZoneInfo("UTC"))
        result = format_datetime(dt)
        assert result is not None
        assert "2024-01-15 10:00:00 AM PST" in result

    def test_format_datetime_none(self):
        assert format_datetime(None) is None

    def test_format_heart_rate(self):
        assert format_heart_rate(150.7) == "151 bpm"

    def test_format_activity_type(self):
        assert format_activity_type("cycling") == "Cycling"
        assert format_activity_type("trail_running") == "Trail Running"
        assert format_activity_type("") == "Unknown"
        assert format_activity_type(None) == "Unknown"
