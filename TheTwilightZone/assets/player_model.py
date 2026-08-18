"""Procedural side-on diver sprite for the player character."""

from __future__ import annotations

import pygame


def create_player_sprite(width: int = 70, height: int = 110) -> pygame.Surface:
    """Create a tall side-on diver sprite with a vertical player hitbox."""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    cx = width // 2
    cy = height // 2

    body_color = (72, 177, 212)
    dark_color = (18, 39, 46)
    suit_color = (30, 101, 123)
    accent_color = (255, 209, 102)
    fin_color = (158, 214, 232)
    tank_color = (64, 128, 148)

    # Body / torso (side profile)
    pygame.draw.rect(surface, suit_color, (int(width * 0.25), int(height * 0.30), int(width * 0.42), int(height * 0.42)), border_radius=12)
    pygame.draw.rect(surface, body_color, (int(width * 0.30), int(height * 0.36), int(width * 0.32), int(height * 0.30)), border_radius=10)

    # Tank and gear on the back
    pygame.draw.rect(surface, tank_color, (int(width * 0.58), int(height * 0.38), int(width * 0.18), int(height * 0.26)), border_radius=8)
    pygame.draw.rect(surface, accent_color, (int(width * 0.72), int(height * 0.42), int(width * 0.06), int(height * 0.12)), border_radius=4)

    # Head / helmet
    pygame.draw.circle(surface, (206, 230, 240), (int(width * 0.67), int(height * 0.20)), int(width * 0.17))
    pygame.draw.circle(surface, dark_color, (int(width * 0.67), int(height * 0.20)), int(width * 0.11))
    pygame.draw.circle(surface, accent_color, (int(width * 0.71), int(height * 0.18)), int(width * 0.03))

    # Arm and leg detail for side profile
    pygame.draw.line(surface, body_color, (int(width * 0.30), int(height * 0.55)), (int(width * 0.12), int(height * 0.67)), 6)
    pygame.draw.line(surface, body_color, (int(width * 0.61), int(height * 0.72)), (int(width * 0.75), int(height * 0.85)), 6)
    pygame.draw.line(surface, fin_color, (int(width * 0.34), int(height * 0.74)), (int(width * 0.18), int(height * 0.92)), 6)
    pygame.draw.line(surface, fin_color, (int(width * 0.62), int(height * 0.74)), (int(width * 0.79), int(height * 0.92)), 6)

    # Tail/flipper detail
    pygame.draw.polygon(surface, fin_color, [
        (int(width * 0.20), int(height * 0.76)),
        (int(width * 0.12), int(height * 0.92)),
        (int(width * 0.30), int(height * 0.88)),
    ])
    pygame.draw.polygon(surface, fin_color, [
        (int(width * 0.74), int(height * 0.76)),
        (int(width * 0.84), int(height * 0.92)),
        (int(width * 0.65), int(height * 0.88)),
    ])

    # Small motion highlights
    pygame.draw.line(surface, (186, 235, 255), (int(width * 0.32), int(height * 0.68)), (int(width * 0.34), int(height * 0.80)), 3)
    pygame.draw.line(surface, (186, 235, 255), (int(width * 0.60), int(height * 0.68)), (int(width * 0.58), int(height * 0.80)), 3)

    return surface
