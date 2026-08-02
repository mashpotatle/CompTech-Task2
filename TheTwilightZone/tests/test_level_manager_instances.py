import json
import sys
from pathlib import Path

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
