from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pygame


@dataclass
class LevelElement:
    """
    Represents a single element stored inside a cave section.

    Polygon points are stored in local coordinates relative to the
    element's position. The get_polygon() method converts these points
    into world coordinates when required.
    """

    element_id: str
    element_type: str

    position: pygame.Vector2 = field(
        default_factory=lambda: pygame.Vector2(0, 0)
    )

    points: list[pygame.Vector2] = field(
        default_factory=list
    )

    properties: dict[str, Any] = field(
        default_factory=dict
    )

    material: dict[str, Any] = field(
        default_factory=dict
    )

    def is_geometry(self) -> bool:
        """
        Returns True if the element contains polygon geometry.
        """

        return bool(
            self.points
        )

    def get_polygon(
        self
    ) -> list[pygame.Vector2]:
        """
        Returns the polygon points in world coordinates.

        Polygon points are stored locally relative to the element's
        position. The element position is added to each point to
        calculate the final world-space coordinates.
        """

        return [
            point + self.position
            for point in self.points
        ]

    def get_world_points(
        self,
    ) -> list[pygame.Vector2]:
        """
        Return the element's polygon points in world coordinates.

        The points stored in the level file are local to the element.
        The element's position determines where the element exists in
        the world.

        Returns:
            A new list containing the polygon points translated into
            world coordinates.
        """

        return [
            point + self.position
            for point in self.points
        ]


@dataclass
class CaveSection:
    """
    Stores the complete data for one modular cave section.

    The section contains world data only.

    Camera position, scrolling speed and screen coordinates are
    handled by other game systems.
    """

    section_id: str
    name: str

    entry_position: pygame.Vector2
    entry_direction: str

    exit_position: pygame.Vector2
    exit_direction: str

    elements: list[LevelElement] = field(
        default_factory=list
    )

    width: float = 0.0
    height: float = 0.0

    def get_walls(self) -> list[LevelElement]:
        """
        Returns all wall elements in this section.
        """

        return [
            element
            for element in self.elements
            if element.element_type == "wall"
        ]

    def get_obstacles(self) -> list[LevelElement]:
        """
        Returns all solid obstacle elements.
        """

        return [
            element
            for element in self.elements
            if element.element_type == "obstacle"
        ]

    def get_geometry(self) -> list[LevelElement]:
        """
        Returns all elements that provide solid collision geometry.
        """

        return [
            element
            for element in self.elements
            if element.element_type in (
                "wall",
                "obstacle",
            )
        ]

    def get_entities(self) -> list[LevelElement]:
        """
        Returns all non-geometry gameplay elements.
        """

        return [
            element
            for element in self.elements
            if element.element_type not in (
                "wall",
                "obstacle",
            )
        ]

    def draw(
        self,
        screen: pygame.Surface,
        camera,
        debug: bool = False,
    ) -> None:
        """
        Draw all geometry in the cave section.

        Geometry is first converted from local coordinates to world
        coordinates. The camera then converts world coordinates into
        screen coordinates.
        """

        # Draw cave walls.
        for wall in self.get_walls():

            # Convert local geometry into world coordinates.
            world_polygon = wall.get_polygon()

            # Convert world coordinates into screen coordinates.
            screen_polygon = [
                camera.world_to_screen(point)
                for point in world_polygon
            ]

            if screen_polygon:

                pygame.draw.polygon(
                    screen,
                    (70, 80, 85),
                    screen_polygon,
                )

                if debug:

                    pygame.draw.lines(
                        screen,
                        (120, 130, 135),
                        True,
                        screen_polygon,
                        2,
                    )

        # Draw solid obstacles.
        for obstacle in self.get_obstacles():

            # Convert local geometry into world coordinates.
            world_polygon = obstacle.get_polygon()

            # Convert world coordinates into screen coordinates.
            screen_polygon = [
                camera.world_to_screen(point)
                for point in world_polygon
            ]

            if screen_polygon:

                pygame.draw.polygon(
                    screen,
                    (80, 90, 95),
                    screen_polygon,
                )

                if debug:

                    pygame.draw.lines(
                        screen,
                        (130, 140, 145),
                        True,
                        screen_polygon,
                        2,
                    )