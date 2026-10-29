"""Card shown instead of stats when they can't be produced.

Always a valid SVG, so a README shows a readable message rather than
a broken-image icon.
"""

from .components import card_frame, esc, font, svg_open, terminal_chrome
from .theme import COLORS

WIDTH = 480
HEIGHT = 140
CHROME_H = 40


def generate_error_card(username: str, title: str, detail: str) -> str:
    parts: list[str] = [svg_open(WIDTH, HEIGHT)]
    parts += card_frame(WIDTH, HEIGHT)
    parts += terminal_chrome(WIDTH, f"guest@github:~$ stats --user {username[:24]}", CHROME_H)
    parts.append(
        f'<text x="24" y="{CHROME_H + 38}" {font(13, 600)} fill="{COLORS["accent_amber"]}">'
        f"error: {esc(title)}</text>"
    )
    parts.append(
        f'<text x="24" y="{CHROME_H + 64}" {font(11)} fill="{COLORS["dim"]}"># {esc(detail)}</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)
