"""
Thermal Vent entity for The Twilight Zone game.

Thermal vents are environmental hazards that deal damage to the player.
"""

from __future__ import annotations

import pygame


class ThermalVent(pygame.sprite.Sprite):
    """
    Represents a thermal vent hazard in the cave.
    
    Thermal vents emit heat that damages the player when touched.
    They have a visual effect and a damage radius.
    """
    
    def __init__(self, position: tuple[float, float], vent_id: str = ""):
        """
        Initialize a thermal vent at the given position.
        
        Args:
            position: (x, y) coordinates in world space
            vent_id: Unique identifier for this vent
        """
        super().__init__()
        
        self.position = pygame.Vector2(position)
        self.vent_id = vent_id
        
        # Placeholder visual - a red circle
        self.radius = 30
        self.image = pygame.Surface((60, 60), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (220, 90, 40), (30, 30), 30)
        pygame.draw.circle(self.image, (255, 150, 80), (30, 30), 20)
        
        self.rect = self.image.get_rect(center=self.position)
        
        # Damage properties
        self.damage_per_second = 10.0
        self.damage_radius = 60.0
        
    def update(self, delta_time: float) -> None:
        """
        Update the thermal vent's state (e.g., animation).
        
        Args:
            delta_time: Time elapsed since last frame in seconds
        """
        # TODO: Implement particle effects
        pass
    
    def draw(self, screen: pygame.Surface) -> None:
        """
        Draw the thermal vent on the given surface.
        
        Args:
            screen: The surface to draw on
        """
        screen.blit(self.image, self.rect)
    
    def get_damage_at_distance(self, distance: float) -> float:
        """
        Calculate damage dealt at a given distance from the vent.
        
        Args:
            distance: Distance from vent center
            
        Returns:
            Damage value (0 if outside damage radius)
        """
        if distance > self.damage_radius:
            return 0.0
        
        # Linear falloff
        ratio = 1.0 - (distance / self.damage_radius)
        return self.damage_per_second * ratio
