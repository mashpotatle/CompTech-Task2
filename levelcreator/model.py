from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import copy
import json
from pathlib import Path


DIRECTIONS = ("left", "right", "up", "down")
ITEM_PRESET_IDS = ("oxygen_tank", "med_kit")


ENTITY_DEFINITIONS: dict[str, dict[str, Any]] = {
    "wall": {
        "label": "Wall",
        "kind": "polygon",
        "colour": (85, 105, 115),
        "fields": {},
    },
    "obstacle": {
        "label": "Obstacle",
        "kind": "polygon",
        "colour": (115, 85, 60),
        "fields": {},
    },
    "fish_spawn": {
        "label": "Fish Spawn",
        "kind": "circle",
        "colour": (70, 200, 160),
        "default_radius": 24,
        "fields": {
            "count": ("int", 3),
            "speed": ("float", 70.0),
            "detection_range": ("float", 180.0),
            "damage": ("int", 10),
            "patrol_distance": ("float", 150.0),
            "direction_x": ("float", 1.0),
            "direction_y": ("float", 0.0),
        },
    },
    "spiky_plant": {
        "label": "Spiky Plant",
        "kind": "circle",
        "colour": (100, 210, 100),
        "default_radius": 22,
        "fields": {
            "damage": ("int", 10),
            "radius": ("float", 22.0),
        },
    },
    "thermal_vent": {
        "label": "Thermal Vent",
        "kind": "circle",
        "colour": (230, 95, 45),
        "default_radius": 26,
        "fields": {
            "radius": ("float", 26.0),
            "heat_radius": ("float", 100.0),
            "heat_damage": ("float", 5.0),
            "eruption_damage": ("float", 20.0),
            "eruption_duration": ("float", 1.0),
            "eruption_interval": ("float", 5.0),
            "haze_length": ("float", 95.0),
            "haze_width": ("float", 30.0),
            "haze_alpha": ("int", 65),
            "bubble_count": ("int", 14),
            "bubble_spread": ("float", 15.0),
            "bubble_speed": ("float", 1.0),
        },
    },
    "silt_cloud": {
        "label": "Silt Cloud",
        "kind": "circle",
        "colour": (145, 145, 155),
        "default_radius": 120,
        "fields": {
            "radius": ("float", 120.0),
            "visibility": ("float", 0.1),
        },
    },
    "current": {
        "label": "Current",
        "kind": "rect",
        "colour": (65, 135, 225),
        "default_width": 260,
        "default_height": 120,
        "fields": {
            "width": ("float", 260.0),
            "height": ("float", 120.0),
            "strength": ("float", 40.0),
            "direction_x": ("float", 1.0),
            "direction_y": ("float", 0.0),
        },
    },
    "item": {
        "label": "Item",
        "kind": "circle",
        "colour": (235, 205, 75),
        "default_radius": 18,
        "fields": {
            "item_type": ("item_id", ITEM_PRESET_IDS[0]),
            "pickup_radius": ("float", 48.0),
        },
    },
    "lore_fragment": {
        "label": "Lore Fragment",
        "kind": "circle",
        "colour": (205, 125, 235),
        "default_radius": 18,
        "fields": {
            "text": ("str", "New lore fragment"),
            "interaction_radius": ("float", 48.0),
        },
    },
}


@dataclass
class Element:
    element_id: str
    element_type: str
    x: float
    y: float
    points: list[list[float]] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)
    material: dict[str, Any] = field(default_factory=dict)

    def copy(self) -> "Element":
        return copy.deepcopy(self)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.element_id,
            "type": self.element_type,
            "position": [round(self.x, 3), round(self.y, 3)],
        }
        if self.points:
            data["geometry"] = {
                "points": [
                    [round(p[0], 3), round(p[1], 3)]
                    for p in self.points
                ]
            }
        if self.properties:
            data["properties"] = copy.deepcopy(self.properties)
        if self.material:
            data["material"] = copy.deepcopy(self.material)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Element":
        pos = data.get("position", [0, 0])
        geometry = data.get("geometry", {})
        return cls(
            element_id=str(data["id"]),
            element_type=str(data["type"]),
            x=float(pos[0]),
            y=float(pos[1]),
            points=[
                [float(p[0]), float(p[1])]
                for p in geometry.get("points", [])
            ],
            properties=copy.deepcopy(data.get("properties", {})),
            material=copy.deepcopy(data.get("material", {})),
        )


@dataclass
class Level:
    level_id: str = "section_01"
    name: str = "New Cave Section"
    width: int = 2048
    height: int = 768
    # Entry and exit are structural section boundaries, not editable elements.
    entry_x: float = 0.0
    entry_y: float = 384.0
    entry_direction: str = "right"
    exit_x: float = 2048.0
    exit_y: float = 384.0
    exit_direction: str = "right"
    elements: list[Element] = field(default_factory=list)
    format_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        mid_y = self.height / 2
        return {
            "format_version": self.format_version,
            "id": self.level_id,
            "name": self.name,
            "width": int(self.width),
            "height": int(self.height),
            "entry": {
                "position": [0.0, round(mid_y, 3)],
                "direction": "right",
            },
            "exit": {
                "position": [round(float(self.width), 3), round(mid_y, 3)],
                "direction": "right",
            },
            "elements": [e.to_dict() for e in self.elements],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Level":
        width = int(data.get("width", 2048))
        height = int(data.get("height", 768))
        # Older level files may contain movable entry/exit positions. Ignore them
        # and migrate them to the canonical section boundaries on load.
        return cls(
            level_id=str(data.get("id", "unnamed_section")),
            name=str(data.get("name", "Cave Section")),
            width=width,
            height=height,
            entry_x=0.0,
            entry_y=height / 2,
            entry_direction="right",
            exit_x=float(width),
            exit_y=height / 2,
            exit_direction="right",
            elements=[Element.from_dict(e) for e in data.get("elements", [])],
            format_version=int(data.get("format_version", 1)),
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=4), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "Level":
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.width < 512:
            errors.append("Section width must be at least 512.")
        if self.height < 512:
            errors.append("Section height must be at least 512.")

        if self.entry_x != 0 or self.entry_y != self.height / 2:
            errors.append("Entry is not at the fixed left section boundary.")
        if self.exit_x != self.width or self.exit_y != self.height / 2:
            errors.append("Exit is not at the fixed right section boundary.")

        for label, direction in (
            ("Entry", self.entry_direction),
            ("Exit", self.exit_direction),
        ):
            if direction not in DIRECTIONS:
                errors.append(f"{label} direction is invalid.")

        ids: set[str] = set()
        for e in self.elements:
            if e.element_id in ids:
                errors.append(f"Duplicate element id: {e.element_id}")
            ids.add(e.element_id)

            for px, py in e.points:
                wx, wy = e.x + px, e.y + py
                if not (0 <= wx <= self.width and 0 <= wy <= self.height):
                    errors.append(f"Element '{e.element_id}' extends outside the section.")
                    break

            if not e.points and not (0 <= e.x <= self.width and 0 <= e.y <= self.height):
                errors.append(f"Element '{e.element_id}' is outside the section.")

            if e.element_type == "current":
                if float(e.properties.get("width", 0)) <= 0 or float(e.properties.get("height", 0)) <= 0:
                    errors.append(f"Current '{e.element_id}' has invalid dimensions.")

        return errors
