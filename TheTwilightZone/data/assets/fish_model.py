"""Fish sprite loaded from the dedicated image asset."""

from __future__ import annotations

from pathlib import Path

import pygame


def create_fish_sprite(width: int = 96, height: int = 60) -> pygame.Surface:
    """Load fish art and fit it inside the target sprite bounds."""
    asset_path = Path(__file__).resolve().with_name("fish.png")
    sprite = pygame.image.load(str(asset_path)).convert_alpha()

    source_width, source_height = sprite.get_size()
    scale = min(width / source_width, height / source_height)
    scaled_size = (
        max(1, round(source_width * scale)),
        max(1, round(source_height * scale)),
    )

    fitted_sprite = pygame.transform.smoothscale(sprite, scaled_size)
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    surface.blit(fitted_sprite, fitted_sprite.get_rect(center=surface.get_rect().center))
    return surface
