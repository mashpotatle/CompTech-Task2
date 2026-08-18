"""Procedural fish sprite for temporary hazard art."""

from __future__ import annotations

import pygame


def create_fish_sprite(width: int = 32, height: int = 20) -> pygame.Surface:
    """Create a simple hostile-fish sprite with a tail and eye."""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)

    pygame.draw.ellipse(surface, (70, 200, 160), pygame.Rect(5, 3, 22, 14))
    pygame.draw.polygon(surface, (50, 160, 135), [(7, 10), (0, 3), (0, 17)])
    pygame.draw.circle(surface, (10, 20, 20), (23, 7), 2)
    pygame.draw.line(surface, (120, 240, 200), (16, 9), (20, 9), 2)
    return surface
