"""Procedural spiky-plant sprite for temporary hazard art."""

from __future__ import annotations

import math

import pygame


def create_spiky_plant_sprite(radius: float = 60.0) -> pygame.Surface:
    """Create a clustered spiky plant marker for cave hazards."""
    size = int(radius * 2 + 18)
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    centre = size // 2
    body_radius = int(radius * 0.55)

    pygame.draw.circle(surface, (46, 140, 72), (centre, centre), body_radius)
    pygame.draw.circle(surface, (20, 60, 32), (centre, centre), body_radius, 2)

    for i in range(12):
        angle = (math.tau / 12) * i
        inner = pygame.Vector2(math.cos(angle), math.sin(angle)) * body_radius
        outer = pygame.Vector2(math.cos(angle), math.sin(angle)) * radius
        left = pygame.Vector2(math.cos(angle + 0.18), math.sin(angle + 0.18)) * (body_radius * 0.85)
        right = pygame.Vector2(math.cos(angle - 0.18), math.sin(angle - 0.18)) * (body_radius * 0.85)
        pygame.draw.polygon(surface, (95, 220, 120), [
            (centre + left.x, centre + left.y),
            (centre + outer.x, centre + outer.y),
            (centre + right.x, centre + right.y),
        ])

    return surface
