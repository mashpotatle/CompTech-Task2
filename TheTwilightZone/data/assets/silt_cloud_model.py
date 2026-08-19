"""Procedural silt cloud sprite used as the low-visibility cave hazard."""

from __future__ import annotations

import pygame


def create_silt_cloud_sprite(radius: int = 42) -> pygame.Surface:
    """Create a dense, soft cloud with a murky, low-visibility silhouette."""
    diameter = max(28, radius * 2)
    surface = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
    cx = diameter // 2
    cy = diameter // 2

    cloud_colors = [
        (143, 160, 169, 140),
        (188, 195, 198, 120),
        (104, 119, 128, 118),
        (67, 82, 90, 110),
    ]

    for index, offset in enumerate(((0, 0), (-18, 10), (18, -8), (8, 18), (-12, -16), (0, 22))):
        size = max(18, radius - 6 + index * 2)
        pygame.draw.circle(surface, cloud_colors[index % len(cloud_colors)], (cx + offset[0], cy + offset[1]), size)

    pygame.draw.circle(surface, (226, 233, 238, 90), (cx, cy), max(8, radius - 8))
    pygame.draw.circle(surface, (123, 143, 154, 110), (cx + 12, cy - 10), max(9, radius // 3))
    pygame.draw.circle(surface, (84, 101, 112, 120), (cx - 16, cy + 10), max(11, radius // 3))

    return surface
