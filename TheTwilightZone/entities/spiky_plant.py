"""
Spiky Plant entity for The Twilight Zone game.

Spiky plants are environmental hazards with sharp protrusions.
"""

from __future__ import annotations

import pygame


class SpikyPlant(pygame.sprite.Sprite):
    """
    Represents a spiky plant hazard in the cave.
    
    Spiky plants have thorns that deal damage when the player touches them.
    """
    
    def __init__(self, position: tuple[float, float], plant_id: str = ""):
        """
        Initialize a spiky plant at the given position.
        
        Args:
            position: (x, y) coordinates in world space
            plant_id: Unique identifier for this plant
        """
        super().__init__()
        
        self.position = pygame.Vector2(position)
        self.plant_id = plant_id
        
        # Placeholder visual - a green circle with spikes
        self.radius = 20
        self.image = pygame.Surface((50, 50), pygame.SRCALPHA)
        
        # Draw plant body
        pygame.draw.circle(self.image, (100, 180, 100), (25, 25), 15)
        
        # Draw spikes
        spike_count = 8
        import math
        for i in range(spike_count):
            angle = (360 / spike_count) * i
            rad = math.radians(angle)
            x1 = 25 + math.cos(rad) * 15
            y1 = 25 + math.sin(rad) * 15
            x2 = 25 + math.cos(rad) * 25
            y2 = 25 + math.sin(rad) * 25
            pygame.draw.line(self.image, (150, 220, 150), (x1, y1), (x2, y2), 2)
        
        self.rect = self.image.get_rect(center=self.position)
        
        # Damage properties
        self.damage_per_hit = 15.0
        self.collision_radius = 25.0
        
    def update(self, delta_time: float) -> None:
        """
        Update the spiky plant's state.
        
        Args:
            delta_time: Time elapsed since last frame in seconds
        """
        # TODO: Implement animations
        pass
    
    def draw(self, screen: pygame.Surface) -> None:
        """
        Draw the spiky plant on the given surface.
        
        Args:
            screen: The surface to draw on
        """
        screen.blit(self.image, self.rect)
