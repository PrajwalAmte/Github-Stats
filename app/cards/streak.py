"""Contribution streak SVG card generator."""

from datetime import datetime


def generate_streak_card(
    username: str,
    current_streak: int,
    longest_streak: int,
    total_contributions: int,
    last_sync: datetime | None = None,
) -> str:
    """
    Generate a contribution streak SVG card.

    Args:
        username: GitHub username
        current_streak: Current contribution streak in days
        longest_streak: Longest contribution streak in days
        total_contributions: Total contribution count
        last_sync: Last synchronization timestamp

    Returns:
        SVG markup as string
    """

    def format_num(n: int) -> str:
        return f"{n:,}"

    last_updated = last_sync.strftime("%Y-%m-%d %H:%M UTC") if last_sync else ""

    # Calculate progress bar width (0-100%)
    progress = min(100, (current_streak / longest_streak) * 100) if longest_streak > 0 else 0

    svg = f"""
<svg width="500" height="200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      .card {{ fill: #0d1117; }}
      .border {{ fill: none; stroke: #30363d; stroke-width: 1; }}
      .title {{ fill: #c9d1d9; font-size: 18px; font-weight: 600; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif; }}
      .label {{ fill: #8b949e; font-size: 14px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif; }}
      .value {{ fill: #c9d1d9; font-size: 24px; font-weight: 700; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif; }}
      .footer {{ fill: #6e7681; font-size: 11px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif; }}
      .progress-bg {{ fill: #21262d; }}
      .progress-bar {{ fill: #58a6ff; }}
    </style>
  </defs>

  <rect class="card" width="500" height="200" rx="6"/>
  <rect class="border" width="498" height="198" x="1" y="1" rx="6"/>

  <text class="title" x="250" y="35" text-anchor="middle">{username}'s Contribution Streak</text>

  <!-- Current Streak -->
  <text class="label" x="120" y="75" text-anchor="middle">Current Streak</text>
  <text class="value" x="120" y="105" text-anchor="middle">{format_num(current_streak)}</text>
  <text class="label" x="120" y="125" text-anchor="middle">days</text>

  <!-- Longest Streak -->
  <text class="label" x="380" y="75" text-anchor="middle">Longest Streak</text>
  <text class="value" x="380" y="105" text-anchor="middle">{format_num(longest_streak)}</text>
  <text class="label" x="380" y="125" text-anchor="middle">days</text>

  <!-- Progress Bar -->
  <rect class="progress-bg" x="50" y="145" width="400" height="8" rx="4"/>
  <rect class="progress-bar" x="50" y="145" width="{progress * 4}" height="8" rx="4"/>

  <!-- Total Contributions -->
  <text class="label" x="250" y="170" text-anchor="middle">Total Contributions: {format_num(total_contributions)}</text>

  <!-- Footer -->
  <text class="footer" x="250" y="190" text-anchor="middle">Last updated: {last_updated}</text>
</svg>
"""
    return svg.strip()
