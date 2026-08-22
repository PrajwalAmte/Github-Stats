"""Languages SVG card generator."""

from datetime import datetime


def generate_languages_card(
    username: str,
    languages: list[tuple[str, float]],
    last_sync: datetime | None = None,
) -> str:
    """
    Generate a top languages SVG card.

    Args:
        username: GitHub username
        languages: List of (language_name, percentage) tuples, top 6
        last_sync: Last synchronization timestamp

    Returns:
        SVG markup as string
    """
    # Language color mapping (GitHub's default colors)
    language_colors = {
        "Python": "#3572A5",
        "JavaScript": "#f1e05a",
        "TypeScript": "#2b7489",
        "Java": "#b07219",
        "C++": "#f34b7d",
        "C": "#555555",
        "C#": "#178600",
        "Go": "#00ADD8",
        "Rust": "#dea584",
        "Ruby": "#701516",
        "PHP": "#4F5D95",
        "Swift": "#ffac45",
        "Kotlin": "#A97BFF",
        "Dart": "#00B4AB",
        "Shell": "#89e051",
        "HTML": "#e34c26",
        "CSS": "#563d7c",
        "Jupyter Notebook": "#DA5B0B",
        "R": "#198CE7",
        "Scala": "#c22d40",
        "Objective-C": "#438eff",
        "Perl": "#0298c3",
        "Lua": "#000080",
        "Haskell": "#5e5086",
        "Elixir": "#6e4a7e",
    }

    # Take top 6 languages
    top_languages = languages[:6]

    # Calculate bar positions
    bar_height = 24
    bar_spacing = 40
    start_y = 60
    max_bar_width = 440

    last_updated = last_sync.strftime("%Y-%m-%d %H:%M UTC") if last_sync else ""

    # Start building SVG
    svg_parts = [
        '<svg width="500" height="320" xmlns="http://www.w3.org/2000/svg">',
        '  <defs>',
        '    <style>',
        '      .card { fill: #0d1117; }',
        '      .border { fill: none; stroke: #30363d; stroke-width: 1; }',
        '      .title { fill: #c9d1d9; font-size: 18px; font-weight: 600; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', \'Noto Sans\', Helvetica, Arial, sans-serif; }',
        '      .lang-name { fill: #c9d1d9; font-size: 14px; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', \'Noto Sans\', Helvetica, Arial, sans-serif; }',
        '      .percentage { fill: #8b949e; font-size: 13px; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', \'Noto Sans\', Helvetica, Arial, sans-serif; }',
        '      .footer { fill: #6e7681; font-size: 11px; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', \'Noto Sans\', Helvetica, Arial, sans-serif; }',
        '      .bar-bg { fill: #21262d; }',
        '    </style>',
        '  </defs>',
        '',
        '  <rect class="card" width="500" height="320" rx="6"/>',
        '  <rect class="border" width="498" height="318" x="1" y="1" rx="6"/>',
        '',
        f'  <text class="title" x="250" y="35" text-anchor="middle">{username}\'s Most Used Languages</text>',
        '',
    ]

    # Add language bars
    for idx, (lang_name, percentage) in enumerate(top_languages):
        y_position = start_y + (idx * bar_spacing)
        bar_width = (percentage / 100) * max_bar_width

        # Get color for language (default to gray if not found)
        color = language_colors.get(lang_name, "#858585")

        # Background bar
        svg_parts.append(f'  <!-- {lang_name} -->')
        svg_parts.append(f'  <rect class="bar-bg" x="30" y="{y_position}" width="{max_bar_width}" height="{bar_height}" rx="4"/>')

        # Filled bar
        svg_parts.append(f'  <rect fill="{color}" x="30" y="{y_position}" width="{bar_width}" height="{bar_height}" rx="4"/>')

        # Language name
        svg_parts.append(f'  <text class="lang-name" x="30" y="{y_position - 6}">{lang_name}</text>')

        # Percentage
        svg_parts.append(f'  <text class="percentage" x="{30 + max_bar_width}" y="{y_position - 6}" text-anchor="end">{percentage:.1f}%</text>')
        svg_parts.append('')

    # Footer
    footer_y = start_y + (len(top_languages) * bar_spacing) + 20
    svg_parts.append(f'  <text class="footer" x="250" y="{footer_y}" text-anchor="middle">Last updated: {last_updated}</text>')
    svg_parts.append('</svg>')

    return '\n'.join(svg_parts)
