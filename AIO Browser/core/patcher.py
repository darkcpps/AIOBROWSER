# core/patcher.py
# Compatibility module - imports from separate patcher modules
# This file maintains backward compatibility for existing imports

from core.goldberg_patcher import (
    ensure_goldberg_files,
    patch_game,
    revert_patch
)

from core.creamapi_patcher import (
    ensure_creamapi_files,
    patch_game_creamapi,
    revert_creamapi_patch
)

# Re-export all functions for backward compatibility
__all__ = [
    'ensure_goldberg_files',
    'patch_game',
    'revert_patch',
    'ensure_creamapi_files',
    'patch_game_creamapi',
    'revert_creamapi_patch'
]