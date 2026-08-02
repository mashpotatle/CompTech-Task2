import json
import sys
from pathlib import Path

import pygame

from levels.level_manager import LevelManager
from levels.cave_section import LevelElement


def _write_section(path: Path, section_id: str) -> None:
    payload = {
        "id": section_id,
        "name": section_id,
        "entry": {"position": [0, 0], "direction": "right"},
        "exit": {"position": [400, 0], "direction": "right"},
        "elements": [
            {
                "id": f"{section_id}_wall",
                "type": "wall",
                "position": [0, 0],
                "geometry": {"points": [[0, 0], [400, 0], [400, 50], [0, 50]]},
                "properties": {},
                "material": {},
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_reused_templates_create_independent_instances(tmp_path):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

    section_path = tmp_path / "section_01.json"
    _write_section(section_path, "section_01")

    manager = LevelManager(tmp_path, available_sections=["section_01.json"])

    first_instance = manager.load_initial_section("section_01.json")
    second_instance = manager.stitch_next_section("section_01.json")

    assert first_instance.instance_id != second_instance.instance_id
    assert first_instance.template_filename == second_instance.template_filename == "section_01.json"

    first_item = LevelElement(
        element_id="item_1",
        element_type="item",
        position=[10, 10],
    )
    second_item = LevelElement(
        element_id="item_2",
        element_type="item",
        position=[20, 20],
    )

    manager.add_dropped_item(first_instance, first_item)
    manager.add_dropped_item(second_instance, second_item)

    assert len(first_instance.runtime_state["dropped_items"]) == 1
    assert len(second_instance.runtime_state["dropped_items"]) == 1
    assert first_instance.runtime_state["dropped_items"][0].element_id == "item_1"
    assert second_instance.runtime_state["dropped_items"][0].element_id == "item_2"


def test_transition_to_existing_section_uses_loaded_next_instance(tmp_path):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

    _write_section(tmp_path / "section_01.json", "section_01")
    _write_section(tmp_path / "section_02.json", "section_02")

    manager = LevelManager(
        tmp_path,
        available_sections=["section_01.json", "section_02.json"],
        preload_section_count=0,
    )

    first_instance = manager.load_initial_section("section_01.json")
    second_instance = manager.stitch_next_section("section_02.json")

    manager.current_section_index = 0

    transition_target = manager.transition_to_next_section(
        first_instance.world_offset + first_instance.section.exit_position,
        pygame.Vector2(1, 0),
    )

    assert transition_target is second_instance
    assert manager.get_current_section() is second_instance


def test_transition_ignores_backward_movement_towards_exit(tmp_path):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

    _write_section(tmp_path / "section_01.json", "section_01")
    _write_section(tmp_path / "section_02.json", "section_02")

    manager = LevelManager(
        tmp_path,
        available_sections=["section_01.json", "section_02.json"],
    )

    first_instance = manager.load_initial_section("section_01.json")
    second_instance = manager.stitch_next_section("section_02.json")

    manager.current_section_index = 0

    transition_target = manager.transition_to_next_section(
        first_instance.world_offset + first_instance.section.exit_position,
        pygame.Vector2(-1, 0),
    )

    assert transition_target is None
    assert manager.get_current_section() is first_instance


def test_preload_count_loads_sections_ahead(tmp_path):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

    _write_section(tmp_path / "section_01.json", "section_01")
    _write_section(tmp_path / "section_02.json", "section_02")
    _write_section(tmp_path / "section_03.json", "section_03")

    manager = LevelManager(
        tmp_path,
        available_sections=["section_01.json", "section_02.json", "section_03.json"],
        preload_section_count=2,
    )

    manager.load_initial_section("section_01.json")

    assert len(manager.sections) == 3


def test_preload_count_can_exceed_available_unique_files(tmp_path):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

    _write_section(tmp_path / "section_01.json", "section_01")
    _write_section(tmp_path / "section_02.json", "section_02")

    manager = LevelManager(
        tmp_path,
        available_sections=["section_01.json", "section_02.json"],
        preload_section_count=5,
    )

    manager.load_initial_section("section_01.json")

    assert len(manager.sections) == 6


def test_preload_count_keeps_sections_ahead_when_player_moves_forward(tmp_path):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

    _write_section(tmp_path / "section_01.json", "section_01")
    _write_section(tmp_path / "section_02.json", "section_02")
    _write_section(tmp_path / "section_03.json", "section_03")
    _write_section(tmp_path / "section_04.json", "section_04")

    manager = LevelManager(
        tmp_path,
        available_sections=[
            "section_01.json",
            "section_02.json",
            "section_03.json",
            "section_04.json",
        ],
        preload_section_count=2,
    )

    manager.load_initial_section("section_01.json")

    assert len(manager.sections) == 3

    second_section = manager.sections[1]
    manager.update_active_section(
        second_section.world_offset + pygame.Vector2(10, 10)
    )

    assert manager.current_section_index == 1
    assert len(manager.sections) == 4


def test_level_manager_discovers_sections_from_data_directory(tmp_path):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

    _write_section(tmp_path / "section_01.json", "section_01")
    _write_section(tmp_path / "section_02.json", "section_02")
    _write_section(tmp_path / "section_03.json", "section_03")

    manager = LevelManager(
        tmp_path,
        available_sections=["section_01.json"],
    )

    assert manager.available_sections == [
        "section_01.json",
        "section_02.json",
        "section_03.json",
    ]
