"""Language statistics calculation."""

from typing import NamedTuple


class LanguagePercentage(NamedTuple):
    """Language with calculated percentage."""

    name: str
    bytes: int
    percentage: float


def calculate_language_percentages(
    language_totals: list[tuple[str, int]]
) -> list[LanguagePercentage]:
    """
    Calculate language percentages from byte counts.

    Args:
        language_totals: List of (language_name, byte_count) tuples

    Returns:
        List of LanguagePercentage with calculated percentages, sorted descending by bytes
    """
    if not language_totals or (total_bytes := sum(b for _, b in language_totals)) == 0:
        return []

    results = [
        LanguagePercentage(
            name=lang,
            bytes=bytes_count,
            percentage=round((bytes_count / total_bytes) * 100, 1),
        )
        for lang, bytes_count in language_totals
    ]

    # Sort descending by byte count
    results.sort(key=lambda x: x.bytes, reverse=True)

    return results
