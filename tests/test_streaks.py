"""Tests for streak calculation."""

from datetime import date, timedelta

from app.stats.streaks import calculate_contribution_total, calculate_streaks


def test_empty_contributions():
    """Test streak calculation with no contributions."""
    current, longest = calculate_streaks([])
    assert current == 0
    assert longest == 0


def test_all_zero_contributions():
    """Test streak calculation with all zero contributions."""
    contributions = [
        (date(2026, 1, 1), 0),
        (date(2026, 1, 2), 0),
        (date(2026, 1, 3), 0),
    ]
    current, longest = calculate_streaks(contributions)
    assert current == 0
    assert longest == 0


def test_single_day_today():
    """Test streak with single contribution today."""
    today = date.today()
    contributions = [(today, 5)]
    current, longest = calculate_streaks(contributions)
    assert current == 1
    assert longest == 1


def test_single_day_yesterday():
    """Test streak with single contribution yesterday."""
    yesterday = date.today() - timedelta(days=1)
    contributions = [(yesterday, 3)]
    current, longest = calculate_streaks(contributions)
    assert current == 1
    assert longest == 1


def test_single_day_old():
    """Test streak with single contribution in the past."""
    old_date = date.today() - timedelta(days=10)
    contributions = [(old_date, 2)]
    current, longest = calculate_streaks(contributions)
    assert current == 0  # Not current since it's not recent
    assert longest == 1


def test_consecutive_days_ending_today():
    """Test consecutive days ending today."""
    today = date.today()
    contributions = [
        (today - timedelta(days=2), 1),
        (today - timedelta(days=1), 2),
        (today, 3),
    ]
    current, longest = calculate_streaks(contributions)
    assert current == 3
    assert longest == 3


def test_consecutive_days_ending_yesterday():
    """Test consecutive days ending yesterday."""
    yesterday = date.today() - timedelta(days=1)
    contributions = [
        (yesterday - timedelta(days=2), 1),
        (yesterday - timedelta(days=1), 2),
        (yesterday, 3),
    ]
    current, longest = calculate_streaks(contributions)
    assert current == 3
    assert longest == 3


def test_gap_in_contributions():
    """Test contributions with gap."""
    today = date.today()
    contributions = [
        (today - timedelta(days=5), 1),
        (today - timedelta(days=4), 2),
        # Gap here
        (today - timedelta(days=1), 3),
        (today, 4),
    ]
    current, longest = calculate_streaks(contributions)
    assert current == 2
    assert longest == 2


def test_longest_streak_in_past():
    """Test when longest streak is in the past."""
    today = date.today()
    contributions = [
        # Old long streak
        (today - timedelta(days=20), 1),
        (today - timedelta(days=19), 1),
        (today - timedelta(days=18), 1),
        (today - timedelta(days=17), 1),
        (today - timedelta(days=16), 1),
        # Gap
        # Current short streak
        (today - timedelta(days=1), 2),
        (today, 3),
    ]
    current, longest = calculate_streaks(contributions)
    assert current == 2
    assert longest == 5


def test_contribution_total():
    """Test contribution total calculation."""
    contributions = [
        (date(2026, 1, 1), 5),
        (date(2026, 1, 2), 10),
        (date(2026, 1, 3), 3),
    ]
    total = calculate_contribution_total(contributions)
    assert total == 18


def test_contribution_total_empty():
    """Test contribution total with no data."""
    total = calculate_contribution_total([])
    assert total == 0
