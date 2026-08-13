import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from editor import LevelEditor
from model import Element


def test_selected_element_can_be_dragged_by_world_delta():
    editor = LevelEditor()
    editor.camera = pygame.Vector2(0, 0)
    editor.zoom = 1.0
    element = Element("item_001", "item", 100, 100, properties={"pickup_radius": 48.0})
    editor.level.elements = [element]
    editor.selected = element

    editor.begin_drag_selected(pygame.Vector2(100, 100))
    editor.move_dragged_element(pygame.Vector2(140, 90))
    editor.finish_drag_selected()

    assert editor.selected is element
    assert element.x == 140.0
    assert element.y == 90.0
