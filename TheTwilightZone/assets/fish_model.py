"""Procedural hostile-fish sprite for the cave fauna hazard."""

from __future__ import annotations

import pygame


def create_fish_sprite(width: int = 96, height: int = 60) -> pygame.Surface:
    """Create a strong side-profile fish silhouette with a threatening body."""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)

    body = (52, 162, 174)
    body_dark = (17, 65, 73)
    fin = (12, 101, 116)
    eye = (18, 28, 33)
    highlight = (196, 245, 242)

    # Main body with tapering tail.
    pygame.draw.ellipse(surface, body, pygame.Rect(int(width * 0.18), int(height * 0.18), int(width * 0.64), int(height * 0.6)))
    pygame.draw.polygon(surface, body, [(int(width * 0.12), int(height * 0.5)), (0, int(height * 0.18)), (0, int(height * 0.82))])
    pygame.draw.polygon(surface, fin, [(int(width * 0.34), int(height * 0.18)), (int(width * 0.52), 0), (int(width * 0.52), int(height * 0.32))])
    pygame.draw.polygon(surface, fin, [(int(width * 0.38), int(height * 0.78)), (int(width * 0.52), int(height * 0.98)), (int(width * 0.52), int(height * 0.56))])

    # Eye and mouth details.
    pygame.draw.circle(surface, eye, (int(width * 0.72), int(height * 0.42)), 4)
    pygame.draw.circle(surface, highlight, (int(width * 0.73), int(height * 0.40)), 2)
    pygame.draw.line(surface, body_dark, (int(width * 0.76), int(height * 0.54)), (int(width * 0.86), int(height * 0.60)), 2)
    pygame.draw.arc(surface, body_dark, pygame.Rect(int(width * 0.62), int(height * 0.38), int(width * 0.18), int(height * 0.14)), -0.6, 0.8, 2)

    return surface
