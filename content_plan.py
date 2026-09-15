"""Vexora Tales / Sameena publishing schedule."""
from datetime import date

SHORT_DURATIONS = (40, 60)
LONG_SUNDAY_DURATIONS = (10, 13, 15)
# First Sunday of the rollout. Future Sundays progress 10 -> 13 -> 15 min.
ROLLOUT_FIRST_SUNDAY = date(2026, 9, 6)


def short_duration(day: date) -> int:
    return SHORT_DURATIONS[day.toordinal() % len(SHORT_DURATIONS)]


def sunday_long_duration(day: date) -> int:
    weeks = max(0, (day - ROLLOUT_FIRST_SUNDAY).days // 7)
    return LONG_SUNDAY_DURATIONS[min(weeks, len(LONG_SUNDAY_DURATIONS) - 1)]


def schedule_for_day(day: date):
    if day.weekday() == 6:
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
