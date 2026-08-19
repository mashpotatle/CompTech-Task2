"""Hotbar template — 5-slot quick-access inventory bar.

Matches the wireframe's row of circular slots along the bottom of the
screen. The overall bar position/size comes from `data/ui/hotbar.json`;
individual slot circles are laid out evenly inside that rect.
"""

from __future__ import annotations

import pygame

from ui.layout import load_layout
from ui import theme

SLOT_COUNT = 5


class Hotbar:
    """Draws the 5 hotbar slots and highlights the active one."""

    def __init__(self):
        self.layout = load_layout("hotbar")
        self.font = pygame.font.Font(None, theme.FONT_TINY)
        self.item_icons: dict[str, pygame.Surface] = {}

        self.slot_color = (200, 200, 200)
        self.slot_fill = (50, 50, 50)
        self.active_color = theme.COLOR_ACCENT
        self.text_color = theme.COLOR_TEXT

    def set_item_icons(self, item_icons: dict[str, pygame.Surface]) -> None:
        self.item_icons = dict(item_icons)

    def slot_rects(self, surface: pygame.Surface) -> list[pygame.Rect]:
        bar_rect = self.layout.rect(
            "hotbar_bar", pygame.Rect(0, surface.get_height() - 130, surface.get_width(), 100)
        )

        slot_diameter = min(60, bar_rect.height)
        spacing = 20
        total_width = (slot_diameter * SLOT_COUNT) + (spacing * (SLOT_COUNT - 1))
        start_x = bar_rect.centerx - total_width // 2
        y = bar_rect.centery

        rects = []
        for index in range(SLOT_COUNT):
            x = start_x + index * (slot_diameter + spacing)
            rects.append(pygame.Rect(x, y - slot_diameter // 2, slot_diameter, slot_diameter))
        return rects

    def draw(self, surface: pygame.Surface, items: list[str | None], active_index: int = 0) -> None:
        items = list(items) + [None] * (SLOT_COUNT - len(items))

        for index, rect in enumerate(self.slot_rects(surface)):
            outline = self.active_color if index == active_index else self.slot_color
            width = 4 if index == active_index else 2
            pygame.draw.circle(surface, self.slot_fill, rect.center, rect.width // 2)
            pygame.draw.circle(surface, outline, rect.center, rect.width // 2, width)

            item = items[index]
            if item and item in self.item_icons:
                icon = self.item_icons[item]
                sized_icon = pygame.transform.smoothscale(icon, (max(18, rect.width - 18), max(18, rect.height - 18)))
                surface.blit(sized_icon, sized_icon.get_rect(center=rect.center))
            elif item:
                text = item
                if text == "oxygen_tank":
                    text = "O₂"
                elif text == "med_kit":
                    text = "HP"
                label = self.font.render(str(text), True, self.text_color)
                surface.blit(label, label.get_rect(center=rect.center))
