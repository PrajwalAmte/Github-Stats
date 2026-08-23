"""Shared visual theme for GitHub stats cards.

The whole set is styled as terminal output rather than a generic
rounded dashboard card: monospace throughout, a fake shell prompt as
the card's title, and segmented block meters instead of smooth
progress bars. One theme module so every card pulls from the same
palette instead of redefining colors inline.
"""

COLORS = {
    "bg": "#0b0e14",  # near-black, slightly blue — distinct from GitHub's own #0d1117
    "chrome": "#161c2c",  # terminal title bar
    "border": "#232a3d",
    "text": "#d5dae3",  # primary text
    "dim": "#5c6370",  # comments / labels, One-Dark-inspired
    "accent": "#59d499",  # prompt / success green, muted rather than neon
    "accent_blue": "#61afef",
    "accent_amber": "#e5a659",
    "empty_block": "#1c2333",
    "dot_red": "#e5534b",
    "dot_yellow": "#e2b93d",
    "dot_green": "#57ab5a",
}

FONT_STACK = (
    "'JetBrains Mono','Fira Code',ui-monospace,SFMono-Regular,"
    "Menlo,Consolas,monospace"
)

# GitHub linguist colors — kept as-is, this mapping is the one place
# a *non*-monospace-green color is correct, since language identity
# color is information, not decoration.
LANGUAGE_COLORS = {
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#2b7489",
    "Java": "#b07219",
    "C++": "#f34b7d",
    "C": "#555555",
    "C#": "#178600",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Ruby": "#701516",
    "PHP": "#4F5D95",
    "Swift": "#ffac45",
    "Kotlin": "#A97BFF",
    "Dart": "#00B4AB",
    "Shell": "#89e051",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Jupyter Notebook": "#DA5B0B",
    "R": "#198CE7",
    "Scala": "#c22d40",
    "Objective-C": "#438eff",
    "Perl": "#0298c3",
    "Lua": "#000080",
    "Haskell": "#5e5086",
    "Elixir": "#6e4a7e",
}