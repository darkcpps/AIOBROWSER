# core/patcher.py
# Compatibility module - imports from separate patcher modules
# This file maintains backward compatibility for existing imports

from core.goldberg_patcher import (
    ensure_goldberg_files,
    patch_game,
    revert_patch
)

from core.greenluma_patcher import (
    patch_with_greenluma,
    get_current_applist
)

# Re-export all functions for backward compatibility
__all__ = [
    'ensure_goldberg_files',
    'patch_game',
    'revert_patch',
    'patch_with_greenluma',
    'get_current_applist'
]