"""HUD template — HP/O2 survival meters.

Starting-point implementation matching the game design doc's HUD
readability requirement (4.1/5.3): HP and O2 bars must stay legible,
including a low-value pulse warning. Bar rects come from
`data/ui/hud.json`, editable with the `uicreator` tool.
"""

from __future__ import annotations

import math

import pygame

from ui.layout import load_layout
from ui import theme

LOW_VALUE_THRESHOLD = 25


class HUD:
    """Draws the HP and O2 bars. Values are 0-100 percentages."""

    def __init__(self):
        self.layout = load_layout("hud")
        self.font = pygame.font.Font(None, theme.FONT_SMALL)

        self.bg_color = (30, 30, 30)
        self.border_color = theme.COLOR_BORDER
        self.hp_color = (200, 60, 60)
        self.o2_color = (70, 170, 210)
        self.text_color = theme.COLOR_TEXT

    def draw(self, surface: pygame.Surface, hp_percent: float, o2_percent: float) -> None:
        hp_percent = max(0.0, min(100.0, hp_percent))
        o2_percent = max(0.0, min(100.0, o2_percent))

        hp_rect = self.layout.rect("hp_bar", pygame.Rect(20, 20, 220, 26))
        o2_rect = self.layout.rect("o2_bar", pygame.Rect(20, 54, 220, 26))

        self._draw_bar(surface, hp_rect, "HP", hp_percent, self.hp_color)
        self._draw_bar(surface, o2_rect, "O2", o2_percent, self.o2_color)

    def _draw_bar(self, surface, rect: pygame.Rect, label: str, percent: float, color) -> None:
        pygame.draw.rect(surface, self.bg_color, rect, border_radius=theme.BAR_BORDER_RADIUS)

        fill_color = color
        if percent <= LOW_VALUE_THRESHOLD:
            # Pulse the fill colour to warn the player the meter is critical.
            pulse = (math.sin(pygame.time.get_ticks() / 150.0) + 1) / 2
            fill_color = tuple(int(c + (255 - c) * pulse * 0.5) for c in color)

        fill_width = int(rect.width * (percent / 100))
        if fill_width > 0:
            fill_rect = pygame.Rect(rect.x, rect.y, fill_width, rect.height)
            pygame.draw.rect(surface, fill_color, fill_rect, border_radius=theme.BAR_BORDER_RADIUS)

        pygame.draw.rect(surface, self.border_color, rect, theme.BUTTON_BORDER_WIDTH, border_radius=theme.BAR_BORDER_RADIUS)

        label_surf = self.font.render(f"{label} {int(percent)}%", True, self.text_color)
        label_rect = label_surf.get_rect(center=rect.center)
        surface.blit(label_surf, label_rect)
