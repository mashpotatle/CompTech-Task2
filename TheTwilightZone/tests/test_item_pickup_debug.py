import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from game.game import Game
from levels.cave_section import LevelElement


def test_item_pickup_marks_world_item_collected_and_hides_it():
    pygame.init()
    game = Game()

    item = LevelElement(
        element_id="item_001",
        element_type="item",
        position=pygame.Vector2(100, 100),
        properties={"item_type": "oxygen_tank", "pickup_radius": 48.0},
    )
    game.level_manager.sections[0].section.elements = [item]
    game.player.position = pygame.Vector2(100, 100)
    game.player.rect.center = (100, 100)

    game.check_item_pickups()

    assert item.properties.get("collected") is True
    assert item.properties.get("in_inventory") is True
    assert game.inventory.active_item is not None or game.inventory.slots[0] == "oxygen_tank"
