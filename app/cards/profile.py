"""Profile statistics SVG card."""

from app.stats.models import UserStats

from .components import (
    card_frame,
    cursor_blink,
    fmt,
    footer_comment,
    kv_row,
    svg_open,
    terminal_chrome,
    updated_label,
)

WIDTH = 480
HEIGHT = 300
CHROME_H = 40
COL1_X, COL1_END = 24, 224
COL2_X, COL2_END = 248, 456


def generate_profile_card(stats: UserStats) -> str:
    """Generate a profile statistics SVG card."""

    rows_left = [
        ("commits --total", fmt(stats.total_commits)),
        ("pull-requests --total", fmt(stats.total_pull_requests)),
        ("issues --total", fmt(stats.total_issues)),
        ("reviews --total", fmt(stats.total_reviews)),
    ]
    rows_right = [
        ("stars --sum", fmt(stats.star_count)),
        ("repos --count", fmt(stats.repository_count)),
        ("streak --current", f"{stats.current_streak}d"),
        ("streak --longest", f"{stats.longest_streak}d"),
    ]

    parts: list[str] = [svg_open(WIDTH, HEIGHT)]
    parts += card_frame(WIDTH, HEIGHT)
    parts += terminal_chrome(WIDTH, f"guest@github:~$ stats --user {stats.username}", CHROME_H)

    row_y0, row_gap = CHROME_H + 40, 42
    for i, (label, value) in enumerate(rows_left):
        parts += kv_row(COL1_X, COL1_END, row_y0 + i * row_gap, label, value)
    for i, (label, value) in enumerate(rows_right):
        parts += kv_row(COL2_X, COL2_END, row_y0 + i * row_gap, label, value)

    footer_y = HEIGHT - 20
    parts.append(footer_comment(WIDTH / 2, footer_y, updated_label(stats.fetched_at)))
    parts.append(cursor_blink(COL1_X + 4, footer_y))

    parts.append("</svg>")
    return "\n".join(parts)
