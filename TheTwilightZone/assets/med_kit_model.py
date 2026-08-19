"""Med-kit sprite loaded from the dedicated image asset."""

from __future__ import annotations

from pathlib import Path

import pygame


def create_med_kit_sprite(width: int = 47, height: int = 47) -> pygame.Surface:
    """Load the med-kit art and resize it to the desired in-game size."""
    asset_path = Path(__file__).resolve().with_name("medkit.png")
    sprite = pygame.image.load(str(asset_path)).convert_alpha()
    return pygame.transform.smoothscale(sprite, (width, height))
