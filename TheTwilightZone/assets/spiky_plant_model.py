"""Procedural spiky-plant sprite for the cave flora hazard."""

from __future__ import annotations

import math

import pygame


def create_spiky_plant_sprite(radius: float = 60.0) -> pygame.Surface:
    """Create a dense thorny plant with a heavy central stalk and long spikes."""
    size = int(radius * 2 + 18)
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    centre = size // 2
    body_radius = int(radius * 0.55)

    base = (28, 122, 72)
    base_dark = (10, 54, 31)
    thorn = (116, 216, 134)
    thorn_dark = (64, 156, 89)

    # Central bulb and root body.
    pygame.draw.circle(surface, base, (centre, centre), body_radius)
    pygame.draw.circle(surface, base_dark, (centre, centre), body_radius, 3)
    pygame.draw.ellipse(surface, base_dark, pygame.Rect(centre - int(radius * 0.18), centre - int(radius * 0.28), int(radius * 0.36), int(radius * 0.56)))

    # Spike ring.
    for i in range(12):
        angle = (math.tau / 12) * i
        inner = pygame.Vector2(math.cos(angle), math.sin(angle)) * body_radius
        outer = pygame.Vector2(math.cos(angle), math.sin(angle)) * radius
        left = pygame.Vector2(math.cos(angle + 0.20), math.sin(angle + 0.20)) * (body_radius * 0.8)
        right = pygame.Vector2(math.cos(angle - 0.20), math.sin(angle - 0.20)) * (body_radius * 0.8)
        pygame.draw.polygon(surface, thorn, [
            (centre + left.x, centre + left.y),
            (centre + outer.x, centre + outer.y),
            (centre + right.x, centre + right.y),
        ])
        pygame.draw.line(surface, thorn_dark, (centre + inner.x, centre + inner.y), (centre + outer.x, centre + outer.y), 2)

    return surface
