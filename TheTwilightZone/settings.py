"""
Global configuration settings for The Twilight Zone.

Keeping configuration values in one module makes the game easier to
maintain and allows gameplay settings to be changed without searching
through the entire codebase.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


# ---------------------------------------------------------------------------
# Display Settings
# ---------------------------------------------------------------------------

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768

WINDOW_TITLE = "The Twilight Zone"

ASSET_SCALE = 2.5
PLAYER_WIDTH = 70
PLAYER_HEIGHT = 110

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

SAVE_PATH = Path(__file__).resolve().parent / "data" / "save.json"


@dataclass
class RuntimeSettings:
    """Persisted gameplay and UI state for the current run."""

    color_blind_mode: bool = False
    master_volume: int = 80
    ambience_volume: int = 50
    menus_volume: int = 100
    game_volume: int = 100
    max_distance_travelled: int = 0


def _coerce_int(value, default: int) -> int:
    try:
        return max(0, min(100, int(value)))
    except (TypeError, ValueError):
        return default


def _coerce_bool(value, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    return default


def load_settings(path: str | Path = SAVE_PATH) -> RuntimeSettings:
    """Load settings from the local JSON save file if it exists."""
    file_path = Path(path)
    if not file_path.exists():
        return RuntimeSettings()

    try:
        with file_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return RuntimeSettings()

    if not isinstance(data, dict):
        return RuntimeSettings()

    settings = RuntimeSettings()
    settings.color_blind_mode = _coerce_bool(data.get("color_blind_mode"), settings.color_blind_mode)
    settings.master_volume = _coerce_int(data.get("master_volume"), settings.master_volume)
    settings.ambience_volume = _coerce_int(data.get("ambience_volume"), settings.ambience_volume)
    settings.menus_volume = _coerce_int(data.get("menus_volume"), settings.menus_volume)
    settings.game_volume = _coerce_int(data.get("game_volume"), settings.game_volume)
    settings.max_distance_travelled = _coerce_int(data.get("max_distance_travelled"), settings.max_distance_travelled)
    return settings


def save_settings(settings: RuntimeSettings | None = None, path: str | Path = SAVE_PATH) -> RuntimeSettings:
    """Persist the current runtime settings to JSON."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    active_settings = settings or SETTINGS
    payload = asdict(active_settings)

    with file_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)

    return active_settings


SETTINGS = load_settings()