from datetime import date, timedelta

from content_plan import schedule_for_day, sunday_long_duration


def test_sunday_rollout_progression():
    first = date(2026, 9, 6)
    assert sunday_long_duration(first) == 10
    assert sunday_long_duration(first + timedelta(days=7)) == 13
    assert sunday_long_duration(first + timedelta(days=14)) == 15
    assert sunday_long_duration(first + timedelta(days=21)) == 15


def test_weekday_is_short():
    plan = schedule_for_day(date(2026, 9, 14))  # Monday
    assert plan["content_type"] == "short"
    assert plan["target_duration_seconds"] in (40, 60)


def test_sunday_is_long():
    plan = schedule_for_day(date(2026, 9, 13))
    assert plan["content_type"] == "long"
    assert plan["target_duration_seconds"] == 13 * 60
