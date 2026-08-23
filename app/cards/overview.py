"""Consolidated wide SVG card for single-row README usage."""

from datetime import datetime

from .components import (
    block_meter,
    card_frame,
    cursor_blink,
    esc,
    font,
    footer_comment,
    kv_row,
    terminal_chrome,
)
from .theme import COLORS, LANGUAGE_COLORS

WIDTH = 1100
HEIGHT = 260
CHROME_H = 40


def generate_overview_card(
    username: str,
    total_commits: int,
    total_prs: int,
    total_issues: int,
    total_reviews: int,
    star_count: int,
    repo_count: int,
    current_streak: int,
    longest_streak: int,
    total_contributions: int,
    languages: list[tuple[str, float]],
    last_sync: datetime | None = None,
) -> str:
    """Generate a single consolidated card that spans most README width."""

    def fmt(n: int) -> str:
        return f"{n:,}"

    last_updated = last_sync.strftime("%Y-%m-%d %H:%M UTC") if last_sync else "never"
    top_languages = languages[:4]

    parts: list[str] = [
        (
            f'<svg width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" '
            'xmlns="http://www.w3.org/2000/svg">'
        )
    ]
    parts += card_frame(WIDTH, HEIGHT)
    parts += terminal_chrome(WIDTH, f"guest@github:~$ overview --user {username}", CHROME_H)

    content_top = CHROME_H + 26
    divider_left_x = 430
    divider_right_x = 748
    left_x, left_end = 24, divider_left_x - 20
    center_x0 = divider_left_x + 18
    right_x0 = divider_right_x + 20

    parts.append(
        f'<line x1="{divider_left_x}" y1="{CHROME_H + 14}" x2="{divider_left_x}" y2="{HEIGHT - 34}" '
        f'stroke="{COLORS["border"]}"/>'
    )
    parts.append(
        f'<line x1="{divider_right_x}" y1="{CHROME_H + 14}" x2="{divider_right_x}" y2="{HEIGHT - 34}" '
        f'stroke="{COLORS["border"]}"/>'
    )

    left_rows = [
        ("commits --total", fmt(total_commits)),
        ("pull-requests --total", fmt(total_prs)),
        ("issues --total", fmt(total_issues)),
        ("reviews --total", fmt(total_reviews)),
        ("stars --sum", fmt(star_count)),
        ("repos --count", fmt(repo_count)),
    ]
    for i, (label, value) in enumerate(left_rows):
        parts += kv_row(left_x, left_end, content_top + i * 24, label, value)

    streak_ratio = (current_streak / longest_streak) * 16 if longest_streak > 0 else 0
    parts.append(
        f'<text x="{center_x0}" y="{content_top}" {font(11)} fill="{COLORS["dim"]}"># streak</text>'
    )
    parts.append(
        f'<text x="{center_x0}" y="{content_top + 36}" {font(34, 700)} '
        f'fill="{COLORS["accent"]}">{fmt(current_streak)}d</text>'
    )
    parts.append(
        f'<text x="{center_x0}" y="{content_top + 56}" {font(11)} fill="{COLORS["dim"]}">current</text>'
    )
    parts.append(
        f'<text x="{divider_right_x - 24}" y="{content_top + 36}" text-anchor="end" {font(24, 600)} '
        f'fill="{COLORS["text"]}">best {fmt(longest_streak)}d</text>'
    )
    parts += block_meter(center_x0, content_top + 72, 16, streak_ratio, seg_w=12, gap=5, seg_h=10)
    parts.append(
        f'<text x="{center_x0}" y="{content_top + 108}" {font(12)} fill="{COLORS["dim"]}">'
        f'total contributions: <tspan fill="{COLORS["text"]}" font-weight="600">'
        f'{fmt(total_contributions)}</tspan></text>'
    )

    parts.append(
        f'<text x="{right_x0}" y="{content_top}" {font(11)} fill="{COLORS["dim"]}"># top languages</text>'
    )
    if not top_languages:
        parts.append(
            f'<text x="{right_x0}" y="{content_top + 26}" {font(12)} fill="{COLORS["dim"]}">'
            "no language data yet</text>"
        )
    else:
        row_h = 28
        for i, (lang_name, percentage) in enumerate(top_languages):
            y = content_top + 24 + i * row_h
            color = LANGUAGE_COLORS.get(lang_name, COLORS["accent_blue"])
            parts.append(f'<circle cx="{right_x0 + 5}" cy="{y - 4}" r="4" fill="{color}"/>')
            parts.append(
                f'<text x="{right_x0 + 16}" y="{y}" {font(12)} fill="{COLORS["text"]}">'
                f"{esc(lang_name)}</text>"
            )
            parts += block_meter(
                right_x0 + 116,
                y - 11,
                12,
                (percentage / 100) * 12,
                seg_w=9,
                gap=3,
                seg_h=9,
                color=color,
            )
            parts.append(
                f'<text x="{WIDTH - 20}" y="{y}" text-anchor="end" {font(12, 600)} '
                f'fill="{COLORS["text"]}">{percentage:.1f}%</text>'
            )

    footer_y = HEIGHT - 16
    parts.append(footer_comment(WIDTH / 2, footer_y, f"# synced {last_updated} · v1"))
    parts.append(cursor_blink(30, footer_y))

    parts.append("</svg>")
    return "\n".join(parts)
