"""Procedural thermal-vent sprite used as the lava-like hazard marker."""

from __future__ import annotations

import math

import pygame


def create_thermal_vent_sprite(radius: int = 82) -> pygame.Surface:
    """Create a glowing vent with a hot plume and jagged crack geometry."""
    diameter = max(44, radius * 2)
    surface = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
    cx = diameter // 2
    cy = diameter // 2

    # Warm luminous glow to match the orange screen flash.
    for layer, color in enumerate([(255, 160, 68, 120), (255, 190, 90, 160), (255, 130, 60, 190)]):
        offset = (layer - 1) * 8
        pygame.draw.circle(surface, color, (cx + offset, cy), radius - 10)

    # Vent mouth.
    pygame.draw.circle(surface, (255, 228, 154, 220), (cx, cy), max(10, radius // 4))
    pygame.draw.circle(surface, (255, 102, 42, 255), (cx, cy), max(16, radius // 3))

    # Pressure plume.
    for i in range(12):
        angle = i * (math.pi / 6)
        spread = radius * 0.9
        x1 = cx + int(18 * math.cos(angle))
        y1 = cy + int(18 * math.sin(angle))
        x2 = cx + int((spread + 14) * math.cos(angle))
        y2 = cy + int((spread + 12) * math.sin(angle))
        pygame.draw.line(surface, (255, 180, 80, 120), (x1, y1), (x2, y2), 10)

    # Bubble crack detail.
    for px, py in [(cx - 10, cy + 8), (cx + 12, cy - 10), (cx + 2, cy - 16), (cx - 16, cy - 4)]:
        pygame.draw.circle(surface, (255, 213, 120, 200), (px, py), 6)

    return surface
