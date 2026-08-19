"""Procedural oxygen tank sprite for the survival pickup item."""

from __future__ import annotations

import pygame


def create_oxygen_tank_sprite(width: int = 70, height: int = 70) -> pygame.Surface:
    """Create a readable O₂ tank that reads at a glance during gameplay."""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    cx = width // 2
    cy = height // 2

    tank = (90, 168, 214)
    tank_dark = (16, 55, 72)
    pipe = (137, 209, 232)
    glow = (214, 245, 255)
    gauge = (176, 242, 255)

    # Body and valve.
    pygame.draw.rect(surface, tank_dark, (cx - 17, cy - 12, 34, 34), border_radius=10)
    pygame.draw.rect(surface, tank, (cx - 15, cy - 10, 30, 30), border_radius=9)
    pygame.draw.rect(surface, pipe, (cx + 14, cy - 2, 6, 6), border_radius=3)
    pygame.draw.rect(surface, glow, (cx - 2, cy - 10, 4, 20), border_radius=2)

    # Gauge and label.
    pygame.draw.circle(surface, gauge, (cx, cy + 2), 7)
    pygame.draw.circle(surface, tank_dark, (cx, cy + 2), 4)
    pygame.draw.line(surface, gauge, (cx, cy - 2), (cx, cy + 8), 2)
    pygame.draw.line(surface, gauge, (cx - 6, cy + 2), (cx + 6, cy + 2), 2)

    # Simple O₂ mark using vector strokes rather than a font dependency.
    pygame.draw.line(surface, (226, 247, 255), (cx - 4, cy - 9), (cx + 4, cy - 9), 2)
    pygame.draw.line(surface, (226, 247, 255), (cx - 4, cy - 9), (cx - 4, cy + 7), 2)
    pygame.draw.line(surface, (226, 247, 255), (cx + 4, cy - 9), (cx + 4, cy + 7), 2)
    pygame.draw.circle(surface, (226, 247, 255), (cx, cy + 2), 2)

    return surface
