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
        strength: Maximum push speed/force applied at the centre.
        effect_radius: Radius of the current's influence in world pixels.

    ``strength`` is treated as pixels-per-second when used through
    :meth:`apply_to_player`.  ``get_force_at_position`` retains the force
    vector API used by the original placeholder, making the entity easy to
    integrate with other movement systems.
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

        The push is strongest at the centre and smoothly falls to zero at
        ``effect_radius``. Positions outside the current receive no force.
        """

        if self.effect_radius <= 0:
            return pygame.Vector2()

        offset = pygame.Vector2(position) - self.position
        distance = offset.length()

        if distance >= self.effect_radius:
            return pygame.Vector2()

        # Smooth falloff avoids an abrupt speed change at the edge.
        ratio = 1.0 - (distance / self.effect_radius)
        ratio = ratio * ratio * (3.0 - 2.0 * ratio)

        return self.direction * (self.strength * ratio)

    def apply_to_player(self, player, delta_time: float) -> pygame.Vector2:
        """Apply this current to a player and return the applied movement.

        The method accepts the existing Player object used by the project.
        It updates ``player.position`` and ``player.rect`` when the player is
        inside the current.  A zero/negative delta time is ignored.
        """

        if delta_time <= 0:
            return pygame.Vector2()

        force = self.get_force_at_position(player.position)
        movement = force * float(delta_time)

        if movement.length_squared() == 0:
            return movement

        player.position += movement
        if hasattr(player, "rect"):
            player.rect.center = (
                round(player.position.x),
                round(player.position.y),
            )

        return movement

    def affects_position(self, position: pygame.Vector2) -> bool:
        """Return whether ``position`` is inside the current's influence."""

        if self.effect_radius <= 0:
            return False
        return self.position.distance_to(position) < self.effect_radius

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
        """Redraw the current's simple debug-friendly flow visual."""

        self.image.fill((0, 0, 0, 0))

        if self.effect_radius <= 0:
            return

        centre = pygame.Vector2(self.image.get_width() / 2, self.image.get_height() / 2)
        radius = max(1, int(self.effect_radius))

        pygame.draw.circle(
            self.image,
            (60, 140, 220, 55),
            (round(centre.x), round(centre.y)),
            radius,
        )
        pygame.draw.circle(
            self.image,
            (100, 190, 245, 130),
            (round(centre.x), round(centre.y)),
            radius,
            2,
        )

        # Three arrows communicate the flow direction. Their phase changes
        # over time so the current is visibly active rather than a dead blob.
        perpendicular = pygame.Vector2(-self.direction.y, self.direction.x)
        base_distance = radius * 0.45
        arrow_length = max(8.0, radius * 0.35)
        phase_offset = (self._animation_time - 0.5) * radius * 0.5

        for index in range(3):
            lateral = (index - 1) * radius * 0.32
            centre_line = (
                centre
                + perpendicular * lateral
                - self.direction * phase_offset
            )
            start = centre_line - self.direction * (arrow_length * 0.5)
            end = centre_line + self.direction * (arrow_length * 0.5)

            pygame.draw.line(
                self.image,
                (130, 215, 255, 190),
                (round(start.x), round(start.y)),
                (round(end.x), round(end.y)),
                max(1, round(radius / 18)),
            )

            head_size = max(4.0, radius * 0.12)
            left = end - self.direction * head_size + perpendicular * head_size * 0.55
            right = end - self.direction * head_size - perpendicular * head_size * 0.55
            pygame.draw.polygon(
                self.image,
                (130, 215, 255, 190),
                [
                    (round(end.x), round(end.y)),
                    (round(left.x), round(left.y)),
                    (round(right.x), round(right.y)),
                ],
            )

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
