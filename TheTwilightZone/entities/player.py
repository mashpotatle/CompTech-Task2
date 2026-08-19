"""
Player entity for The Twilight Zone.

The Player class manages the diver's position, movement, and basic
rendering. Gameplay systems such as health, oxygen, and inventory
will be added in later development stages.
"""

import pygame

from assets.player_model import create_player_sprite
from settings import SCREEN_HEIGHT, SCREEN_WIDTH, PLAYER_WIDTH, PLAYER_HEIGHT
from systems.collision import CollisionSystem
import math

class Player:
    """
    Represents the player-controlled diver.

    The player can move in four directions on a two-dimensional plane.
    Movement uses delta time so the player's speed remains consistent
    regardless of the current frame rate.
    """

    def __init__(self, position):
        """
        Initialise the player.

        Args:
            position: The player's starting position as an (x, y) pair.
        """

        # Vector2 provides efficient two-dimensional position and
        # velocity calculations and integrates well with Pygame.
        self.position = pygame.Vector2(position)

        # Stores the player's current movement direction and speed.
        self.velocity = pygame.Vector2()

        # Movement speed is measured in pixels per second.
        self.speed = 250

        # Keep visual sprite dimensions separate from collision dimensions.
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        self.collision_base_width = max(1, round(self.width / 1.5))
        self.collision_base_height = max(1, round(self.height / 1.5))
        self.facing = 1
        self.pitch_input = 0
        self.max_pitch_degrees = 18
        self.hitbox_max_pitch_degrees = 90

        # Create a rectangular hitbox centred around the player's
        # position. This will later be used for collision detection.
        self.rect = pygame.Rect(
            0,
            0,
            self.collision_base_width,
            self.collision_base_height,
        )

        self.rect.center = (
            round(self.position.x),
            round(self.position.y)
        )

        self._update_collision_rect_dimensions()

        # Health (temporary). A simple integer health pool for
        # environmental damage and entity attacks.
        self.health = 100
        # Tracks fractional damage between frames so slow damage-over-time
        # sources (e.g. thermal vents) aren't lost to integer truncation.
        self._damage_remainder = 0.0
        # Wobble visual state applied when inside a current.
        self.wobble_strength = 0.0
        self.wobble_timer = 0.0
        self._wobble_time = 0.0

        self.sprite = create_player_sprite(self.width, self.height)

    def handle_input(self):
        """
        Read keyboard input and calculate the player's movement direction.

        WASD and the arrow keys are both supported, as specified in the
        game design document.

        The movement vector is normalised so diagonal movement does not
        make the player move faster than horizontal or vertical movement.
        """

        keys = pygame.key.get_pressed()

        self.velocity.x = 0
        self.velocity.y = 0
        self.pitch_input = 0

        # Horizontal movement.
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.velocity.x -= 1

        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.velocity.x += 1

        # Vertical movement.
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.velocity.y -= 1
            self.pitch_input = -1

        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.velocity.y += 1
            self.pitch_input = 1

        # Normalising prevents diagonal movement from being faster
        # than movement in a single direction.
        if self.velocity.length_squared() > 0:
            self.velocity = self.velocity.normalize()
            self.facing = 1 if self.velocity.x >= 0 else -1

        self._update_collision_rect_dimensions()

    def _get_pitch_angle(self) -> float:
        """Return player pitch in degrees, corrected for facing direction."""

        return -self.pitch_input * self.max_pitch_degrees * self.facing

    def _get_hitbox_pitch_angle(self) -> float:
        """Return hitbox pitch in degrees for collision shape projection."""

        return self.pitch_input * self.hitbox_max_pitch_degrees

    def _update_collision_rect_dimensions(self) -> None:
        """Resize collision rect to match pitched hitbox projection."""

        angle = math.radians(abs(self._get_hitbox_pitch_angle()))
        cos_angle = abs(math.cos(angle))
        sin_angle = abs(math.sin(angle))

        rotated_width = max(
            1,
            round(
                self.collision_base_width * cos_angle
                + self.collision_base_height * sin_angle
            ),
        )
        rotated_height = max(
            1,
            round(
                self.collision_base_width * sin_angle
                + self.collision_base_height * cos_angle
            ),
        )

        self.rect.size = (
            rotated_width,
            rotated_height,
        )
        self.rect.center = (
            round(self.position.x),
            round(self.position.y),
        )

    def update(self, delta_time, collision_system):
        """
        Update player movement and resolve cave collisions.

        Horizontal and vertical movement are resolved independently.
        This allows the player to slide along cave walls rather than
        becoming completely stuck when moving diagonally into a wall.

        Args:
            delta_time: Time in seconds since the previous frame.
            collision_system: CollisionSystem used to check cave walls.
        """

        movement = (
            self.velocity
            * self.speed
            * delta_time
        )

        self._update_collision_rect_dimensions()

        # ---------------------------------------------------------------
        # Horizontal Movement
        # ---------------------------------------------------------------

        self.position.x += movement.x
        self.rect.centerx = round(self.position.x)

        if collision_system.check_collision(self.rect):
            # Undo the movement if it caused a collision.
            self.position.x -= movement.x
            self.rect.centerx = round(self.position.x)

        # ---------------------------------------------------------------
        # Vertical Movement
        # ---------------------------------------------------------------

        self.position.y += movement.y
        self.rect.centery = round(self.position.y)

        if collision_system.check_collision(self.rect):
            # Undo the movement if it caused a collision.
            self.position.y -= movement.y
            self.rect.centery = round(self.position.y)

        # Update wobble visual timer
        if delta_time is not None and delta_time > 0:
            self._wobble_time += delta_time
            if self.wobble_timer > 0:
                self.wobble_timer = max(0.0, self.wobble_timer - delta_time)
                if self.wobble_timer == 0.0:
                    self.wobble_strength = 0.0

        # ---------------------------------------------------------------
        # Horizontal Movement
        # ---------------------------------------------------------------

        self.position.x += movement.x
        self.rect.centerx = round(self.position.x)

        if collision_system.check_collision(self.rect):
            # Undo the movement if it caused a collision.
            self.position.x -= movement.x
            self.rect.centerx = round(self.position.x)

        # ---------------------------------------------------------------
        # Vertical Movement
        # ---------------------------------------------------------------

        self.position.y += movement.y
        self.rect.centery = round(self.position.y)

        if collision_system.check_collision(self.rect):
            # Undo the movement if it caused a collision.
            self.position.y -= movement.y
            self.rect.centery = round(self.position.y)

    def keep_on_screen(self):
        """
        Prevent the player from moving outside the game window.

        This is temporary boundary handling. It will eventually be
        replaced or supplemented by cave-wall collision detection.
        """

        half_width = self.rect.width / 2
        half_height = self.rect.height / 2

        self.position.x = max(
            half_width,
            min(self.position.x, SCREEN_WIDTH - half_width),
        )

        self.position.y = max(
            half_height,
            min(self.position.y, SCREEN_HEIGHT - half_height),
        )

        self.rect.center = self.position

    def draw(
        self,
        screen: pygame.Surface,
        camera,
    ) -> None:
        """
        Draw the player using the camera's world-to-screen transformation.

        The player's position and collision rectangle remain in world
        coordinates. Only the temporary rendering rectangle is converted
        into screen coordinates.
        """

        # Convert the player's world-space centre to screen coordinates.
        screen_position = camera.world_to_screen(
            self.position
        )

        # Create a temporary rectangle for rendering.
        # This does not modify the player's world-space collision rectangle.
        screen_rect = pygame.Rect(
            0,
            0,
            self.width,
            self.height,
        )

        # Centre the visual representation on the player's screen position.
        wobble_offset_x = 0.0
        wobble_offset_y = 0.0

        if self.wobble_strength > 0.0:
            wobble_offset_x = math.sin(self._wobble_time * 18.0) * (self.wobble_strength * 6.0)
            wobble_offset_y = math.sin(self._wobble_time * 24.0) * (self.wobble_strength * 3.0)

        screen_rect.center = (
            round(screen_position.x + wobble_offset_x),
            round(screen_position.y + wobble_offset_y),
        )

        sprite = self.sprite
        if self.facing < 0:
            sprite = pygame.transform.flip(self.sprite, True, False)

        pitch_angle = self._get_pitch_angle()
        if pitch_angle != 0:
            sprite = pygame.transform.rotate(sprite, pitch_angle)

        sprite_rect = sprite.get_rect(center=screen_rect.center)
        screen.blit(sprite, sprite_rect)

    def apply_damage(self, amount: float) -> None:
        """Reduce player health by `amount` and clamp at zero.

        Fractional amounts accumulate across calls so continuous, sub-1
        per-frame damage (like thermal vent heat) still adds up over time.
        """

        try:
            damage = float(amount)
        except Exception:
            return

        if damage <= 0:
            return

        self._damage_remainder += damage
        whole_damage = int(self._damage_remainder)
        if whole_damage > 0:
            self._damage_remainder -= whole_damage
            self.health = max(0, self.health - whole_damage)

    def add_wobble(self, strength: float, duration: float) -> None:
        """Increase wobble visual effect with given `strength` and `duration`.

        Strength is a small scalar (e.g. 0.0-2.0). Duration is seconds.
        """

        try:
            s = float(strength)
            d = float(duration)
        except Exception:
            return

        # Keep the strongest recent wobble and the longest duration
        self.wobble_strength = max(self.wobble_strength, s)
        self.wobble_timer = max(self.wobble_timer, d)