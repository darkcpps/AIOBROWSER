# themes/__init__.py
from .midnight_purple import MIDNIGHT_PURPLE
from .black_gold import BLACK_GOLD
from .aurora_borealis import AURORA_BOREALIS

THEMES = {
    "default": MIDNIGHT_PURPLE,
    "aurora_borealis": AURORA_BOREALIS,
    "black_gold": BLACK_GOLD,
}

# Current active theme (default)
_current_theme = "default"


def get_current_theme():
    return _current_theme


def set_current_theme(theme_name):
    global _current_theme
    if theme_name in THEMES:
        _current_theme = theme_name
        return True
    return False


def get_colors():
    return THEMES.get(_current_theme, THEMES["default"])


# For backward compatibility - create a copy, not a reference
COLORS = dict(THEMES["default"])


def update_colors():
    global COLORS
    # Update all keys in the COLORS dictionary with current theme
    new_colors = get_colors()
    # Remove keys that don't exist in new theme
    for key in list(COLORS.keys()):
        if key not in new_colors:
            del COLORS[key]
    # Update/add all keys from new theme
    for key, value in new_colors.items():
        COLORS[key] = value
