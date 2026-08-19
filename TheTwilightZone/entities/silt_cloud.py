"""
Silt Cloud entity for The Twilight Zone game.

Silt clouds are environmental obstacles that reduce visibility and movement.
"""

from __future__ import annotations

import pygame

from data.assets.silt_cloud_model import create_silt_cloud_sprite


class SiltCloud(pygame.sprite.Sprite):
    """A murky cloud that reduces visibility and movement speed."""

    def __init__(
        self,
        position: tuple[float, float],
        cloud_id: str = "",
        radius: float = 40.0,
        visibility: float = 0.15,
        speed_reduction: float = 0.5,
    ):
        super().__init__()

        self.position = pygame.Vector2(position)
        self.cloud_id = cloud_id
        self.radius = max(0.0, float(radius))
        self.effect_radius = self.radius
        self.visibility_reduction = max(0.0, min(1.0, float(visibility)))
        self.speed_reduction = max(0.0, min(1.0, float(speed_reduction)))

        sprite_radius = max(20, int(self.radius))
        self.image = create_silt_cloud_sprite(sprite_radius)
        self.rect = self.image.get_rect(center=(round(self.position.x), round(self.position.y)))

    def update(self, delta_time: float) -> None:
        """Keep the cloud sprite aligned with its world position."""
        self.rect.center = (round(self.position.x), round(self.position.y))

    def draw(self, screen: pygame.Surface, camera=None) -> None:
        """Draw the cloud using world-to-screen camera conversion."""
        if camera is None:
            draw_position = self.position
        else:
            draw_position = camera.world_to_screen(self.position)

        screen_rect = self.image.get_rect(
            center=(round(draw_position.x), round(draw_position.y))
        )
        screen.blit(self.image, screen_rect)
