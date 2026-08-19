"""Procedural side-on diver sprite for the player character."""

from __future__ import annotations

import pygame


def create_player_sprite(width: int = 72, height: int = 112) -> pygame.Surface:
    """Create a readable cave diver silhouette with clear front/back mass."""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    cx = width / 2
    cy = height / 2

    body = (68, 180, 202)
    suit = (21, 79, 90)
    suit_dark = (10, 34, 46)
    gear = (16, 125, 139)
    tank = (42, 97, 119)
    fin = (136, 214, 229)
    glow = (255, 214, 119)
    visor = (217, 242, 249)

    # Body mass.
    pygame.draw.ellipse(surface, suit, pygame.Rect(int(width * 0.22), int(height * 0.24), int(width * 0.5), int(height * 0.44)))
    pygame.draw.ellipse(surface, body, pygame.Rect(int(width * 0.28), int(height * 0.30), int(width * 0.38), int(height * 0.30)))
    pygame.draw.rect(surface, suit, (int(width * 0.28), int(height * 0.54), int(width * 0.34), int(height * 0.18)), border_radius=10)

    # Oxygen tank and main gear.
    pygame.draw.rect(surface, tank, (int(width * 0.60), int(height * 0.38), int(width * 0.18), int(height * 0.26)), border_radius=8)
    pygame.draw.rect(surface, gear, (int(width * 0.68), int(height * 0.44), int(width * 0.08), int(height * 0.12)), border_radius=4)
    pygame.draw.rect(surface, glow, (int(width * 0.72), int(height * 0.47), int(width * 0.04), int(height * 0.06)), border_radius=2)

    # Helmet and visor.
    pygame.draw.circle(surface, visor, (int(width * 0.63), int(height * 0.20)), int(width * 0.16))
    pygame.draw.circle(surface, suit_dark, (int(width * 0.63), int(height * 0.20)), int(width * 0.12))
    pygame.draw.arc(surface, glow, pygame.Rect(int(width * 0.55), int(height * 0.13), int(width * 0.16), int(height * 0.11)), 0.2, 2.9, 3)

    # Arms and fins.
    pygame.draw.line(surface, body, (int(width * 0.30), int(height * 0.56)), (int(width * 0.12), int(height * 0.64)), 6)
    pygame.draw.line(surface, body, (int(width * 0.56), int(height * 0.70)), (int(width * 0.74), int(height * 0.88)), 6)
    pygame.draw.polygon(surface, fin, [(int(width * 0.18), int(height * 0.72)), (int(width * 0.06), int(height * 0.92)), (int(width * 0.28), int(height * 0.88))])
    pygame.draw.polygon(surface, fin, [(int(width * 0.68), int(height * 0.70)), (int(width * 0.83), int(height * 0.92)), (int(width * 0.60), int(height * 0.87))])

    # Small motion accents to give depth.
    pygame.draw.line(surface, (192, 234, 250), (int(width * 0.38), int(height * 0.60)), (int(width * 0.38), int(height * 0.78)), 3)
    pygame.draw.line(surface, (192, 234, 250), (int(width * 0.52), int(height * 0.60)), (int(width * 0.52), int(height * 0.78)), 3)

    return surface
