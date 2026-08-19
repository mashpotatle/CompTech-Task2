import json
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame

from assets.o2_tank_model import create_oxygen_tank_sprite
from game.game import Game
from levels.cave_section import LevelElement
from levels.level_loader import LevelLoader


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


def test_item_pickup_uses_the_section_world_offset():
    pygame.init()
    game = Game()

    item = LevelElement(
        element_id="item_001",
        element_type="item",
        position=pygame.Vector2(100, 100),
        properties={"item_type": "med_kit", "pickup_radius": 48.0},
    )
    section = game.level_manager.sections[0]
    section.section.elements = [item]
    section.world_offset = pygame.Vector2(500, 0)
    game.player.position = pygame.Vector2(600, 100)
    game.player.rect.center = (600, 100)

    game.check_item_pickups()

    assert item.properties.get("collected") is True
    assert game.inventory.slots[0] == "med_kit"


def test_level_loader_randomizes_item_rotation(tmp_path, monkeypatch):
    loader = LevelLoader(tmp_path)
    monkeypatch.setattr("levels.level_loader.random.uniform", lambda a, b: 123.0)

    section_data = {
        "id": "section_01",
        "name": "section_01",
        "entry": {"position": [0, 0], "direction": "right"},
        "exit": {"position": [400, 0], "direction": "right"},
        "elements": [
            {
                "id": "item_001",
                "type": "item",
                "position": [100, 100],
                "properties": {"item_type": "oxygen_tank"},
            }
        ],
    }
    (tmp_path / "section_01.json").write_text(json.dumps(section_data), encoding="utf-8")

    section = loader.load_section("section_01.json")

    assert section.elements[0].properties["rotation"] == 123.0


def test_dropped_item_gets_random_rotation(monkeypatch):
    pygame.init()
    game = Game()
    monkeypatch.setattr(game.inventory, "drop_active", lambda: "med_kit")
    monkeypatch.setattr(game.level_manager, "get_current_section", lambda: object())

    captured = {}

    def fake_add_dropped_item(section, item):
        captured["section"] = section
        captured["item"] = item

    monkeypatch.setattr(game.level_manager, "add_dropped_item", fake_add_dropped_item)
    monkeypatch.setattr("game.game.random.uniform", lambda a, b: 321.0)

    game.drop_active_item()

    assert captured["item"].properties["rotation"] == 321.0


def test_oxygen_tank_sprite_preserves_tall_aspect_ratio():
    pygame.init()
    pygame.display.set_mode((1, 1))

    sprite = create_oxygen_tank_sprite(70, 70)
    opaque_bounds = sprite.get_bounding_rect()

    assert sprite.get_size() == (70, 70)
    assert opaque_bounds.height == 70
    assert opaque_bounds.width < opaque_bounds.height
