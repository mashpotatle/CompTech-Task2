"""Centralised filesystem paths for The Twilight Zone.

Using one module for path construction avoids scattering relative path logic
throughout the codebase and makes path changes safer.
"""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
ASSETS_DIR = DATA_DIR / "assets"
UI_LAYOUT_DIR = DATA_DIR / "ui"
CAVE_SECTIONS_DIR = DATA_DIR / "cave_sections"


def data_path(*parts: str) -> Path:
    """Build an absolute path inside the data directory."""

    return DATA_DIR.joinpath(*parts)