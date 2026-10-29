"""Top languages SVG card."""

from app.stats.models import UserStats

from .components import (
    block_meter,
    card_frame,
    cursor_blink,
    esc,
    font,
    footer_comment,
    language_color,
    svg_open,
    terminal_chrome,
    updated_label,
)
from .theme import COLORS

WIDTH = 480
CHROME_H = 40
ROW_H = 34
ROW_Y0 = CHROME_H + 34
SEGMENTS = 18
METER_X = 172


def generate_languages_card(stats: UserStats) -> str:
    """Generate a top-languages SVG card.

    Height is derived from the number of languages passed in (up to
    6) instead of a fixed 320px that leaves dead space for accounts
    with fewer languages. Empty input renders an explicit empty
    state rather than a mostly-blank card.
    """
    top_languages = stats.languages[:6]

    row_count = max(len(top_languages), 1)
    height = ROW_Y0 + row_count * ROW_H + 34

    parts: list[str] = [svg_open(WIDTH, height)]
    parts += card_frame(WIDTH, height)
    parts += terminal_chrome(
        WIDTH, f"guest@github:~$ languages --user {stats.username} --top 6", CHROME_H
    )

    if not top_languages:
        parts.append(
            f'<text x="24" y="{ROW_Y0}" {font(12)} fill="{COLORS["dim"]}"># no language data yet</text>'
        )
    else:
        for i, lang in enumerate(top_languages):
            y = ROW_Y0 + i * ROW_H
            color = language_color(lang)
            parts.append(f'<circle cx="28" cy="{y - 4}" r="4" fill="{color}"/>')
            parts.append(
                f'<text x="40" y="{y}" {font(12)} fill="{COLORS["text"]}">{esc(lang.name)}</text>'
            )
            filled = (lang.percentage / 100) * SEGMENTS
            parts += block_meter(
                METER_X, y - 12, SEGMENTS, filled, seg_w=8, gap=3, seg_h=10, color=color
            )
            parts.append(
                f'<text x="{WIDTH - 24}" y="{y}" text-anchor="end" {font(12, 600)} '
                f'fill="{COLORS["text"]}">{lang.percentage:.1f}%</text>'
            )

    footer_y = height - 16
    parts.append(footer_comment(WIDTH / 2, footer_y, updated_label(stats.fetched_at)))
    parts.append(cursor_blink(WIDTH - 32, footer_y))

    parts.append("</svg>")
    return "\n".join(parts)
