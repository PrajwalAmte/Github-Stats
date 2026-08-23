"""Profile statistics SVG card."""

from datetime import datetime

from .components import (
    card_frame,
    cursor_blink,
    footer_comment,
    kv_row,
    terminal_chrome,
)

WIDTH = 480
HEIGHT = 300
CHROME_H = 40
COL1_X, COL1_END = 24, 224
COL2_X, COL2_END = 248, 456


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
    """Generate a profile statistics SVG card.

    Args mirror the underlying `users` aggregate row directly — no
    derived formatting happens outside this function.
    """

    def fmt(n: int) -> str:
        return f"{n:,}"

    last_updated = last_sync.strftime("%Y-%m-%d %H:%M UTC") if last_sync else "never"

    rows_left = [
        ("commits --total", fmt(total_commits)),
        ("pull-requests --total", fmt(total_prs)),
        ("issues --total", fmt(total_issues)),
        ("reviews --total", fmt(total_reviews)),
    ]
    rows_right = [
        ("stars --sum", fmt(star_count)),
        ("repos --count", fmt(repo_count)),
        ("streak --current", f"{current_streak}d"),
        ("streak --longest", f"{longest_streak}d"),
    ]

    parts: list[str] = [
        f'<svg width="{WIDTH}" height="{HEIGHT}" xmlns="http://www.w3.org/2000/svg">'
    ]
    parts += card_frame(WIDTH, HEIGHT)
    parts += terminal_chrome(WIDTH, f"guest@github:~$ stats --user {username}", CHROME_H)

    row_y0, row_gap = CHROME_H + 40, 42
    for i, (label, value) in enumerate(rows_left):
        parts += kv_row(COL1_X, COL1_END, row_y0 + i * row_gap, label, value)
    for i, (label, value) in enumerate(rows_right):
        parts += kv_row(COL2_X, COL2_END, row_y0 + i * row_gap, label, value)

    footer_y = HEIGHT - 20
    parts.append(footer_comment(WIDTH / 2, footer_y, f"# synced {last_updated} \u00b7 v1"))
    parts.append(cursor_blink(COL1_X + 4, footer_y))

    parts.append("</svg>")
    return "\n".join(parts)
