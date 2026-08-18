"""Loader for UI layouts authored with the `uicreator` tool.

Layouts are plain JSON files under `data/ui/<screen>.json`, each describing
a screen's widgets as simple pixel rectangles (x, y, w, h) plus optional
text/colors. This lets UI positioning be edited visually instead of by
guessing pixel numbers in code.
"""

from __future__ import annotations

import json
from typing import Any

import pygame
from paths import UI_LAYOUT_DIR

DATA_DIR = UI_LAYOUT_DIR


class Layout:
    """A parsed UI layout with named widgets."""

    def __init__(self, data: dict[str, Any]):
        self.reference_width = data.get("reference_width", 1024)
        self.reference_height = data.get("reference_height", 768)
        self.widgets: dict[str, dict[str, Any]] = {
            widget["id"]: widget for widget in data.get("widgets", []) if "id" in widget
        }

    def rect(self, widget_id: str, default: pygame.Rect | None = None) -> pygame.Rect | None:
        """Return the pygame.Rect for a widget, or `default` if not defined."""
        widget = self.widgets.get(widget_id)
        if widget is None:
            return default
        return pygame.Rect(widget["x"], widget["y"], widget["w"], widget["h"])

    def get(self, widget_id: str, key: str, default: Any = None) -> Any:
        """Return an arbitrary property (e.g. "text", "color") for a widget."""
        widget = self.widgets.get(widget_id)
        if widget is None:
            return default
        return widget.get(key, default)


def load_layout(name: str) -> Layout:
    """Load `data/ui/<name>.json`. Returns an empty layout if it is missing."""
    path = DATA_DIR / f"{name}.json"
    if not path.exists():
        return Layout({})
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (json.JSONDecodeError, OSError):
        return Layout({})
    return Layout(data)
