"""Loading of the player diver sprite asset."""

from __future__ import annotations

from pathlib import Path

import pygame


def create_player_sprite(width: int = 170, height: int = 92) -> pygame.Surface:
    """Load and scale the side-on diver art stored as a PNG asset."""
    asset_path = Path(__file__).resolve().with_name("player_diver.png")
    sprite = pygame.image.load(str(asset_path)).convert_alpha()
    sprite = pygame.transform.smoothscale(sprite, (width, height))
    return sprite
