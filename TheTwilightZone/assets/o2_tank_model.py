"""Simple procedural oxygen tank sprite for pickup items."""

from __future__ import annotations

import pygame


def create_oxygen_tank_sprite(width: int = 70, height: int = 70) -> pygame.Surface:
    """Create a small oxygen tank marker that reads clearly in the cave."""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    cx = width // 2
    cy = height // 2

    body = (62, 146, 196)
    dark = (20, 42, 58)
    accent = (189, 235, 255)
    valve = (103, 180, 220)

    # Main cylindrical body.
    pygame.draw.rect(surface, body, (cx - 8, cy - 10, 16, 22), border_radius=5)
    pygame.draw.rect(surface, dark, (cx - 6, cy - 8, 12, 18), border_radius=4)

    # Valve and gauge details.
    pygame.draw.rect(surface, valve, (cx + 9, cy - 2, 5, 4), border_radius=2)
    pygame.draw.rect(surface, accent, (cx - 2, cy - 5, 4, 10), border_radius=2)
    pygame.draw.circle(surface, accent, (cx, cy + 3), 3)

    # Tiny O2 mark.
    font = pygame.font.Font(None, 12)
    label = font.render("O₂", True, (235, 250, 255))
    label_rect = label.get_rect(center=(cx, cy + 1))
    surface.blit(label, label_rect)

    return surface
