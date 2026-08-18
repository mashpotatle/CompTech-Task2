"""Procedural thermal-vent sprite used as a temporary hazard marker."""

from __future__ import annotations

import pygame


def create_thermal_vent_sprite(radius: int = 30) -> pygame.Surface:
    """Create a visible hot vent glow suitable for the cave environment."""
    diameter = max(24, radius * 2)
    surface = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
    cx = diameter // 2
    cy = diameter // 2

    for i, alpha in enumerate((100, 140, 185)):
        offset = (i - 1) * 5
        pygame.draw.circle(surface, (255, 151, 71, alpha), (cx + offset, cy), radius - 4)

    pygame.draw.circle(surface, (255, 224, 140, 220), (cx, cy), max(5, radius // 3))
    pygame.draw.circle(surface, (255, 130, 60, 255), (cx, cy), radius - 10)
    return surface
