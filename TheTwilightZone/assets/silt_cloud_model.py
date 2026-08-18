"""Procedural silt cloud sprite used as a temporary environmental hazard."""

from __future__ import annotations

import pygame


def create_silt_cloud_sprite(radius: int = 40) -> pygame.Surface:
    """Create a soft, cloudy haze for the silt cloud hazard."""
    diameter = max(24, radius * 2)
    surface = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
    cx = diameter // 2
    cy = diameter // 2

    for offset in ((0, 0), (-12, 10), (12, -8), (8, 18), (-18, -12)):
        pygame.draw.circle(
            surface,
            (146, 168, 172, 110),
            (cx + offset[0], cy + offset[1]),
            radius - 6,
        )

    pygame.draw.circle(surface, (192, 200, 206, 85), (cx, cy), radius)
    pygame.draw.circle(surface, (120, 132, 138, 90), (cx + 6, cy - 6), max(8, radius // 3))
    return surface
