# Small helpers to convert race times into decimal minutes.
# All Hyrox times in this project are stored as decimal minutes,
# e.g. 3 minutes 45 seconds is stored as 3.75.

SECONDS_PER_MINUTE = 60
MINUTES_PER_HOUR = 60


def convert_time_to_minutes(time_text: str) -> float:
    """Convert a time like "03:45" (MM:SS) or "1:02:30" (HH:MM:SS) to minutes.

    Examples:
        "03:45"   -> 3.75
        "1:02:30" -> 62.5
    """
    parts = [int(part) for part in time_text.strip().split(":")]

    if len(parts) == 2:
        hours = 0
        minutes, seconds = parts
    elif len(parts) == 3:
        hours, minutes, seconds = parts
    else:
        raise ValueError(f"Time must look like MM:SS or HH:MM:SS, got '{time_text}'")

    return hours * MINUTES_PER_HOUR + minutes + seconds / SECONDS_PER_MINUTE


def convert_seconds_to_minutes(seconds: float) -> float:
    """Convert a number of seconds to minutes, e.g. 225 -> 3.75."""
    return seconds / SECONDS_PER_MINUTE
