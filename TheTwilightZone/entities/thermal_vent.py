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
        self._eruption_timer = 0.0
        self.is_erupting = False

        visual_radius = max(
            self.damage_radius,
            self.radius + self.haze_length,
            self.haze_width * 1.6,
            24.0,
        )
        diameter = max(48, int(math.ceil(visual_radius * 2 + 20)))
        self.image = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(round(self.position.x), round(self.position.y)))
        self._plume_surface: pygame.Surface | None = None
        self._draw_visual()

    def update(self, delta_time: float) -> None:
        """Advance vent visual animation, eruption cycle, and keep position aligned."""
        if delta_time > 0:
            self._animation_time = (self._animation_time + delta_time * self.bubble_speed) % 1.0
            self._update_eruption_state(delta_time)
            self._draw_visual()
        self.rect.center = (round(self.position.x), round(self.position.y))

    def _update_eruption_state(self, delta_time: float) -> None:
        """Advance the eruption timer and toggle whether the vent is currently erupting."""
        if self.eruption_interval <= 0:
            self.is_erupting = False
            return

        period = self.eruption_interval + self.eruption_duration
        self._eruption_timer = (self._eruption_timer + delta_time) % period
        self.is_erupting = self._eruption_timer >= self.eruption_interval

    def _build_plume_surface(self) -> pygame.Surface:
        """Bake a soft, gradient haze plume from overlapping fuzzy blobs instead of hard-edged polygons."""
        diameter = self.image.get_width()
        plume = pygame.Surface((diameter, diameter), pygame.SRCALPHA)

        center = pygame.Vector2(diameter / 2, diameter / 2)
        plume_length = max(self.haze_length, self.radius * 2.5, 50.0)
        plume_width = max(self.haze_width, self.radius * 1.2, 18.0)
        alpha_scale = self.haze_alpha / 255.0

        steps = 40
        for i in range(steps, -1, -1):
            t = i / steps
            blob_center = center + self.direction * (plume_length * t)
            blob_radius = max(3.0, (plume_width * 0.5) * (0.2 + (1.0 - t) * 0.85))

            color_t = min(1.0, t * 1.2)
            r = 255
            g = int(240 - (240 - 150) * color_t)
            b = int(90 + (170 - 90) * (1.0 - color_t))
            fade = (1.0 - t) ** 0.6

            self._blit_soft_blob(plume, blob_center, blob_radius, (r, g, b), fade * alpha_scale)

        return plume

    @staticmethod
    def _blit_soft_blob(surface: pygame.Surface, center: pygame.Vector2, radius: float, color: tuple[int, int, int], alpha_scale: float) -> None:
        """Draw a circle whose alpha fades smoothly from centre to edge, avoiding hard rings when overlapped."""
        if alpha_scale <= 0 or radius <= 0:
            return

        rings = 10
        for ring in range(rings, 0, -1):
            ring_t = ring / rings
            ring_radius = max(1, round(radius * ring_t))
            ring_alpha = int(60 * alpha_scale * (1.0 - ring_t) ** 1.5)
            if ring_alpha <= 0:
                continue
            pygame.draw.circle(
                surface,
                (*color, ring_alpha),
                (round(center.x), round(center.y)),
                ring_radius,
            )

    def _draw_visual(self) -> None:
        self.image.fill((0, 0, 0, 0))

        # The plume shape never changes at runtime, so bake it once and reuse it.
        if self._plume_surface is None:
            self._plume_surface = self._build_plume_surface()
        self.image.blit(self._plume_surface, (0, 0))

        center = pygame.Vector2(self.image.get_width() / 2, self.image.get_height() / 2)
        side = pygame.Vector2(-self.direction.y, self.direction.x)

        plume_length = max(self.haze_length, self.radius * 2.5, 50.0)

        # Fine bubbles stream away from the vent in a single narrow line.
        for i in range(max(8, self.bubble_count)):
            t = (self._animation_time + i / max(1, self.bubble_count)) % 1.0
            bubble_distance = plume_length * (0.12 + t * 0.88)
            wobble = math.sin((t * 16.0 + i * 0.8) * math.tau) * self.bubble_spread * 0.25
            bubble_pos = center + self.direction * bubble_distance + side * wobble
            bubble_radius = max(1, int(2.0 * (1.0 - t * 0.65)))
            bubble_alpha = max(25, int(180 * (1.0 - t)))
            pygame.draw.circle(
                self.image,
                (255, 238, 190, bubble_alpha),
                (round(bubble_pos.x), round(bubble_pos.y)),
                bubble_radius,
            )

        # Tiny vent mouth for the source point.
        pygame.draw.circle(self.image, (255, 208, 112, 220), (round(center.x), round(center.y)), max(2, int(self.radius * 0.35)))

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
        """Return the heat damage (passive plus eruption burst) at a given distance."""
        if self.damage_radius <= 0:
            return 0.0

        if distance > self.damage_radius:
            return 0.0

        ratio = max(0.0, 1.0 - (distance / self.damage_radius))
        damage = self.damage_per_second * ratio
        if self.is_erupting:
            damage += self.eruption_damage * ratio
        return damage
