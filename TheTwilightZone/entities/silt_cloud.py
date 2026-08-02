"""
Silt Cloud entity for The Twilight Zone game.

Silt clouds are environmental obstacles that reduce visibility and movement.
"""

from __future__ import annotations

import pygame


class SiltCloud(pygame.sprite.Sprite):
    """
    Represents a silt cloud in the cave.
    
    Silt clouds obscure vision and slow player movement.
    """
    
    def __init__(self, position: tuple[float, float], cloud_id: str = ""):
        """
        Initialize a silt cloud at the given position.
        
        Args:
            position: (x, y) coordinates in world space
            cloud_id: Unique identifier for this cloud
        """
        super().__init__()
        
        self.position = pygame.Vector2(position)
        self.cloud_id = cloud_id
        
        # Placeholder visual - a gray semi-transparent circle
        self.radius = 40
        self.image = pygame.Surface((100, 100), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (120, 120, 120, 128), (50, 50), 40)
        pygame.draw.circle(self.image, (140, 140, 140, 96), (40, 40), 30)
        pygame.draw.circle(self.image, (100, 100, 100, 96), (60, 60), 30)
        
        self.rect = self.image.get_rect(center=self.position)
        
        # Effect properties
        self.visibility_reduction = 0.3  # Reduces visibility by 30%
        self.speed_reduction = 0.8  # Reduces player speed by 20%
        self.effect_radius = 80.0
        
    def update(self, delta_time: float) -> None:
        """
        Update the silt cloud's state (e.g., dispersal).
        
        Args:
            delta_time: Time elapsed since last frame in seconds
        """
        # TODO: Implement cloud dispersal animation
        pass
    
    def draw(self, screen: pygame.Surface) -> None:
        """
        Draw the silt cloud on the given surface.
        
        Args:
            screen: The surface to draw on
        """
        screen.blit(self.image, self.rect)
