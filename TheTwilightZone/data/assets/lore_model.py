"""Lore fragment sprite loaded from the dedicated image asset."""

from __future__ import annotations

from pathlib import Path

import pygame


def create_lore_sprite(width: int = 70, height: int = 70) -> pygame.Surface:
    """Load the lore parchment art and resize it to the desired in-game size."""
    asset_path = Path(__file__).resolve().with_name("lore.png")
    sprite = pygame.image.load(str(asset_path)).convert_alpha()
    return pygame.transform.smoothscale(sprite, (width, height))
