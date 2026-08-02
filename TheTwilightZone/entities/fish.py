"""
Fish entity for The Twilight Zone game.

Fish are passive creatures that spawn in groups and move around the cave.
"""

from __future__ import annotations

import pygame


class Fish(pygame.sprite.Sprite):
    """
    Represents a fish entity in the cave.
    
    Fish are spawned in groups via fish_spawn level elements.
    They move in patterns and do not interact with the player.
    """
    
    def __init__(self, position: tuple[float, float], spawn_id: str = ""):
        """
        Initialize a fish at the given position.
        
        Args:
            position: (x, y) coordinates in world space
            spawn_id: ID of the spawn point that created this fish
        """
        super().__init__()
        
        self.position = pygame.Vector2(position)
        self.spawn_id = spawn_id
        
        # Placeholder image - a small circle
        self.image = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (70, 200, 160), (8, 8), 8)
        
        self.rect = self.image.get_rect(center=self.position)
        
        # Movement properties
        self.velocity = pygame.Vector2(0, 0)
        self.max_speed = 50.0
        self.acceleration = 0.0
        
    def update(self, delta_time: float) -> None:
        """
        Update the fish's position and behavior.
        
        Args:
            delta_time: Time elapsed since last frame in seconds
        """
        # TODO: Implement fish AI and movement
        pass
    
    def draw(self, screen: pygame.Surface) -> None:
        """
        Draw the fish on the given surface.
        
        Args:
            screen: The surface to draw on
        """
        screen.blit(self.image, self.rect)
