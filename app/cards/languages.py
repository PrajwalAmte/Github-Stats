"""Top languages SVG card."""

from datetime import datetime

from .components import block_meter, card_frame, cursor_blink, font, footer_comment, terminal_chrome
from .theme import COLORS, LANGUAGE_COLORS

WIDTH = 480
CHROME_H = 40
ROW_H = 34
ROW_Y0 = CHROME_H + 34
SEGMENTS = 18
METER_X = 150


def generate_languages_card(
    username: str,
    languages: list[tuple[str, float]],
    last_sync: datetime | None = None,
) -> str:
    """Generate a top-languages SVG card.

    Height is derived from the number of languages passed in (up to
    6) instead of a fixed 320px that leaves dead space for accounts
    with fewer languages. Empty input renders an explicit empty
    state rather than a mostly-blank card.
    """
    top_languages = languages[:6]
    last_updated = last_sync.strftime("%Y-%m-%d %H:%M UTC") if last_sync else "never"

    row_count = max(len(top_languages), 1)
    height = ROW_Y0 + row_count * ROW_H + 34

    parts: list[str] = [
        f'<svg width="{WIDTH}" height="{height}" xmlns="http://www.w3.org/2000/svg">'
    ]
    parts += card_frame(WIDTH, height)
    parts += terminal_chrome(
        WIDTH, f"guest@github:~$ languages --user {username} --top 6", CHROME_H
    )

    if not top_languages:
        parts.append(
            f'<text x="24" y="{ROW_Y0}" {font(12)} fill="{COLORS["dim"]}"># no language data yet</text>'
        )
    else:
        for i, (lang_name, percentage) in enumerate(top_languages):
            y = ROW_Y0 + i * ROW_H
            color = LANGUAGE_COLORS.get(lang_name, COLORS["dim"])
            parts.append(f'<circle cx="28" cy="{y - 4}" r="4" fill="{color}"/>')
            parts.append(
                f'<text x="40" y="{y}" {font(12)} fill="{COLORS["text"]}">{lang_name}</text>'
            )
            filled = (percentage / 100) * SEGMENTS
            parts += block_meter(
                METER_X, y - 12, SEGMENTS, filled, seg_w=8, gap=3, seg_h=10, color=color
            )
            parts.append(
                f'<text x="{WIDTH - 24}" y="{y}" text-anchor="end" {font(12, 600)} '
                f'fill="{COLORS["text"]}">{percentage:.1f}%</text>'
            )

    footer_y = height - 16
    parts.append(footer_comment(WIDTH / 2, footer_y, f"# synced {last_updated} \u00b7 v1"))
    parts.append(cursor_blink(WIDTH - 32, footer_y))

    parts.append("</svg>")
    return "\n".join(parts)
