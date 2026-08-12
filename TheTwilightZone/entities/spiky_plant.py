"""
Spiky Plant entity for The Twilight Zone.

Spiky plants are stationary environmental hazards. They are rendered in
world space through the active camera and expose their gameplay values to
the game controller in the same way as Fish.
"""

from __future__ import annotations

import math

import pygame


class SpikyPlant(pygame.sprite.Sprite):
    """A stationary environmental hazard with a damaging collision area."