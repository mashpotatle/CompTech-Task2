"""Simple procedural med-kit sprite for health pickups."""

from __future__ import annotations

import pygame


def create_med_kit_sprite(width: int = 28, height: int = 28) -> pygame.Surface:
    """Create a compact med-kit pickup sprite."""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    cx = width // 2
    cy = height // 2

    case = (239, 103, 103)
    accent = (255, 234, 195)
    cross = (255, 255, 255)
    shadow = (123, 42, 42)

    pygame.draw.rect(surface, shadow, (cx - 9, cy - 10, 18, 22), border_radius=5)
    pygame.draw.rect(surface, case, (cx - 10, cy - 11, 20, 24), border_radius=6)
    pygame.draw.rect(surface, accent, (cx - 4, cy - 8, 8, 16), border_radius=2)
    pygame.draw.rect(surface, cross, (cx - 1, cy - 9, 2, 18), border_radius=1)
    pygame.draw.rect(surface, cross, (cx - 9, cy - 1, 18, 2), border_radius=1)

    return surface
