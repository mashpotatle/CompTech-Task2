from __future__ import annotations

import json
from pathlib import Path

import pygame

from levels.cave_section import CaveSection, LevelElement


class LevelLoader:
    """
    Loads cave section data from JSON files.

    This class is responsible only for converting saved level data into
    Python objects. It does not handle camera movement, scrolling or
    gameplay behaviour.
    """

    def __init__(self, data_directory: str | Path):
        self.data_directory = Path(data_directory)

    def load_section(self, filename: str) -> CaveSection:
        """
        Loads one cave section from a JSON file.

        Args:
            filename: JSON filename inside the data directory.

        Returns:
            A fully populated CaveSection.
        """

        path = self.data_directory / filename

        if not path.exists():
            raise FileNotFoundError(
                f"Cave section file not found: {path}"
            )

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return self._parse_section(data)

    def _parse_section(self, data: dict) -> CaveSection:
        """
        Converts raw JSON data into a CaveSection object.
        """

        entry = data["entry"]
        exit_data = data["exit"]

        elements = []

        for element_data in data.get("elements", []):
            elements.append(
                self._parse_element(element_data)
            )

        return CaveSection(
            section_id=data["id"],
            name=data.get("name", data["id"]),

            entry_position=pygame.Vector2(
                entry["position"]
            ),

            entry_direction=entry.get(
                "direction",
                "right"
            ),

            exit_position=pygame.Vector2(
                exit_data["position"]
            ),

            exit_direction=exit_data.get(
                "direction",
                "right"
            ),

            elements=elements,

            width=data.get(
                "width",
                self._calculate_width(elements)
            ),

            height=data.get(
                "height",
                self._calculate_height(elements)
            )
        )

    @staticmethod
    def _parse_element(data: dict) -> LevelElement:
        """
        Converts one JSON element into a LevelElement.
        """

        position = pygame.Vector2(
            data.get("position", [0, 0])
        )

        geometry = data.get(
            "geometry",
            {}
        )

        points = [
            pygame.Vector2(point)
            for point in geometry.get(
                "points",
                []
            )
        ]

        return LevelElement(
            element_id=data["id"],
            element_type=data["type"],
            position=position,
            points=points,
            properties=data.get(
                "properties",
                {}
            ),
            material=data.get(
                "material",
                {}
            )
        )

    @staticmethod
    def _calculate_width(
        elements: list[LevelElement]
    ) -> float:
        """
        Calculates the width required by the geometry.

        Local polygon coordinates are combined with each element's
        position to determine the maximum world-space coordinate.
        """

        maximum_x = 0.0

        for element in elements:

            for point in element.points:

                world_x = (
                    element.position.x
                    + point.x
                )

                maximum_x = max(
                    maximum_x,
                    world_x
                )

        return maximum_x

    @staticmethod
    def _calculate_height(
        elements: list[LevelElement]
    ) -> float:
        """
        Calculates the height required by the geometry.
        """

        maximum_y = 0.0

        for element in elements:
            for point in element.points:
                maximum_y = max(
                    maximum_y,
                    point.y
                )

            maximum_y = max(
                maximum_y,
                element.position.y
            )

        return maximum_y