"""
Thermal Vent entity for The Twilight Zone game.

Thermal vents are environmental hazards that deal damage to the player.
"""

from __future__ import annotations

import math

import pygame


class ThermalVent(pygame.sprite.Sprite):
    """A hot vent that emits directional haze and damages nearby players."""

    def __init__(
        self,
        position: tuple[float, float],
        vent_id: str = "",
        direction: tuple[float, float] = (1.0, 0.0),
        radius: float = 26.0,
        heat_radius: float = 60.0,
        heat_damage: float = 10.0,
        eruption_damage: float = 20.0,
        eruption_duration: float = 1.0,
        eruption_interval: float = 5.0,
        haze_length: float = 95.0,
        haze_width: float = 30.0,
        haze_alpha: int = 65,
        bubble_count: int = 14,
        bubble_spread: float = 15.0,
        bubble_speed: float = 1.0,
    ):
        super().__init__()

        self.position = pygame.Vector2(position)
        self.vent_id = vent_id

        self.direction = pygame.Vector2(direction)
        if self.direction.length_squared() == 0:
            self.direction = pygame.Vector2(1.0, 0.0)
        else:
            self.direction = self.direction.normalize()

        self.radius = max(4.0, float(radius))
        self.damage_radius = max(0.0, float(heat_radius))
        self.damage_per_second = max(0.0, float(heat_damage))
        self.eruption_damage = max(0.0, float(eruption_damage))
        self.eruption_duration = max(0.0, float(eruption_duration))
        self.eruption_interval = max(0.0, float(eruption_interval))

        self.haze_length = max(0.0, float(haze_length))
        self.haze_width = max(0.0, float(haze_width))
        self.haze_alpha = max(0, min(255, int(haze_alpha)))
        self.bubble_count = max(0, int(bubble_count))
        self.bubble_spread = max(0.0, float(bubble_spread))
        self.bubble_speed = max(0.05, float(bubble_speed))

        self._animation_time = 0.0

        visual_radius = max(
            self.damage_radius,
            self.radius + self.haze_length,
            self.haze_width * 1.6,
            24.0,
        )
        diameter = max(48, int(math.ceil(visual_radius * 2 + 20)))
        self.image = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(round(self.position.x), round(self.position.y)))
        self._draw_visual()

    def update(self, delta_time: float) -> None:
        """Advance vent visual animation and keep position aligned."""
        if delta_time > 0:
            self._animation_time = (self._animation_time + delta_time * self.bubble_speed) % 1.0
            self._draw_visual()
        self.rect.center = (round(self.position.x), round(self.position.y))

    def _draw_visual(self) -> None:
        self.image.fill((0, 0, 0, 0))

        center = pygame.Vector2(self.image.get_width() / 2, self.image.get_height() / 2)
        side = pygame.Vector2(-self.direction.y, self.direction.x)

        # Vent mouth glow.
        pygame.draw.circle(self.image, (255, 95, 52, 240), (round(center.x), round(center.y)), int(self.radius))
        pygame.draw.circle(self.image, (255, 185, 105, 235), (round(center.x), round(center.y)), max(3, int(self.radius * 0.45)))

        # Faint red haze plume extending in vent direction.
        layers = 6
        for i in range(layers):
            t = (i + 1) / layers
            layer_center = center + self.direction * (self.haze_length * t * 0.56)
            half_width = self.haze_width * (1.0 - t * 0.52)
            half_len = self.haze_length * (0.12 + t * 0.11)

            points = [
                layer_center - self.direction * half_len + side * half_width,
                layer_center + self.direction * half_len + side * (half_width * 0.58),
                layer_center + self.direction * half_len - side * (half_width * 0.58),
                layer_center - self.direction * half_len - side * half_width,
            ]
            alpha = int(self.haze_alpha * (1.0 - t * 0.82))
            pygame.draw.polygon(
                self.image,
                (255, 78, 68, max(0, alpha)),
                [(round(p.x), round(p.y)) for p in points],
            )

        # Fine bubbles that stream through the haze.
        for i in range(self.bubble_count):
            t = (self._animation_time + i / max(1, self.bubble_count)) % 1.0
            forward = self.haze_length * (0.08 + t * 0.92)
            wobble = math.sin((t * 10.0 + i * 0.7) * math.tau) * self.bubble_spread * (1.0 - t)
            bubble_pos = center + self.direction * forward + side * wobble

            bubble_radius = max(1, int(1 + (1.0 - t) * 2.0))
            bubble_alpha = max(18, int(200 * (1.0 - t)))

            pygame.draw.circle(
                self.image,
                (255, 228, 210, bubble_alpha),
                (round(bubble_pos.x), round(bubble_pos.y)),
                bubble_radius,
            )

        # Direction indicator to keep the vent easy to read.
        end = center + self.direction * max(self.radius * 1.2, self.haze_length * 0.45)
        pygame.draw.line(
            self.image,
            (255, 235, 215, 170),
            (round(center.x), round(center.y)),
            (round(end.x), round(end.y)),
            2,
        )

    def draw(self, screen: pygame.Surface, camera=None) -> None:
        """Draw the vent."""
        if camera is None:
            draw_position = self.position
        else:
            draw_position = camera.world_to_screen(self.position)

        screen_rect = self.image.get_rect(
            center=(round(draw_position.x), round(draw_position.y))
        )
        screen.blit(self.image, screen_rect)

    def get_damage_at_distance(self, distance: float) -> float:
        """Return the continuous heat damage at a given distance."""
        if self.damage_radius <= 0:
            return 0.0

        if distance > self.damage_radius:
            return 0.0

        ratio = 1.0 - (distance / self.damage_radius)
        return self.damage_per_second * max(0.0, ratio)
