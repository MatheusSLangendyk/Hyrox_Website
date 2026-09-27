import pytest
from utils.time_conversion import convert_time_to_minutes, convert_seconds_to_minutes


@pytest.mark.parametrize("time_text, expected_minutes", [
    ("03:45", 3.75),
    ("3:45", 3.75),
    ("00:30", 0.5),
    ("1:02:30", 62.5),
    (" 10:00 ", 10.0),
])
def test_convert_time_to_minutes(time_text, expected_minutes):
    assert convert_time_to_minutes(time_text) == pytest.approx(expected_minutes)


@pytest.mark.parametrize("bad_time", ["345", "1:2:3:4", "ab:cd", ""])
def test_convert_time_to_minutes_rejects_bad_input(bad_time):
    with pytest.raises(ValueError):
        convert_time_to_minutes(bad_time)


def test_convert_seconds_to_minutes():
    assert convert_seconds_to_minutes(225) == pytest.approx(3.75)
