"""Contribution streak SVG card."""

from app.stats.models import UserStats

from .components import (
    block_meter,
    card_frame,
    cursor_blink,
    fmt,
    font,
    footer_comment,
    svg_open,
    terminal_chrome,
    updated_label,
)
from .theme import COLORS

WIDTH = 480
HEIGHT = 200
CHROME_H = 40
SEGMENTS = 20


def generate_streak_card(stats: UserStats) -> str:
    """Generate a contribution streak SVG card.

    The streak bar is a segmented block meter (current / longest),
    not a smooth progress bar — reads like a terminal load indicator
    rather than a generic dashboard widget.
    """
    current_streak, longest_streak = stats.current_streak, stats.longest_streak
    filled = (current_streak / longest_streak) * SEGMENTS if longest_streak > 0 else 0

    parts: list[str] = [svg_open(WIDTH, HEIGHT)]
    parts += card_frame(WIDTH, HEIGHT)
    parts += terminal_chrome(WIDTH, f"guest@github:~$ streak --user {stats.username}", CHROME_H)

    big_y = CHROME_H + 48
    parts.append(
        f'<text x="24" y="{big_y}" {font(30, 700)} fill="{COLORS["accent"]}">{fmt(current_streak)}</text>'
    )
    parts.append(
        f'<text x="24" y="{big_y + 18}" {font(11)} fill="{COLORS["dim"]}">days \u00b7 current streak</text>'
    )
    parts.append(
        f'<text x="{WIDTH - 24}" y="{big_y}" text-anchor="end" {font(20, 600)} '
        f'fill="{COLORS["text"]}">best {fmt(longest_streak)}d</text>'
    )

    meter_y = big_y + 36
    parts += block_meter(24, meter_y, SEGMENTS, filled, color=COLORS["accent"])

    contrib_y = meter_y + 32
    parts.append(
        f'<text x="24" y="{contrib_y}" {font(12)} fill="{COLORS["dim"]}">'
        f'total contributions: <tspan fill="{COLORS["text"]}" font-weight="600">{fmt(stats.contribution_count)}</tspan></text>'
    )

    footer_y = HEIGHT - 16
    parts.append(footer_comment(WIDTH / 2, footer_y, updated_label(stats.fetched_at)))
    parts.append(cursor_blink(WIDTH - 32, footer_y))

    parts.append("</svg>")
    return "\n".join(parts)
