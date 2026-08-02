from __future__ import annotations

import pygame


class Camera:
    """
    Controls the portion of the world currently visible on screen.

    The camera stores its position in world coordinates. It converts
    world coordinates into screen coordinates when rendering.
    """

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
    ):
        """
        Initialise the camera.

        Args:
            screen_width: Width of the game window.
            screen_height: Height of the game window.
        """

        self.screen_width = screen_width
        self.screen_height = screen_height

        self.position = pygame.Vector2(0, 0)

    def update(
        self,
        target_position: pygame.Vector2,
        world_bounds: pygame.Rect,
    ):
        """
        Update the camera to follow the target while remaining
        inside the complete stitched world.
        """

        target_x = (
            target_position.x
            - self.screen_width / 2
        )

        target_y = (
            target_position.y
            - self.screen_height / 2
        )

        # Clamp camera to the actual world bounds while keeping
        # horizontal follow behavior intact.
        self.position.x = max(
            world_bounds.left,
            target_x,
        )

        self.position.y = max(
            world_bounds.top,
            min(
                target_y,
                world_bounds.bottom
                - self.screen_height,
            ),
        )

    def world_to_screen(
        self,
        world_position: pygame.Vector2
    ) -> pygame.Vector2:
        """
        Convert a world-space position into screen-space coordinates.
        """

        return (
            pygame.Vector2(world_position)
            - self.position
        )