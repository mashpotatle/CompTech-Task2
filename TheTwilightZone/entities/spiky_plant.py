"""
Spiky Plant entity for The Twilight Zone.

Spiky plants are stationary environmental hazards. They damage the
player on contact and are rendered in world space using the camera.
"""

from __future__ import annotations

import math
import pygame

from data.assets.spiky_plant_model import create_spiky_plant_sprite


class SpikyPlant(pygame.sprite.Sprite):
    """Stationary damaging cave flora."""

    def __init__(
        self,
        position: tuple[float, float],
        plant_id: str = "",
        damage: int = 15,
        radius: float = 24,
    ):
        super().__init__()

        self.position = pygame.Vector2(position)
        self.plant_id = plant_id

        self.damage = int(damage)
        self.collision_radius = float(radius)

        self.damage_cooldown = 0.75
        self.damage_timer = 0.0

        self.image = create_spiky_plant_sprite(float(radius))

        size = self.image.get_width()
        centre = size // 2

        self.rect = self.image.get_rect(
            center=(
                round(self.position.x),
                round(self.position.y),
            )
        )

    # ==========================================================
    # UPDATE
    # ==========================================================

    def update(self, delta_time: float) -> None:
        self.damage_timer = max(
            0.0,
            self.damage_timer - delta_time,
        )

        self.rect.center = (
            round(self.position.x),
            round(self.position.y),
        )

    # ==========================================================
    # COLLISION
    # ==========================================================

    def check_player_collision(
        self,
        player_rect: pygame.Rect,
    ) -> bool:

        closest_x = max(
            player_rect.left,
            min(self.position.x, player_rect.right),
        )

        closest_y = max(
            player_rect.top,
            min(self.position.y, player_rect.bottom),
        )

        distance = pygame.Vector2(
            closest_x,
            closest_y,
        ).distance_to(self.position)

        if distance > self.collision_radius:
            return False

        if self.damage_timer > 0:
            return False

        self.damage_timer = self.damage_cooldown
        return True

    # ==========================================================
    # DRAWING
    # ==========================================================

    def draw(
        self,
        screen: pygame.Surface,
        camera,
    ) -> None:

        screen_position = camera.world_to_screen(
            self.position
        )

        draw_rect = self.image.get_rect(
            center=(
                round(screen_position.x),
                round(screen_position.y),
            )
        )

        screen.blit(self.image, draw_rect)
