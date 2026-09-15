"""Vexora Tales publishing/content schedule.

The schedule is intentionally separate from upload logic: generation may happen
automatically, but public publishing still requires explicit approval.
"""
from datetime import date


SHORT_DURATIONS = (40, 60)
LONG_SUNDAY_DURATIONS = (10, 13, 15)


def short_duration(day: date) -> int:
    """Pick 40 or 60 seconds deterministically, without stretching the script."""
    return SHORT_DURATIONS[day.toordinal() % len(SHORT_DURATIONS)]


def sunday_long_duration(day: date) -> int:
    """Return the planned Sunday duration: 10, then 13, then 15 minutes."""
    # ISO week gives a stable weekly progression. After 15 minutes, stay at 15.
    week_index = day.isocalendar().week
    return LONG_SUNDAY_DURATIONS[min(week_index - 1, len(LONG_SUNDAY_DURATIONS) - 1)]


def schedule_for_day(day: date):
    """Return the user's requested daily publishing plan."""
    if day.weekday() == 6:  # Sunday
        minutes = sunday_long_duration(day)
        return {
            "day": day.isoformat(),
            "content_type": "long",
            "target_duration_seconds": minutes * 60,
            "target_duration_label": f"{minutes} minutes",
        }
    seconds = short_duration(day)
    return {
        "day": day.isoformat(),
        "content_type": "short",
        "target_duration_seconds": seconds,
        "target_duration_label": f"{seconds} seconds",
    }
