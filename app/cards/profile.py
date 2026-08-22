"""Profile statistics SVG card generator."""

from datetime import datetime


def generate_profile_card(
    username: str,
    total_commits: int,
    total_prs: int,
    total_issues: int,
    total_reviews: int,
    star_count: int,
    repo_count: int,
    current_streak: int,
    longest_streak: int,
    last_sync: datetime | None = None,
) -> str:
    """
    Generate a profile statistics SVG card.

    Args:
        username: GitHub username
        total_commits: Total commit contributions
        total_prs: Total pull requests
        total_issues: Total issues
        total_reviews: Total reviews
        star_count: Total stars across repositories
        repo_count: Number of repositories
        current_streak: Current contribution streak
        longest_streak: Longest contribution streak
        last_sync: Last synchronization timestamp

    Returns:
        SVG markup as string
    """

    # Format large numbers with commas
    def format_num(n: int) -> str:
        return f"{n:,}"

    last_updated = last_sync.strftime("%Y-%m-%d %H:%M UTC") if last_sync else ""

    svg = f"""
<svg width="500" height="300" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      .card {{ fill: #0d1117; }}
      .border {{ fill: none; stroke: #30363d; stroke-width: 1; }}
      .title {{ fill: #c9d1d9; font-size: 18px; font-weight: 600; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif; }}
      .label {{ fill: #8b949e; font-size: 14px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif; }}
      .value {{ fill: #c9d1d9; font-size: 16px; font-weight: 600; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif; }}
      .footer {{ fill: #6e7681; font-size: 11px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif; }}
    </style>
  </defs>

  <rect class="card" width="500" height="300" rx="6"/>
  <rect class="border" width="498" height="298" x="1" y="1" rx="6"/>

  <text class="title" x="20" y="35">{username}'s GitHub Stats</text>

  <!-- Left Column -->
  <text class="label" x="20" y="70">Total Commits</text>
  <text class="value" x="20" y="90">{format_num(total_commits)}</text>

  <text class="label" x="20" y="125">Total Pull Requests</text>
  <text class="value" x="20" y="145">{format_num(total_prs)}</text>

  <text class="label" x="20" y="180">Total Issues</text>
  <text class="value" x="20" y="200">{format_num(total_issues)}</text>

  <text class="label" x="20" y="235">Total Reviews</text>
  <text class="value" x="20" y="255">{format_num(total_reviews)}</text>

  <!-- Right Column -->
  <text class="label" x="260" y="70">Total Stars</text>
  <text class="value" x="260" y="90">{format_num(star_count)}</text>

  <text class="label" x="260" y="125">Repositories</text>
  <text class="value" x="260" y="145">{format_num(repo_count)}</text>

  <text class="label" x="260" y="180">Current Streak</text>
  <text class="value" x="260" y="200">{format_num(current_streak)} days</text>

  <text class="label" x="260" y="235">Longest Streak</text>
  <text class="value" x="260" y="255">{format_num(longest_streak)} days</text>

  <!-- Footer -->
  <text class="footer" x="250" y="290" text-anchor="middle">Last updated: {last_updated}</text>
</svg>
"""
    return svg.strip()
