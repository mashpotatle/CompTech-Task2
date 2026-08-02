"""
Global configuration settings for The Twilight Zone.

Keeping configuration values in one module makes the game easier to
maintain and allows gameplay settings to be changed without searching
through the entire codebase.
"""

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Display Settings
# ---------------------------------------------------------------------------

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768

WINDOW_TITLE = "The Twilight Zone"

PLAYER_WIDTH = 40
PLAYER_HEIGHT = 40

# ---------------------------------------------------------------------------
# Performance Settings
# ---------------------------------------------------------------------------

# The target frame rate specified in the game design document.
TARGET_FPS = 60

# Number of sections to load ahead of the player so transitions feel
# smoother. Set to 0 to disable preloading.
PRELOAD_SECTION_COUNT = 3

# ---------------------------------------------------------------------------
# Debug Settings
# ---------------------------------------------------------------------------

# Used during development to display useful information such as FPS.
# This should be disabled for the final release.
DEBUG_MODE = True

# Displays collision geometry when enabled.
DEBUG_COLLISION = True

# Displays the player's collision rectangle.
DEBUG_PLAYER_COLLISION = True


# ---------------------------------------------------------------------------
# Runtime Settings / Save Data
# ---------------------------------------------------------------------------

@dataclass
class RuntimeSettings:
    """Persisted gameplay and UI state for the current run."""

    color_blind_mode: bool = False
    master_volume: int = 80
    ambience_volume: int = 50
    menus_volume: int = 100
    game_volume: int = 100
    max_distance_travelled: int = 0


SETTINGS = RuntimeSettings()