from datetime import datetime, timezone

from app.utils.datetime_utils import format_input_time, format_system_wib


def test_format_system_wib_converts_utc_to_wib():
    dt = datetime(2026, 7, 8, 3, 17, tzinfo=timezone.utc)
    assert format_system_wib(dt) == "08 Jul 2026 10:17 WIB"


def test_format_system_wib_treats_naive_as_utc():
    dt = datetime(2026, 7, 8, 3, 17)
    assert format_system_wib(dt) == "08 Jul 2026 10:17 WIB"


def test_format_input_time_preserves_local_input():
    dt = datetime(2026, 7, 8, 10, 17)
    assert format_input_time(dt) == "08 Jul 2026 10:17 WIB"


def test_format_input_time_converts_aware_timezone():
    dt = datetime(2026, 7, 8, 3, 17, tzinfo=timezone.utc)
    assert format_input_time(dt) == "08 Jul 2026 10:17 WIB"
