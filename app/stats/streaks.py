"""Streak calculation logic - pure functions for contribution streaks."""

from datetime import date, timedelta


def calculate_streaks(contributions: list[tuple[date, int]]) -> tuple[int, int]:
    """
    Calculate current and longest contribution streaks.

    Args:
        contributions: List of (date, count) tuples, assumed to be sorted by date

    Returns:
        Tuple of (current_streak, longest_streak)
    """
    if not contributions:
        return 0, 0

    # Filter to only days with contributions > 0
    active_days = [d for d, count in contributions if count > 0]

    if not active_days:
        return 0, 0

    # Calculate longest streak
    longest = 1
    current_length = 1

    for i in range(1, len(active_days)):
        expected_date = active_days[i - 1] + timedelta(days=1)
        if active_days[i] == expected_date:
            current_length += 1
            longest = max(longest, current_length)
        else:
            current_length = 1

    # Calculate current streak (must end at today or yesterday)
    today = date.today()
    yesterday = today - timedelta(days=1)

    current_streak = 0
    last_active = active_days[-1]

    # Current streak only counts if it ends today or yesterday
    if last_active in (today, yesterday):
        current_streak = 1
        # Count backwards
        for i in range(len(active_days) - 2, -1, -1):
            expected_date = active_days[i + 1] - timedelta(days=1)
            if active_days[i] == expected_date:
                current_streak += 1
            else:
                break

    return current_streak, longest


def calculate_contribution_total(contributions: list[tuple[date, int]]) -> int:
    """Calculate total contribution count from (date, count) tuples."""
    return sum(count for _, count in contributions)
