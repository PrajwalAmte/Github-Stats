from .error import generate_error_card
from .languages import generate_languages_card
from .overview import generate_overview_card
from .profile import generate_profile_card
from .streak import generate_streak_card

CARDS = {
    "overview": generate_overview_card,
    "profile": generate_profile_card,
    "streak": generate_streak_card,
    "languages": generate_languages_card,
}

__all__ = [
    "CARDS",
    "generate_error_card",
    "generate_profile_card",
    "generate_streak_card",
    "generate_languages_card",
    "generate_overview_card",
]
