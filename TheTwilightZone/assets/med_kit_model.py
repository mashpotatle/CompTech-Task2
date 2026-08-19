"""Procedural med-kit sprite for the health pickup item."""

from __future__ import annotations

import pygame


def create_med_kit_sprite(width: int = 70, height: int = 70) -> pygame.Surface:
    """Create a medical kit that stands out against the dark cave palette."""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    cx = width // 2
    cy = height // 2

    shell = (226, 76, 76)
    shell_dark = (104, 33, 33)
    cross = (255, 245, 228)
    band = (255, 201, 130)

    # Case shadow and shell.
    pygame.draw.rect(surface, shell_dark, (cx - 13, cy - 10, 26, 30), border_radius=8)
    pygame.draw.rect(surface, shell, (cx - 15, cy - 12, 30, 32), border_radius=10)
    pygame.draw.rect(surface, band, (cx - 4, cy - 14, 8, 36), border_radius=4)
    pygame.draw.rect(surface, band, (cx - 14, cy - 4, 28, 8), border_radius=4)

    # White cross on the front.
    pygame.draw.rect(surface, cross, (cx - 3, cy - 13, 6, 26), border_radius=2)
    pygame.draw.rect(surface, cross, (cx - 13, cy - 3, 26, 6), border_radius=2)

    return surface
