"""
Water-current entity for The Twilight Zone.

A Current is a static environmental hazard that pushes the player while
inside its influence area.  The class deliberately keeps the physics
independent from the Player class so it can be used by the game loop,
level loader, or tests without creating circular imports.
"""

from __future__ import annotations

import math

import pygame


class Current(pygame.sprite.Sprite):
    """A directional underwater current.

    Args:
        position: World-space centre of the current.
        direction: Direction in which the water flows. It is normalised.
        current_id: Optional level-data identifier.
        strength: Push speed/force applied uniformly throughout the current.
        effect_radius: Half-width/half-height of the square current's influence area in world pixels.

    The current applies uniform force (no falloff) to any position within
    its square influence area. ``strength`` is treated as pixels-per-second
    when used through :meth:`apply_to_player`.
    """

    def __init__(
        self,
        position: tuple[float, float],
        direction: tuple[float, float] = (1.0, 0.0),
        current_id: str = "",
        strength: float = 100.0,
        effect_radius: float = 60.0,
    ) -> None:
        super().__init__()

        self.position = pygame.Vector2(position)
        self.current_id = current_id

        self.direction = pygame.Vector2(direction)
        if self.direction.length_squared() == 0:
            self.direction = pygame.Vector2(1, 0)
        else:
            self.direction = self.direction.normalize()

        self.strength = max(0.0, float(strength))
        self.effect_radius = max(0.0, float(effect_radius))

        # Keep the sprite large enough to communicate the influence area,
        # while the actual physics uses world-space distance rather than
        # the sprite rectangle.
        self.radius = self.effect_radius
        diameter = max(2, math.ceil(self.effect_radius * 2))
        self.image = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        self.rect = self.image.get_rect(
            center=(round(self.position.x), round(self.position.y))
        )

        self._animation_time = 0.0
        self._draw_visual()

    # ------------------------------------------------------------------
    # Physics
    # ------------------------------------------------------------------

    def get_force_at_position(self, position: pygame.Vector2) -> pygame.Vector2:
        """Return the current's push vector at ``position``.

        Returns uniform push force if the position is within the square
        influence area, otherwise returns zero force.
        """

        if self.effect_radius <= 0:
            return pygame.Vector2()

        offset = pygame.Vector2(position) - self.position

        # Check if position is within the square bounds (using absolute distance on each axis)
        if abs(offset.x) > self.effect_radius or abs(offset.y) > self.effect_radius:
            return pygame.Vector2()

        # Uniform push force throughout the current
        return self.direction * self.strength

    def apply_to_player(self, player, delta_time: float, collision_system=None) -> pygame.Vector2:
        """Apply this current to a player and return the applied movement.

        The method accepts the existing Player object used by the project.
        It updates ``player.position`` and ``player.rect`` when the player is
        inside the current.  A zero/negative delta time is ignored.
        
        If collision_system is provided, collision checks are performed and
        movement is blocked if it would cause the player to intersect with
        solid level geometry (walls/obstacles).
        """

        if delta_time <= 0:
            return pygame.Vector2()

        force = self.get_force_at_position(player.position)
        movement = force * float(delta_time)

        if movement.length_squared() == 0:
            return movement

        # If collision system is available, check for collisions before applying movement
        if collision_system is not None:
            # Apply movement horizontally
            player.position.x += movement.x
            if hasattr(player, "rect"):
                player.rect.centerx = round(player.position.x)

            # Check for collision and revert if necessary
            if collision_system.check_collision(player.rect):
                player.position.x -= movement.x
                if hasattr(player, "rect"):
                    player.rect.centerx = round(player.position.x)

            # Apply movement vertically
            player.position.y += movement.y
            if hasattr(player, "rect"):
                player.rect.centery = round(player.position.y)

            # Check for collision and revert if necessary
            if collision_system.check_collision(player.rect):
                player.position.y -= movement.y
                if hasattr(player, "rect"):
                    player.rect.centery = round(player.position.y)
        else:
            # Fallback to simple movement if no collision system provided
            player.position += movement
            if hasattr(player, "rect"):
                player.rect.center = (
                    round(player.position.x),
                    round(player.position.y),
                )

        return movement

    def affects_position(self, position: pygame.Vector2) -> bool:
        """Return whether ``position`` is inside the current's square influence area."""

        if self.effect_radius <= 0:
            return False
        offset = pygame.Vector2(position) - self.position
        return abs(offset.x) <= self.effect_radius and abs(offset.y) <= self.effect_radius

    # ------------------------------------------------------------------
    # Entity update / rendering
    # ------------------------------------------------------------------

    def update(self, delta_time: float) -> None:
        """Update the current's animated visual effect.

        The current itself does not move; only the flow arrows animate.
        """

        if delta_time > 0:
            self._animation_time = (
                self._animation_time + delta_time
            ) % 1.0
            self._draw_visual()

    def _draw_visual(self) -> None:
        """Redraw a faint directional gradient with a travelling pulse."""

        self.image.fill((0, 0, 0, 0))

        if self.effect_radius <= 0:
            return

        centre = pygame.Vector2(self.image.get_width() / 2, self.image.get_height() / 2)
        half_size = max(1, int(self.effect_radius))
        rect = pygame.Rect(
            round(centre.x - half_size),
            round(centre.y - half_size),
            half_size * 2,
            half_size * 2,
        )

        self.image.set_clip(rect)
        pygame.draw.rect(
            self.image,
            (55, 145, 235, 10),
            rect,
        )

        perpendicular = pygame.Vector2(-self.direction.y, self.direction.x)
        flow_span = half_size * (abs(self.direction.x) + abs(self.direction.y))
        pulse_position = -flow_span + self._animation_time * flow_span * 2.0
        band_count = max(16, min(32, half_size // 4))
        band_width = flow_span * 2.0 / band_count

        for index in range(band_count):
            projection = -flow_span + (index + 0.5) * band_width
            distance = abs(projection - pulse_position)
            pulse = max(0.0, 1.0 - distance / max(flow_span * 0.42, 1.0))
            directional_fade = (projection + flow_span) / max(flow_span * 2.0, 1.0)
            alpha = int(5 + directional_fade * 7 + pulse * 28)
            strip_centre = centre + self.direction * projection
            strip_half_width = band_width * 0.75
            corners = [
                strip_centre - self.direction * strip_half_width - perpendicular * flow_span,
                strip_centre + self.direction * strip_half_width - perpendicular * flow_span,
                strip_centre + self.direction * strip_half_width + perpendicular * flow_span,
                strip_centre - self.direction * strip_half_width + perpendicular * flow_span,
            ]
            pygame.draw.polygon(
                self.image,
                (75, 175, 245, alpha),
                [(round(point.x), round(point.y)) for point in corners],
            )

        self.image.set_clip(None)

    def draw(self, screen: pygame.Surface, camera=None) -> None:
        """Draw the current using the game's world-to-screen camera API."""

        if camera is None:
            draw_position = self.position
        else:
            draw_position = camera.world_to_screen(self.position)

        screen_rect = self.image.get_rect(
            center=(round(draw_position.x), round(draw_position.y))
        )
        screen.blit(self.image, screen_rect)
