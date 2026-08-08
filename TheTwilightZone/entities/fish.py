"""
Fish entity for The Twilight Zone.

Fish are hostile creatures that patrol cave areas and chase the
player when the player enters their detection range.
"""

from __future__ import annotations

import math
import pygame


class Fish(pygame.sprite.Sprite):
    """
    Represents one hostile fish.

    Fish normally move along a straight patrol path. When the player
    enters the detection radius, the fish moves towards the player.

    Gameplay values are supplied through the constructor so level
    data can control fish behaviour without changing this class.
    """

    def __init__(
        self,
        position: tuple[float, float],
        spawn_id: str = "",
        patrol_direction: tuple[float, float] = (1, 0),
        patrol_distance: float = 150.0,
        speed: float = 70.0,
        detection_range: float = 180.0,
        damage: int = 10,
    ):
        super().__init__()

        # --------------------------------------------------------------
        # Identity / world position
        # --------------------------------------------------------------

        self.position = pygame.Vector2(position)
        self.spawn_id = spawn_id

        # --------------------------------------------------------------
        # Visual
        # --------------------------------------------------------------

        # Temporary pixel-art style fish.
        # Replace this surface with the final sprite later.
        self.image = pygame.Surface(
            (32, 20),
            pygame.SRCALPHA,
        )

        # Body
        pygame.draw.ellipse(
            self.image,
            (70, 200, 160),
            pygame.Rect(5, 3, 22, 14),
        )

        # Tail
        pygame.draw.polygon(
            self.image,
            (50, 160, 135),
            [
                (7, 10),
                (0, 3),
                (0, 17),
            ],
        )

        # Eye
        pygame.draw.circle(
            self.image,
            (10, 20, 20),
            (23, 7),
            2,
        )

        self.rect = self.image.get_rect(
            center=(
                round(self.position.x),
                round(self.position.y),
            )
        )

        # --------------------------------------------------------------
        # Movement
        # --------------------------------------------------------------

        self.velocity = pygame.Vector2()

        self.speed = float(speed)

        # Normalised direction of the straight patrol.
        self.patrol_direction = pygame.Vector2(
            patrol_direction
        )

        if self.patrol_direction.length_squared() == 0:
            self.patrol_direction = pygame.Vector2(1, 0)

        else:
            self.patrol_direction = (
                self.patrol_direction.normalize()
            )

        # Position at the start of the patrol.
        self.patrol_origin = self.position.copy()

        self.patrol_distance = float(
            max(0.0, patrol_distance)
        )

        # Detection / combat
        self.detection_range = float(
            max(0.0, detection_range)
        )

        self.damage = int(
            max(0, damage)
        )

        # Used to reverse the patrol direction.
        self.patrol_direction_sign = 1.0

        # Prevent damage from happening every single frame.
        self.damage_cooldown = 0.75
        self.damage_timer = 0.0

    # ==================================================================
    # AI
    # ==================================================================

    def update(
        self,
        delta_time: float,
        player_position: pygame.Vector2 | None = None,
    ) -> bool:
        """
        Update fish movement.

        Returns:
            True if the fish is currently colliding with the player.
        """

        if delta_time <= 0:
            return False

        self.damage_timer = max(
            0.0,
            self.damage_timer - delta_time,
        )

        # --------------------------------------------------------------
        # Detect player
        # --------------------------------------------------------------

        player_detected = False

        if player_position is not None:

            distance_to_player = (
                self.position.distance_to(
                    player_position
                )
            )

            player_detected = (
                distance_to_player
                <= self.detection_range
            )

        # --------------------------------------------------------------
        # Chase behaviour
        # --------------------------------------------------------------

        if player_detected:

            direction = (
                pygame.Vector2(player_position)
                - self.position
            )

            if direction.length_squared() > 0:

                direction = direction.normalize()

                self.velocity = (
                    direction * self.speed
                )

        # --------------------------------------------------------------
        # Patrol behaviour
        # --------------------------------------------------------------

        else:

            self.velocity = (
                self.patrol_direction
                * self.patrol_direction_sign
                * self.speed
            )

        # --------------------------------------------------------------
        # Move
        # --------------------------------------------------------------

        self.position += (
            self.velocity * delta_time
        )

        # --------------------------------------------------------------
        # Reverse at patrol endpoints
        # --------------------------------------------------------------

        distance_from_origin = (
            self.position - self.patrol_origin
        ).dot(self.patrol_direction)

        if not player_detected:

            if abs(distance_from_origin) >= self.patrol_distance:

                # Clamp the fish back onto the patrol line.
                distance_from_origin = (
                    self.patrol_distance
                    * self.patrol_direction_sign
                )

                self.position = (
                    self.patrol_origin
                    + (
                        self.patrol_direction
                        * distance_from_origin
                    )
                )

                self.patrol_direction_sign *= -1.0

        # --------------------------------------------------------------
        # Update hitbox
        # --------------------------------------------------------------

        self.rect.center = (
            round(self.position.x),
            round(self.position.y),
        )

        return False

    # ==================================================================
    # Collision
    # ==================================================================

    def check_player_collision(
        self,
        player_rect: pygame.Rect,
    ) -> bool:
        """
        Check whether the fish is touching the player.

        A cooldown prevents a single collision from damaging the
        player every frame.
        """

        if not self.rect.colliderect(player_rect):
            return False

        if self.damage_timer > 0:
            return False

        self.damage_timer = self.damage_cooldown

        return True

    # ==================================================================
    # Rendering
    # ==================================================================

    def draw(
        self,
        screen: pygame.Surface,
        camera,
    ) -> None:
        """
        Draw the fish using world-to-screen camera conversion.
        """

        screen_position = (
            camera.world_to_screen(
                self.position
            )
        )

        screen_rect = self.image.get_rect(
            center=(
                round(screen_position.x),
                round(screen_position.y),
            )
        )

        screen.blit(
            self.image,
            screen_rect,
        )