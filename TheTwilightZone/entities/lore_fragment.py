"""
Lore Fragment entity for The Twilight Zone game.

Lore fragments are collectible story elements scattered throughout the cave.
"""

from __future__ import annotations

import pygame


class LoreFragment(pygame.sprite.Sprite):
    """
    Represents a lore fragment or story element in the cave.
    
    Lore fragments can be collected to reveal story information.
    """
    
    def __init__(self, position: tuple[float, float], fragment_id: str = "", content: str = ""):
        """
        Initialize a lore fragment at the given position.
        
        Args:
            position: (x, y) coordinates in world space
            fragment_id: Unique identifier for this fragment
            content: The text content of this lore fragment
        """
        super().__init__()
        
        self.position = pygame.Vector2(position)
        self.fragment_id = fragment_id
        self.content = content
        
        # Placeholder visual - a golden scroll-like object
        self.image = pygame.Surface((30, 40), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (220, 200, 70), (5, 5, 20, 30))
        pygame.draw.rect(self.image, (255, 240, 150), (7, 8, 16, 26))
        pygame.draw.line(self.image, (200, 180, 50), (8, 12), (22, 12), 1)
        pygame.draw.line(self.image, (200, 180, 50), (8, 17), (22, 17), 1)
        pygame.draw.line(self.image, (200, 180, 50), (8, 22), (22, 22), 1)
        
        self.rect = self.image.get_rect(center=self.position)
        
        # Fragment properties
        self.collected = False
        self.animation_time = 0.0
        self.bob_height = 10.0
        self.bob_speed = 2.0
        
    def update(self, delta_time: float) -> None:
        """
        Update the lore fragment's state (e.g., bobbing animation).
        
        Args:
            delta_time: Time elapsed since last frame in seconds
        """
        if not self.collected:
            self.animation_time += delta_time
            
            # Simple bobbing animation
            import math
            bob_offset = math.sin(self.animation_time * self.bob_speed) * self.bob_height
            self.rect.centery = int(self.position.y + bob_offset)
    
    def draw(self, screen: pygame.Surface) -> None:
        """
        Draw the lore fragment on the given surface.
        
        Args:
            screen: The surface to draw on
        """
        if not self.collected:
            screen.blit(self.image, self.rect)
    
    def get_lore_text(self) -> str:
        """
        Get the lore text for this fragment.
        
        Returns:
            The content string of this lore fragment
        """
        return self.content
