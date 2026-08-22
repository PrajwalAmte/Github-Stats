"""Tests for language statistics."""


from app.stats.languages import calculate_language_percentages


def test_empty_languages():
    """Test with no languages."""
    result = calculate_language_percentages([])
    assert result == []


def test_single_language():
    """Test with single language."""
    languages = [("Python", 1000)]
    result = calculate_language_percentages(languages)

    assert len(result) == 1
    assert result[0].name == "Python"
    assert result[0].bytes == 1000
    assert result[0].percentage == 100.0


def test_multiple_languages():
    """Test with multiple languages."""
    languages = [
        ("Python", 5000),
        ("JavaScript", 3000),
        ("TypeScript", 2000),
    ]
    result = calculate_language_percentages(languages)

    assert len(result) == 3

    # Should be sorted by bytes descending
    assert result[0].name == "Python"
    assert result[0].bytes == 5000
    assert result[0].percentage == 50.0

    assert result[1].name == "JavaScript"
    assert result[1].bytes == 3000
    assert result[1].percentage == 30.0

    assert result[2].name == "TypeScript"
    assert result[2].bytes == 2000
    assert result[2].percentage == 20.0


def test_percentage_rounding():
    """Test percentage rounding to 1 decimal place."""
    languages = [
        ("Python", 3333),
        ("JavaScript", 3333),
        ("TypeScript", 3334),
    ]
    result = calculate_language_percentages(languages)

    # Should be sorted and rounded
    assert len(result) == 3
    assert result[0].percentage == 33.3
    assert result[1].percentage == 33.3
    assert result[2].percentage == 33.3


def test_zero_bytes():
    """Test with zero bytes (edge case)."""
    languages = [("Python", 0)]
    result = calculate_language_percentages(languages)
    assert result == []
