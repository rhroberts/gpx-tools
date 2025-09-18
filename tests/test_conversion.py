import pytest
from datetime import datetime
from zoneinfo import ZoneInfo
from gpx_tools.conversion import (
    meters_to_feet,
    meters_to_miles,
    mps_to_mph,
    convert_to_la_timezone,
)


class TestUnitConversions:
    def test_meters_to_feet(self) -> None:
        assert meters_to_feet(1.0) == pytest.approx(3.28084)  # type: ignore[arg-type]
        assert meters_to_feet(100.0) == pytest.approx(328.084)  # type: ignore[arg-type]

    def test_meters_to_miles(self) -> None:
        assert meters_to_miles(1609.344) == pytest.approx(1.0, rel=1e-4)  # type: ignore[arg-type]
        assert meters_to_miles(1000.0) == pytest.approx(0.621371)  # type: ignore[arg-type]

    def test_mps_to_mph(self) -> None:
        assert mps_to_mph(1.0) == pytest.approx(2.23694)  # type: ignore[arg-type]
        assert mps_to_mph(44.704) == pytest.approx(100.0, rel=1e-3)  # type: ignore[arg-type]


class TestTimezoneConversion:
    def test_convert_naive_utc_to_la(self) -> None:
        naive_dt = datetime(2024, 1, 15, 18, 0, 0)  # 6 PM UTC
        la_dt = convert_to_la_timezone(naive_dt)
        assert la_dt is not None
        assert la_dt.hour == 10  # 10 AM PST (UTC-8)

    def test_convert_aware_utc_to_la(self) -> None:
        utc_dt = datetime(2024, 1, 15, 18, 0, 0, tzinfo=ZoneInfo("UTC"))
        la_dt = convert_to_la_timezone(utc_dt)
        assert la_dt is not None
        assert la_dt.hour == 10  # 10 AM PST

    def test_convert_none_returns_none(self) -> None:
        assert convert_to_la_timezone(None) is None
