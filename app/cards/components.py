"""Reusable SVG fragments shared across all cards.

Every card is built from the same small vocabulary: a terminal
chrome header, a prompt-style key/value row, and a segmented block
meter. Centralizing these is what stops each card file from
hand-rolling its own rects and font-family strings.
"""

from xml.sax.saxutils import escape as _escape

from .theme import COLORS, FONT_STACK


def esc(value: object) -> str:
    """XML-escape any value dropped into SVG text content."""
    return _escape(str(value))


def font(size: int, weight: int = 400) -> str:
    return f'font-family="{FONT_STACK}" font-size="{size}" font-weight="{weight}"'


def terminal_chrome(width: int, path: str, height: int = 40) -> list[str]:
    """Title bar styled like a terminal window: traffic-light dots
    plus a fake shell path. Top corners match the card's rounding;
    the bottom edge of the bar is squared off against the body."""
    return [
        f'<rect x="0" y="0" width="{width}" height="{height}" rx="10" fill="{COLORS["chrome"]}"/>',
        f'<rect x="0" y="{height - 20}" width="{width}" height="20" fill="{COLORS["chrome"]}"/>',
        f'<circle cx="18" cy="{height / 2}" r="4.5" fill="{COLORS["dot_red"]}" opacity="0.75"/>',
        f'<circle cx="34" cy="{height / 2}" r="4.5" fill="{COLORS["dot_yellow"]}" opacity="0.75"/>',
        f'<circle cx="50" cy="{height / 2}" r="4.5" fill="{COLORS["dot_green"]}" opacity="0.75"/>',
        f'<text x="{width / 2}" y="{height / 2 + 4}" text-anchor="middle" '
        f'fill="{COLORS["dim"]}" {font(11)}>{esc(path)}</text>',
    ]


def kv_row(
    x_label: int,
    x_value_end: int,
    y: int,
    label: str,
    value: str,
    prompt: str = "$",
) -> list[str]:
    """A single `$ label ......... value` line."""
    return [
        f'<text x="{x_label}" y="{y}" {font(12)} fill="{COLORS["accent"]}">{esc(prompt)}</text>',
        f'<text x="{x_label + 16}" y="{y}" {font(12)} fill="{COLORS["dim"]}">{esc(label)}</text>',
        f'<text x="{x_value_end}" y="{y}" text-anchor="end" {font(13, 600)} '
        f'fill="{COLORS["text"]}">{esc(value)}</text>',
    ]


def block_meter(
    x: int,
    y: int,
    segments: int,
    filled: float,
    seg_w: int = 12,
    gap: int = 4,
    seg_h: int = 10,
    color: str = COLORS["accent"],
) -> list[str]:
    """Segmented meter (like a VU meter / battery indicator) instead
    of a smooth progress bar. `filled` is 0..segments, fractional
    values partially color the boundary segment."""
    parts = []
    for i in range(segments):
        cx = x + i * (seg_w + gap)
        portion = max(0.0, min(1.0, filled - i))
        fill = color if portion >= 1 else COLORS["empty_block"]
        parts.append(
            f'<rect x="{cx}" y="{y}" width="{seg_w}" height="{seg_h}" rx="2" fill="{fill}"/>'
        )
        if 0 < portion < 1:
            partial_w = seg_w * portion
            parts.append(
                f'<rect x="{cx}" y="{y}" width="{partial_w:.1f}" height="{seg_h}" rx="2" fill="{color}"/>'
            )
    return parts


def cursor_blink(x: int, y: int, height: int = 13) -> str:
    """A static block cursor — the one small signature flourish,
    used once per card, never as repeated decoration."""
    return f'<rect x="{x}" y="{y - height + 3}" width="7" height="{height}" fill="{COLORS["accent"]}" opacity="0.85"/>'


def footer_comment(x_center: int, y: int, text: str) -> str:
    return (
        f'<text x="{x_center}" y="{y}" text-anchor="middle" {font(10)} '
        f'fill="{COLORS["dim"]}">{esc(text)}</text>'
    )


def card_frame(width: int, height: int) -> list[str]:
    return [
        f'<rect width="{width}" height="{height}" rx="10" fill="{COLORS["bg"]}"/>',
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10" '
        f'fill="none" stroke="{COLORS["border"]}"/>',
    ]
