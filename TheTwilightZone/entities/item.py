"""
Item entity for The Twilight Zone game.

Items are collectible objects that provide benefits to the player.
"""

from __future__ import annotations

import pygame


class Item(pygame.sprite.Sprite):
    """
    Represents a collectible item in the cave.
    
    Items can restore health, oxygen, or provide other benefits.
    """
    
    ITEM_HEALTH = "health"
    ITEM_OXYGEN = "oxygen"
    ITEM_ARTIFACT = "artifact"
    
    def __init__(self, position: tuple[float, float], item_type: str = ITEM_HEALTH, item_id: str = ""):
        """
        Initialize an item at the given position.
        
        Args:
            position: (x, y) coordinates in world space
            item_type: Type of item (health, oxygen, artifact)
            item_id: Unique identifier for this item
        """
        super().__init__()
        
        self.position = pygame.Vector2(position)
        self.item_type = item_type
        self.item_id = item_id
        
        # Create placeholder visual based on type
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        
        if item_type == self.ITEM_HEALTH:
            # Red cross for health
            pygame.draw.circle(self.image, (255, 100, 100), (10, 10), 10)
            pygame.draw.line(self.image, (255, 255, 255), (10, 5), (10, 15), 2)
            pygame.draw.line(self.image, (255, 255, 255), (5, 10), (15, 10), 2)
            
        elif item_type == self.ITEM_OXYGEN:
            # Blue bubble for oxygen
            pygame.draw.circle(self.image, (100, 200, 255), (10, 10), 10)
            pygame.draw.circle(self.image, (150, 220, 255), (10, 10), 6)
            
        elif item_type == self.ITEM_ARTIFACT:
            # Yellow star for artifact
            pygame.draw.circle(self.image, (220, 200, 70), (10, 10), 10)
            pygame.draw.polygon(self.image, (255, 255, 150), [
                (10, 3), (13, 9), (20, 10), (15, 15), (17, 22), (10, 17), (3, 22), (5, 15), (0, 10), (7, 9)
            ])
        
        self.rect = self.image.get_rect(center=self.position)
        
        # Item properties
        self.value = self._get_default_value()
        self.collected = False
        
    def _get_default_value(self) -> float:
        """Get default value for this item type."""
        if self.item_type == self.ITEM_HEALTH:
            return 25.0
        elif self.item_type == self.ITEM_OXYGEN:
            return 30.0
        elif self.item_type == self.ITEM_ARTIFACT:
            return 1.0
        return 0.0
    
    def update(self, delta_time: float) -> None:
        """
        Update the item's state (e.g., bobbing animation).
        
        Args:
            delta_time: Time elapsed since last frame in seconds
        """
        # TODO: Implement bobbing or other animations
        pass
    
    def draw(self, screen: pygame.Surface) -> None:
        """
        Draw the item on the given surface.
        
        Args:
            screen: The surface to draw on
        """
        if not self.collected:
            screen.blit(self.image, self.rect)
