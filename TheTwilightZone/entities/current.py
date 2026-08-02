"""
Current entity for The Twilight Zone game.

Currents are environmental forces that push the player in a direction.
"""

from __future__ import annotations

import pygame


class Current(pygame.sprite.Sprite):
    """
    Represents a water current in the cave.
    
    Currents apply a pushing force to the player when they enter the current's area.
    """
    
    def __init__(self, position: tuple[float, float], direction: tuple[float, float] = (1.0, 0.0), 
                 current_id: str = ""):
        """
        Initialize a current at the given position.
        
        Args:
            position: (x, y) coordinates in world space
            direction: (x, y) direction vector for the current
            current_id: Unique identifier for this current
        """
        super().__init__()
        
        self.position = pygame.Vector2(position)
        self.current_id = current_id
        
        # Normalize direction
        self.direction = pygame.Vector2(direction)
        if self.direction.length() > 0:
            self.direction = self.direction.normalize()
        else:
            self.direction = pygame.Vector2(1, 0)
        
        # Placeholder visual - an arrow showing current direction
        self.radius = 30
        self.image = pygame.Surface((70, 70), pygame.SRCALPHA)
        
        # Draw circle for current area
        pygame.draw.circle(self.image, (60, 130, 220, 128), (35, 35), 30)
        
        # Draw arrow pointing in direction
        angle = self.direction.angle_to((1, 0))
        # Draw arrow (simplified)
        pygame.draw.line(self.image, (100, 180, 255), (35, 35), 
                        (35 + self.direction.x * 20, 35 + self.direction.y * 20), 3)
        
        self.rect = self.image.get_rect(center=self.position)
        
        # Current properties
        self.strength = 100.0  # Force applied to player
        self.effect_radius = 60.0
        
    def update(self, delta_time: float) -> None:
        """
        Update the current's state.
        
        Args:
            delta_time: Time elapsed since last frame in seconds
        """
        # Currents are static, but may have visual effects
        pass
    
    def draw(self, screen: pygame.Surface) -> None:
        """
        Draw the current on the given surface.
        
        Args:
            screen: The surface to draw on
        """
        screen.blit(self.image, self.rect)
    
    def get_force_at_position(self, position: pygame.Vector2) -> pygame.Vector2:
        """
        Calculate the force applied by this current at a given position.
        
        Args:
            position: Position to check
            
        Returns:
            Force vector
        """
        distance = self.position.distance_to(position)
        
        if distance > self.effect_radius:
            return pygame.Vector2(0, 0)
        
        # Force decreases with distance
        ratio = 1.0 - (distance / self.effect_radius)
        return self.direction * self.strength * ratio
