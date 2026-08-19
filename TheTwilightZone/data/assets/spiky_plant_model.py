"""Spiky plant sprite loaded from the dedicated image asset."""

from __future__ import annotations

from pathlib import Path

import pygame


def create_spiky_plant_sprite(radius: float = 60.0) -> pygame.Surface:
    """Load the spiky plant art and fit it inside the hazard's display bounds."""
    size = int(radius * 2 + 18)
    asset_path = Path(__file__).resolve().with_name("plant.png")
    sprite = pygame.image.load(str(asset_path)).convert_alpha()

    source_width, source_height = sprite.get_size()
    scale = min(size / source_width, size / source_height)
    scaled_size = (
        max(1, round(source_width * scale)),
        max(1, round(source_height * scale)),
    )

    fitted_sprite = pygame.transform.smoothscale(sprite, scaled_size)
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    surface.blit(fitted_sprite, fitted_sprite.get_rect(center=surface.get_rect().center))
    return surface
