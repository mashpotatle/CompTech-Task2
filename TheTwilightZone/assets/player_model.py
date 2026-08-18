"""Simple procedural diver sprite used as a temporary player asset."""

from __future__ import annotations

import pygame


def create_player_sprite(width: int = 40, height: int = 40) -> pygame.Surface:
    """Build a compact, readable diver sprite for the player entity."""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    cx = width // 2
    cy = height // 2

    body_color = (72, 177, 212)
    dark_color = (18, 39, 46)
    suit_color = (30, 101, 123)
    accent_color = (255, 209, 102)
    fin_color = (158, 214, 232)

    # Body
    pygame.draw.ellipse(surface, body_color, (cx - 12, cy - 10, 24, 22))
    pygame.draw.rect(surface, suit_color, (cx - 7, cy - 1, 14, 16))

    # Head / helmet
    pygame.draw.circle(surface, (206, 230, 240), (cx, cy - 12), 9)
    pygame.draw.circle(surface, dark_color, (cx, cy - 12), 6)
    pygame.draw.circle(surface, accent_color, (cx + 2, cy - 14), 2)

    # Arms
    pygame.draw.line(surface, body_color, (cx - 9, cy + 2), (cx - 18, cy + 11), 4)
    pygame.draw.line(surface, body_color, (cx + 9, cy + 2), (cx + 18, cy + 11), 4)

    # Fins
    pygame.draw.polygon(surface, fin_color, [
        (cx - 10, cy + 16),
        (cx - 16, cy + 22),
        (cx - 5, cy + 22),
    ])
    pygame.draw.polygon(surface, fin_color, [
        (cx + 10, cy + 16),
        (cx + 16, cy + 22),
        (cx + 5, cy + 22),
    ])

    # Tank / gear
    pygame.draw.rect(surface, (64, 128, 148), (cx - 3, cy - 3, 6, 14))
    pygame.draw.rect(surface, accent_color, (cx + 8, cy - 3, 4, 7))

    # Flippers / motion accent
    pygame.draw.line(surface, (186, 235, 255), (cx - 2, cy + 18), (cx - 2, cy + 24), 2)
    pygame.draw.line(surface, (186, 235, 255), (cx + 2, cy + 18), (cx + 2, cy + 24), 2)

    return surface
