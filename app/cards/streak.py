"""Contribution streak SVG card."""

from datetime import datetime

from .components import block_meter, card_frame, cursor_blink, font, footer_comment, terminal_chrome
from .theme import COLORS

WIDTH = 480
HEIGHT = 200
CHROME_H = 40
SEGMENTS = 20


def generate_streak_card(
    username: str,
    current_streak: int,
    longest_streak: int,
    total_contributions: int,
    last_sync: datetime | None = None,
) -> str:
    """Generate a contribution streak SVG card.

    The streak bar is a segmented block meter (current / longest),
    not a smooth progress bar — reads like a terminal load indicator
    rather than a generic dashboard widget.
    """
    fmt = lambda n: f"{n:,}"
    last_updated = last_sync.strftime("%Y-%m-%d %H:%M UTC") if last_sync else "never"
    filled = (current_streak / longest_streak) * SEGMENTS if longest_streak > 0 else 0

    parts: list[str] = [
        f'<svg width="{WIDTH}" height="{HEIGHT}" xmlns="http://www.w3.org/2000/svg">'
    ]
    parts += card_frame(WIDTH, HEIGHT)
    parts += terminal_chrome(WIDTH, f"guest@github:~$ streak --user {username}", CHROME_H)

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
        f'total contributions: <tspan fill="{COLORS["text"]}" font-weight="600">{fmt(total_contributions)}</tspan></text>'
    )

    footer_y = HEIGHT - 16
    parts.append(footer_comment(WIDTH / 2, footer_y, f"# synced {last_updated} \u00b7 v1"))
    parts.append(cursor_blink(WIDTH - 32, footer_y))

    parts.append("</svg>")
    return "\n".join(parts)
