"""
Player entity for The Twilight Zone.

The Player class manages the diver's position, movement, and basic
rendering. Gameplay systems such as health, oxygen, and inventory
will be added in later development stages.
"""

import pygame

from settings import SCREEN_HEIGHT, SCREEN_WIDTH, PLAYER_WIDTH, PLAYER_HEIGHT
from systems.collision import CollisionSystem

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

        # Temporary player dimensions used until the player sprite
        # is implemented.
        self.width = 40
        self.height = 40

        # Create a rectangular hitbox centred around the player's
        # position. This will later be used for collision detection.
        self.rect = pygame.Rect(
            0,
            0,
            PLAYER_WIDTH,
            PLAYER_HEIGHT
        )

        self.rect.center = (
            round(self.position.x),
            round(self.position.y)
        )

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

        # Horizontal movement.
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.velocity.x -= 1

        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.velocity.x += 1

        # Vertical movement.
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.velocity.y -= 1

        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.velocity.y += 1

        # Normalising prevents diagonal movement from being faster
        # than movement in a single direction.
        if self.velocity.length_squared() > 0:
            self.velocity = self.velocity.normalize()

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
            self.rect.width,
            self.rect.height,
        )

        # Centre the visual representation on the player's screen position.
        screen_rect.center = (
            round(screen_position.x),
            round(screen_position.y),
        )

        # Temporary player representation.
        pygame.draw.rect(
            screen,
            (40, 180, 220),
            screen_rect,
        )