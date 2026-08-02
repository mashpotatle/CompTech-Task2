"""
Cave Level Editor
=================

Standalone level editor for the STEM Video Game Challenge project.

This editor creates cave section JSON files compatible with the game's
unified level format.

Supported element types:

    wall
    obstacle
    current
    silt_cloud
    thermal_vent
    fish_spawn
    lore_fragment

Controls
--------

Left Mouse Button
    Draw polygon points or place objects.

Right Mouse Button
    Finish the current polygon.

Escape
    Cancel current polygon / deselect.

Delete
    Delete selected element.

S
    Save level.

Ctrl + S
    Save level.

O
    Open level.

N
    New level.

1
    Wall tool.

2
    Obstacle tool.

3
    Current tool.

4
    Silt cloud tool.

5
    Thermal vent tool.

6
    Fish spawn tool.

7
    Lore fragment tool.

E
    Entry point tool.

X
    Exit point tool.

V
    Selection tool.

Mouse Wheel
    Zoom.

Middle Mouse Button
    Pan.

Arrow Keys
    Move selected element.

This is an early version of the editor. The JSON format is intentionally
simple and human-readable so that it can later be inspected or edited
manually if required.
"""

from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path
from typing import Any

import pygame


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

EDITOR_TITLE = "Cave Level Editor"

DEFAULT_LEVEL_WIDTH = 2048
DEFAULT_LEVEL_HEIGHT = 768

GRID_SIZE = 32

MIN_ZOOM = 0.25
MAX_ZOOM = 3.0

ZOOM_STEP = 1.1

POINT_RADIUS = 5

BACKGROUND_COLOUR = (15, 22, 28)
GRID_COLOUR = (35, 45, 52)

WALL_COLOUR = (80, 100, 110)
WALL_OUTLINE_COLOUR = (150, 180, 190)

OBSTACLE_COLOUR = (100, 75, 55)
OBSTACLE_OUTLINE_COLOUR = (180, 140, 100)

CURRENT_COLOUR = (60, 130, 220)
SILT_COLOUR = (120, 120, 120)
THERMAL_COLOUR = (220, 90, 40)
FISH_COLOUR = (70, 200, 160)
LORE_COLOUR = (220, 200, 70)

ENTRY_COLOUR = (80, 220, 100)
EXIT_COLOUR = (220, 80, 80)

TEXT_COLOUR = (220, 230, 235)
PANEL_COLOUR = (25, 32, 38)
PANEL_BORDER_COLOUR = (70, 80, 90)

MIN_SECTION_WIDTH = 512
MIN_SECTION_HEIGHT = 512

ENTRY_EXIT_MIN_DISTANCE = 256
SECTION_BOUNDARY_MARGIN = 64

DATA_DIRECTORY = (
    Path(__file__).resolve().parent
    / "data"
    / "cave_sections"
)


# ---------------------------------------------------------------------------
# Element definitions
# ---------------------------------------------------------------------------

POLYGON_TOOLS = {
    "wall",
    "obstacle",
}

OBJECT_TOOLS = {
    "current",
    "silt_cloud",
    "thermal_vent",
    "fish_spawn",
    "lore_fragment",
}


TOOL_NAMES = {
    "select": "Select",
    "wall": "Wall",
    "obstacle": "Obstacle",
    "current": "Current",
    "silt_cloud": "Silt Cloud",
    "thermal_vent": "Thermal Vent",
    "fish_spawn": "Fish Spawn",
    "lore_fragment": "Lore Fragment",
    "entry": "Entry Point",
    "exit": "Exit Point",
}


ELEMENT_COLOURS = {
    "wall": (
        WALL_COLOUR,
        WALL_OUTLINE_COLOUR,
    ),

    "obstacle": (
        OBSTACLE_COLOUR,
        OBSTACLE_OUTLINE_COLOUR,
    ),

    "current": (
        CURRENT_COLOUR,
        CURRENT_COLOUR,
    ),

    "silt_cloud": (
        SILT_COLOUR,
        SILT_COLOUR,
    ),

    "thermal_vent": (
        THERMAL_COLOUR,
        THERMAL_COLOUR,
    ),

    "fish_spawn": (
        FISH_COLOUR,
        FISH_COLOUR,
    ),

    "lore_fragment": (
        LORE_COLOUR,
        LORE_COLOUR,
    ),
}


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def vector_to_list(
    vector: pygame.Vector2,
) -> list[float]:
    """
    Converts a Vector2 into a JSON-compatible list.
    """

    return [
        round(vector.x, 3),
        round(vector.y, 3),
    ]


def list_to_vector(
    values: list[float],
) -> pygame.Vector2:
    """
    Converts a JSON coordinate list into Vector2.
    """

    return pygame.Vector2(
        float(values[0]),
        float(values[1]),
    )


def distance(
    a: pygame.Vector2,
    b: pygame.Vector2,
) -> float:
    """
    Returns the distance between two points.
    """

    return a.distance_to(b)


# ---------------------------------------------------------------------------
# Level Element
# ---------------------------------------------------------------------------

class EditorElement:
    """
    Represents one editable level element.

    Polygon geometry is stored in LOCAL coordinates.

    The element position determines where the element exists in the
    section's world coordinate system.
    """

    def __init__(
        self,
        element_id: str,
        element_type: str,
        position: pygame.Vector2 | None = None,
        points: list[pygame.Vector2] | None = None,
        properties: dict[str, Any] | None = None,
        material: dict[str, Any] | None = None,
    ):
        self.element_id = element_id

        self.element_type = element_type

        self.position = (
            position.copy()
            if position is not None
            else pygame.Vector2()
        )

        self.points = (
            [
                point.copy()
                for point in points
            ]
            if points is not None
            else []
        )

        self.properties = (
            dict(properties)
            if properties is not None
            else {}
        )

        self.material = (
            dict(material)
            if material is not None
            else {}
        )

    # ------------------------------------------------------------------
    # Geometry
    # ------------------------------------------------------------------

    def get_world_points(
        self,
    ) -> list[pygame.Vector2]:
        """
        Return polygon points converted from local element
        coordinates into world coordinates.
        """

        return [
            point + self.position
            for point in self.points
        ]

    def get_world_bounds(self) -> pygame.Rect:
        """
        Calculate the bounding rectangle containing all geometry
        and the section entry and exit points.
        """

        positions = [
            self.entry_position,
            self.exit_position,
        ]

        for element in self.elements:

            # Include the element position.
            positions.append(
                element.position
            )

            # Include all polygon points in world coordinates.
            positions.extend(
                element.get_polygon()
            )

        if not positions:
            return pygame.Rect(
                0,
                0,
                self.width,
                self.height,
            )

        minimum_x = min(
            position.x
            for position in positions
        )

        minimum_y = min(
            position.y
            for position in positions
        )

        maximum_x = max(
            position.x
            for position in positions
        )

        maximum_y = max(
            position.y
            for position in positions
        )

        return pygame.Rect(
            round(minimum_x),
            round(minimum_y),
            round(maximum_x - minimum_x),
            round(maximum_y - minimum_y),
        )

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Converts the element into JSON-compatible data.
        """

        data = {
            "id": self.element_id,
            "type": self.element_type,
            "position": vector_to_list(
                self.position
            ),
        }

        if self.points:
            data["geometry"] = {
                "points": [
                    vector_to_list(point)
                    for point in self.points
                ]
            }

        if self.properties:
            data["properties"] = (
                self.properties
            )

        if self.material:
            data["material"] = (
                self.material
            )

        return data

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "EditorElement":
        """
        Creates an EditorElement from JSON data.
        """

        geometry = data.get(
            "geometry",
            {},
        )

        points = [
            list_to_vector(point)
            for point in geometry.get(
                "points",
                [],
            )
        ]

        return cls(
            element_id=data["id"],

            element_type=data["type"],

            position=list_to_vector(
                data.get(
                    "position",
                    [0, 0],
                )
            ),

            points=points,

            properties=data.get(
                "properties",
                {},
            ),

            material=data.get(
                "material",
                {},
            ),
        )


# ---------------------------------------------------------------------------
# Level Data
# ---------------------------------------------------------------------------

class LevelData:
    """
    Stores all information belonging to one cave section.
    """

    def __init__(self):
        self.format_version = 1

        self.level_id = "section_01"

        self.name = "New Cave Section"

        self.width = DEFAULT_LEVEL_WIDTH

        self.height = DEFAULT_LEVEL_HEIGHT

        self.entry_position = pygame.Vector2(
            50,
            DEFAULT_LEVEL_HEIGHT / 2,
        )

        self.entry_direction = "right"

        self.exit_position = pygame.Vector2(
            DEFAULT_LEVEL_WIDTH - 50,
            DEFAULT_LEVEL_HEIGHT / 2,
        )

        self.exit_direction = "right"

        self.elements: list[
            EditorElement
        ] = []

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Converts the complete level into JSON-compatible data.
        """

        return {
            "format_version": self.format_version,

            "id": self.level_id,

            "name": self.name,

            "width": self.width,

            "height": self.height,

            "entry": {
                "position": vector_to_list(
                    self.entry_position
                ),
                "direction": self.entry_direction,
            },

            "exit": {
                "position": vector_to_list(
                    self.exit_position
                ),
                "direction": self.exit_direction,
            },

            "elements": [
                element.to_dict()
                for element in self.elements
            ],
        }

    def save(
        self,
        path: Path,
    ) -> bool:
        """
        Validate and save the current cave section.

        Returns:
            True if the level was saved successfully.
            False if validation failed.
        """

        errors = self.validate()

        if errors:

            print(
                "\nLevel validation failed:"
            )

            for error in errors:
                print(
                    f" - {error}"
                )

            return False

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with path.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                self.to_dict(),
                file,
                indent=4,
            )

        return True

    def load(
        self,
        path: Path,
    ) -> None:
        """
        Loads level data from a JSON file.
        """

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        self.format_version = data.get(
            "format_version",
            1,
        )

        self.level_id = data.get(
            "id",
            "unnamed_section",
        )

        self.name = data.get(
            "name",
            self.level_id,
        )

        self.width = data.get(
            "width",
            DEFAULT_LEVEL_WIDTH,
        )

        self.height = data.get(
            "height",
            DEFAULT_LEVEL_HEIGHT,
        )

        entry = data.get(
            "entry",
            {},
        )

        self.entry_position = list_to_vector(
            entry.get(
                "position",
                [50, self.height / 2],
            )
        )

        self.entry_direction = entry.get(
            "direction",
            "right",
        )

        exit_data = data.get(
            "exit",
            {},
        )

        self.exit_position = list_to_vector(
            exit_data.get(
                "position",
                [
                    self.width - 50,
                    self.height / 2,
                ],
            )
        )

        self.exit_direction = exit_data.get(
            "direction",
            "right",
        )

        self.elements.clear()

        for element_data in data.get(
            "elements",
            [],
        ):

            self.elements.append(
                EditorElement.from_dict(
                    element_data
                )
            )

    def validate(
        self,
    ) -> list[str]:
        """
        Validate the cave section before saving.

        Returns:
            A list of validation errors.
            An empty list means the section is valid.
        """

        errors: list[str] = []

        # --------------------------------------------------------------
        # Basic dimensions
        # --------------------------------------------------------------

        if self.width < MIN_SECTION_WIDTH:
            errors.append(
                f"Section width must be at least "
                f"{MIN_SECTION_WIDTH}px."
            )

        if self.height < MIN_SECTION_HEIGHT:
            errors.append(
                f"Section height must be at least "
                f"{MIN_SECTION_HEIGHT}px."
            )

        # --------------------------------------------------------------
        # Entry point
        # --------------------------------------------------------------

        if not (
            0 <= self.entry_position.x <= self.width
            and
            0 <= self.entry_position.y <= self.height
        ):
            errors.append(
                "Entry point is outside the section bounds."
            )

        # --------------------------------------------------------------
        # Exit point
        # --------------------------------------------------------------

        if not (
            0 <= self.exit_position.x <= self.width
            and
            0 <= self.exit_position.y <= self.height
        ):
            errors.append(
                "Exit point is outside the section bounds."
            )

        # --------------------------------------------------------------
        # Entry / exit distance
        # --------------------------------------------------------------

        if (
            self.entry_position.distance_to(
                self.exit_position
            )
            < ENTRY_EXIT_MIN_DISTANCE
        ):
            errors.append(
                "Entry and exit points are too close together."
            )

        # --------------------------------------------------------------
        # Entry direction
        # --------------------------------------------------------------

        valid_directions = {
            "left",
            "right",
            "up",
            "down",
        }

        if self.entry_direction not in valid_directions:
            errors.append(
                f"Invalid entry direction: "
                f"{self.entry_direction}"
            )

        if self.exit_direction not in valid_directions:
            errors.append(
                f"Invalid exit direction: "
                f"{self.exit_direction}"
            )

        # --------------------------------------------------------------
        # Element bounds
        # --------------------------------------------------------------

        for element in self.elements:

            for point in element.get_world_points():

                if (
                    point.x < 0
                    or point.x > self.width
                    or point.y < 0
                    or point.y > self.height
                ):
                    errors.append(
                        f"Element '{element.element_id}' "
                        f"extends outside the section bounds."
                    )

                    break

        return errors

# ---------------------------------------------------------------------------
# Level Editor
# ---------------------------------------------------------------------------

class LevelEditor:
    """
    Main application class for the cave level editor.
    """

    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode(
            (
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
            )
        )

        pygame.display.set_caption(
            EDITOR_TITLE
        )

        self.clock = pygame.time.Clock()

        self.font = pygame.font.Font(
            None,
            20,
        )

        self.small_font = pygame.font.Font(
            None,
            16,
        )

        self.level = LevelData()

        self.current_tool = "select"

        self.selected_element: (
            EditorElement | None
        ) = None

        self.drawing_points: list[
            pygame.Vector2
        ] = []

        self.camera_position = pygame.Vector2(
            0,
            0,
        )

        self.zoom = 0.75

        self.running = True

        self.status_message = (
            "Ready"
        )

        self.current_file: (
            Path | None
        ) = None

        self.dragging = False

        self.last_mouse_position = (
            pygame.Vector2()
        )

        self.next_element_number = 1

    # ------------------------------------------------------------------
    # Main Loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """
        Runs the editor main loop.
        """

        while self.running:

            dt = self.clock.tick(
                60
            ) / 1000.0

            self.handle_events()

            self.update(
                dt
            )

            self.draw()

        pygame.quit()

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def handle_events(self) -> None:
        """
        Processes all pygame events.
        """

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                self.running = False

            elif event.type == pygame.KEYDOWN:

                self.handle_key_down(
                    event
                )

            elif event.type == pygame.MOUSEBUTTONDOWN:

                self.handle_mouse_down(
                    event
                )

            elif event.type == pygame.MOUSEBUTTONUP:

                self.handle_mouse_up(
                    event
                )

            elif event.type == pygame.MOUSEMOTION:

                self.handle_mouse_motion(
                    event
                )

    # ------------------------------------------------------------------
    # Keyboard
    # ------------------------------------------------------------------

    def handle_key_down(
        self,
        event: pygame.event.Event,
    ) -> None:

        if event.key == pygame.K_ESCAPE:

            self.drawing_points.clear()

            self.selected_element = None

            self.status_message = (
                "Selection cleared"
            )

        elif event.key == pygame.K_DELETE:

            self.delete_selected()

        elif event.key == pygame.K_s:

            self.save_level()

        elif event.key == pygame.K_o:

            self.open_level()

        elif event.key == pygame.K_n:

            self.new_level()

        elif event.key == pygame.K_v:

            self.set_tool(
                "select"
            )

        elif event.key == pygame.K_1:

            self.set_tool(
                "wall"
            )

        elif event.key == pygame.K_2:

            self.set_tool(
                "obstacle"
            )

        elif event.key == pygame.K_3:

            self.set_tool(
                "current"
            )

        elif event.key == pygame.K_4:

            self.set_tool(
                "silt_cloud"
            )

        elif event.key == pygame.K_5:

            self.set_tool(
                "thermal_vent"
            )

        elif event.key == pygame.K_6:

            self.set_tool(
                "fish_spawn"
            )

        elif event.key == pygame.K_7:

            self.set_tool(
                "lore_fragment"
            )

        elif event.key == pygame.K_e:

            self.set_tool(
                "entry"
            )

        elif event.key == pygame.K_x:

            self.set_tool(
                "exit"
            )

        elif event.key == pygame.K_UP:

            self.move_selected(
                pygame.Vector2(
                    0,
                    -1,
                )
            )

        elif event.key == pygame.K_DOWN:

            self.move_selected(
                pygame.Vector2(
                    0,
                    1,
                )
            )

        elif event.key == pygame.K_LEFT:

            self.move_selected(
                pygame.Vector2(
                    -1,
                    0,
                )
            )

        elif event.key == pygame.K_RIGHT:

            self.move_selected(
                pygame.Vector2(
                    1,
                    0,
                )
            )

    # ------------------------------------------------------------------
    # Mouse
    # ------------------------------------------------------------------

    def handle_mouse_down(
        self,
        event: pygame.event.Event,
    ) -> None:

        mouse_position = pygame.Vector2(
            event.pos
        )

        if event.button == 1:

            world_position = (
                self.screen_to_world(
                    mouse_position
                )
            )

            self.handle_left_click(
                world_position
            )

        elif event.button == 3:

            if self.current_tool in POLYGON_TOOLS:

                self.finish_polygon()

        elif event.button == 2:

            self.dragging = True

            self.last_mouse_position = (
                mouse_position
            )

        elif event.button == 4:

            self.zoom_at_mouse(
                1 / ZOOM_STEP
            )

        elif event.button == 5:

            self.zoom_at_mouse(
                ZOOM_STEP
            )

    def handle_mouse_up(
        self,
        event: pygame.event.Event,
    ) -> None:

        if event.button == 2:

            self.dragging = False

    def handle_mouse_motion(
        self,
        event: pygame.event.Event,
    ) -> None:

        if not self.dragging:
            return

        current_position = pygame.Vector2(
            event.pos
        )

        movement = (
            current_position
            - self.last_mouse_position
        )

        self.camera_position -= (
            movement
            / self.zoom
        )

        self.last_mouse_position = (
            current_position
        )

    # ------------------------------------------------------------------
    # Tool Handling
    # ------------------------------------------------------------------

    def set_tool(
        self,
        tool: str,
    ) -> None:

        self.current_tool = tool

        self.drawing_points.clear()

        self.selected_element = None

        self.status_message = (
            f"Tool: {TOOL_NAMES.get(tool, tool)}"
        )

    def handle_left_click(
        self,
        world_position: pygame.Vector2,
    ) -> None:

        if self.current_tool == "select":

            self.select_element(
                world_position
            )

        elif self.current_tool in POLYGON_TOOLS:

            self.drawing_points.append(
                world_position
            )

            self.status_message = (
                f"{len(self.drawing_points)} "
                "points. Right-click to finish."
            )

        elif self.current_tool in OBJECT_TOOLS:

            self.create_object(
                world_position
            )

        elif self.current_tool == "entry":

            self.level.entry_position = (
                world_position
            )

            self.status_message = (
                "Entry point moved."
            )

        elif self.current_tool == "exit":

            self.level.exit_position = (
                world_position
            )

            self.status_message = (
                "Exit point moved."
            )

    # ------------------------------------------------------------------
    # Polygon Creation
    # ------------------------------------------------------------------

    def finish_polygon(self) -> None:

        if self.current_tool not in POLYGON_TOOLS:
            return

        if len(self.drawing_points) < 3:

            self.status_message = (
                "A polygon needs at least 3 points."
            )

            self.drawing_points.clear()

            return

        # Convert the clicked world positions into
        # local coordinates.

        minimum_x = min(
            point.x
            for point in self.drawing_points
        )

        minimum_y = min(
            point.y
            for point in self.drawing_points
        )

        position = pygame.Vector2(
            minimum_x,
            minimum_y,
        )

        local_points = [
            point - position
            for point in self.drawing_points
        ]

        element = EditorElement(
            element_id=self.generate_id(
                self.current_tool
            ),

            element_type=self.current_tool,

            position=position,

            points=local_points,
        )

        if self.current_tool == "wall":

            element.material = {
                "texture": None,

                "mapping": {
                    "mode": "world",

                    "origin": [
                        0,
                        0,
                    ],

                    "scale": [
                        1.0,
                        1.0,
                    ],

                    "rotation": 0,
                },
            }

        self.level.elements.append(
            element
        )

        self.selected_element = (
            element
        )

        self.drawing_points.clear()

        self.status_message = (
            f"Created {self.current_tool}."
        )

    # ------------------------------------------------------------------
    # Object Creation
    # ------------------------------------------------------------------

    def create_object(
        self,
        position: pygame.Vector2,
    ) -> None:

        element = EditorElement(
            element_id=self.generate_id(
                self.current_tool
            ),

            element_type=self.current_tool,

            position=position,
        )

        if self.current_tool == "current":

            element.properties = {
                "direction": [
                    1.0,
                    0.0,
                ],

                "strength": 20,

                "radius": 100,
            }

        elif self.current_tool == "silt_cloud":

            element.properties = {
                "radius": 120,

                "visibility": 0.1,
            }

        elif self.current_tool == "thermal_vent":

            element.properties = {
                "damage": 10,

                "radius": 100,
            }

        elif self.current_tool == "fish_spawn":

            element.properties = {
                "count": 3,
            }

        elif self.current_tool == "lore_fragment":

            element.properties = {
                "text": "New lore fragment",
            }

        self.level.elements.append(
            element
        )

        self.selected_element = (
            element
        )

        self.status_message = (
            f"Created {self.current_tool}."
        )

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------

    def select_element(
        self,
        position: pygame.Vector2,
    ) -> None:

        self.selected_element = None

        for element in reversed(
            self.level.elements
        ):

            if self.element_contains_point(
                element,
                position,
            ):

                self.selected_element = (
                    element
                )

                self.status_message = (
                    f"Selected: "
                    f"{element.element_id}"
                )

                return

        self.status_message = (
            "Nothing selected."
        )

    def element_contains_point(
        self,
        element: EditorElement,
        position: pygame.Vector2,
    ) -> bool:

        if element.points:

            polygon = (
                element.get_world_points()
            )

            return self.point_in_polygon(
                position,
                polygon,
            )

        radius = self.get_element_radius(
            element
        )

        return (
            distance(
                position,
                element.position,
            )
            <= radius
        )

    @staticmethod
    def point_in_polygon(
        point: pygame.Vector2,
        polygon: list[pygame.Vector2],
    ) -> bool:

        inside = False

        j = len(polygon) - 1

        for i in range(
            len(polygon)
        ):

            xi = polygon[i].x
            yi = polygon[i].y

            xj = polygon[j].x
            yj = polygon[j].y

            if (
                (yi > point.y)
                != (yj > point.y)
            ):

                intersection_x = (
                    (xj - xi)
                    * (point.y - yi)
                    / (yj - yi)
                    + xi
                )

                if point.x < intersection_x:

                    inside = not inside

            j = i

        return inside

    # ------------------------------------------------------------------
    # Editing
    # ------------------------------------------------------------------

    def move_selected(
        self,
        movement: pygame.Vector2,
    ) -> None:

        if self.selected_element is None:
            return

        self.selected_element.position += (
            movement
            / self.zoom
        )

    def delete_selected(self) -> None:

        if self.selected_element is None:
            return

        element = (
            self.selected_element
        )

        if element in self.level.elements:

            self.level.elements.remove(
                element
            )

        self.selected_element = None

        self.status_message = (
            "Element deleted."
        )

    # ------------------------------------------------------------------
    # IDs
    # ------------------------------------------------------------------

    def generate_id(
        self,
        element_type: str,
    ) -> str:

        element_id = (
            f"{element_type}_"
            f"{self.next_element_number:03d}"
        )

        self.next_element_number += 1

        return element_id

    # ------------------------------------------------------------------
    # File Operations
    # ------------------------------------------------------------------

    def save_level(self) -> None:

        if self.current_file is None:

            filename = (
                self.level.level_id
                + ".json"
            )

            self.current_file = (
                DATA_DIRECTORY
                / filename
            )

        self.level.save(
            self.current_file
        )

        self.status_message = (
            f"Saved: "
            f"{self.current_file.name}"
        )

    def open_level(self) -> None:

        files = sorted(
            DATA_DIRECTORY.glob(
                "*.json"
            )
        )

        if not files:

            self.status_message = (
                "No level files found."
            )

            return

        # Temporary first-file loading system.
        #
        # A proper graphical file browser should be added later.

        path = files[0]

        self.level.load(
            path
        )

        self.current_file = (
            path
        )

        self.status_message = (
            f"Loaded: "
            f"{path.name}"
        )

    def new_level(self) -> None:

        self.level = LevelData()

        self.current_file = None

        self.selected_element = None

        self.drawing_points.clear()

        self.next_element_number = 1

        self.status_message = (
            "Created new level."
        )

    # ------------------------------------------------------------------
    # Camera / Coordinates
    # ------------------------------------------------------------------

    def world_to_screen(
        self,
        position: pygame.Vector2,
    ) -> pygame.Vector2:

        return (
            (
                position
                - self.camera_position
            )
            * self.zoom
        )

    def screen_to_world(
        self,
        position: pygame.Vector2,
    ) -> pygame.Vector2:

        return (
            position
            / self.zoom
            + self.camera_position
        )

    def zoom_at_mouse(
        self,
        zoom_factor: float,
    ) -> None:

        mouse_position = pygame.Vector2(
            pygame.mouse.get_pos()
        )

        before = (
            self.screen_to_world(
                mouse_position
            )
        )

        self.zoom *= zoom_factor

        self.zoom = max(
            MIN_ZOOM,
            min(
                MAX_ZOOM,
                self.zoom,
            )
        )

        after = (
            self.screen_to_world(
                mouse_position
            )
        )

        self.camera_position += (
            before
            - after
        )

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(
        self,
        dt: float,
    ) -> None:

        # Keyboard movement is intentionally
        # handled by the event system for now.

        pass

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self) -> None:

        self.screen.fill(
            BACKGROUND_COLOUR
        )

        self.draw_grid()

        self.draw_level_bounds()

        self.draw_elements()

        self.draw_entry_exit()

        self.draw_current_polygon()

        self.draw_ui()

        pygame.display.flip()

    def draw_grid(self) -> None:

        grid_size = (
            GRID_SIZE
            * self.zoom
        )

        if grid_size < 8:
            return

        start_x = (
            -(
                self.camera_position.x
                * self.zoom
            )
            % grid_size
        )

        start_y = (
            -(
                self.camera_position.y
                * self.zoom
            )
            % grid_size
        )

        for x in range(
            int(start_x),
            SCREEN_WIDTH,
            int(grid_size),
        ):

            pygame.draw.line(
                self.screen,

                GRID_COLOUR,

                (
                    x,
                    0,
                ),

                (
                    x,
                    SCREEN_HEIGHT,
                ),
            )

        for y in range(
            int(start_y),
            SCREEN_HEIGHT,
            int(grid_size),
        ):

            pygame.draw.line(
                self.screen,

                GRID_COLOUR,

                (
                    0,
                    y,
                ),

                (
                    SCREEN_WIDTH,
                    y,
                ),
            )

    def draw_level_bounds(self) -> None:

        top_left = (
            self.world_to_screen(
                pygame.Vector2(
                    0,
                    0,
                )
            )
        )

        bottom_right = (
            self.world_to_screen(
                pygame.Vector2(
                    self.level.width,
                    self.level.height,
                )
            )
        )

        rect = pygame.Rect(
            top_left.x,
            top_left.y,
            bottom_right.x
            - top_left.x,
            bottom_right.y
            - top_left.y,
        )

        pygame.draw.rect(
            self.screen,
            PANEL_BORDER_COLOUR,
            rect,
            2,
        )

    def draw_elements(self) -> None:

        for element in (
            self.level.elements
        ):

            if element.points:

                self.draw_polygon_element(
                    element
                )

            else:

                self.draw_object_element(
                    element
                )

    def draw_polygon_element(
        self,
        element: EditorElement,
    ) -> None:

        world_points = (
            element.get_world_points()
        )

        screen_points = [
            self.world_to_screen(
                point
            )
            for point in world_points
        ]

        fill_colour, outline_colour = (
            ELEMENT_COLOURS.get(
                element.element_type,
                (
                    WALL_COLOUR,
                    WALL_OUTLINE_COLOUR,
                ),
            )
        )

        pygame.draw.polygon(
            self.screen,
            fill_colour,
            screen_points,
        )

        pygame.draw.lines(
            self.screen,
            outline_colour,
            True,
            screen_points,
            max(
                1,
                int(
                    2
                    * self.zoom
                ),
            ),
        )

        for point in screen_points:

            pygame.draw.circle(
                self.screen,
                outline_colour,
                (
                    round(point.x),
                    round(point.y),
                ),
                max(
                    2,
                    round(
                        POINT_RADIUS
                        * self.zoom
                    ),
                ),
            )

        if (
            element
            is self.selected_element
        ):

            pygame.draw.lines(
                self.screen,
                (
                    255,
                    255,
                    255,
                ),
                True,
                screen_points,
                3,
            )

    def draw_object_element(
        self,
        element: EditorElement,
    ) -> None:

        screen_position = (
            self.world_to_screen(
                element.position
            )
        )

        radius = (
            self.get_element_radius(
                element
            )
            * self.zoom
        )

        fill_colour, _ = (
            ELEMENT_COLOURS.get(
                element.element_type,
                (
                    255,
                    255,
                    255,
                ),
            )
        )

        pygame.draw.circle(
            self.screen,

            fill_colour,

            (
                round(
                    screen_position.x
                ),
                round(
                    screen_position.y
                ),
            ),

            max(
                4,
                round(
                    radius
                ),
            ),
        )

        if (
            element
            is self.selected_element
        ):

            pygame.draw.circle(
                self.screen,

                (
                    255,
                    255,
                    255,
                ),

                (
                    round(
                        screen_position.x
                    ),
                    round(
                        screen_position.y
                    ),
                ),

                max(
                    8,
                    round(
                        radius + 5
                    ),
                ),

                2,
            )

    def draw_entry_exit(self) -> None:

        entry = (
            self.world_to_screen(
                self.level.entry_position
            )
        )

        exit_position = (
            self.world_to_screen(
                self.level.exit_position
            )
        )

        pygame.draw.circle(
            self.screen,
            ENTRY_COLOUR,
            (
                round(entry.x),
                round(entry.y),
            ),
            10,
        )

        pygame.draw.circle(
            self.screen,
            EXIT_COLOUR,
            (
                round(exit_position.x),
                round(exit_position.y),
            ),
            10,
        )

        self.draw_text(
            "ENTRY",
            (
                entry.x + 12,
                entry.y - 10,
            ),
            ENTRY_COLOUR,
        )

        self.draw_text(
            "EXIT",
            (
                exit_position.x + 12,
                exit_position.y - 10,
            ),
            EXIT_COLOUR,
        )

    def draw_current_polygon(self) -> None:

        if not self.drawing_points:
            return

        screen_points = [
            self.world_to_screen(
                point
            )
            for point in self.drawing_points
        ]

        if len(
            screen_points
        ) >= 2:

            pygame.draw.lines(
                self.screen,

                (
                    255,
                    255,
                    255,
                ),

                False,

                screen_points,

                2,
            )

        for point in screen_points:

            pygame.draw.circle(
                self.screen,

                (
                    255,
                    255,
                    255,
                ),

                (
                    round(point.x),
                    round(point.y),
                ),

                5,
            )

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def draw_ui(self) -> None:

        pygame.draw.rect(
            self.screen,

            PANEL_COLOUR,

            (
                0,
                0,
                SCREEN_WIDTH,
                70,
            ),
        )

        title = (
            f"Tool: "
            f"{TOOL_NAMES.get(
                self.current_tool,
                self.current_tool,
            )}"
        )

        self.draw_text(
            title,
            (
                15,
                10,
            ),
            TEXT_COLOUR,
        )

        self.draw_text(
            (
                f"Level: "
                f"{self.level.name}"
            ),
            (
                15,
                35,
            ),
            TEXT_COLOUR,
        )

        controls = (
            "V Select | "
            "1 Wall | "
            "2 Obstacle | "
            "3 Current | "
            "4 Silt | "
            "5 Vent | "
            "6 Fish | "
            "7 Lore | "
            "E Entry | "
            "X Exit"
        )

        self.draw_text(
            controls,
            (
                330,
                10,
            ),
            TEXT_COLOUR,
            small=True,
        )

        self.draw_text(
            (
                "Right-click finish polygon | "
                "Middle-drag pan | "
                "Wheel zoom | "
                "S save | "
                "O open | "
                "N new"
            ),
            (
                330,
                35,
            ),
            TEXT_COLOUR,
            small=True,
        )

        status_rect = pygame.Rect(
            0,
            SCREEN_HEIGHT - 35,
            SCREEN_WIDTH,
            35,
        )

        pygame.draw.rect(
            self.screen,
            PANEL_COLOUR,
            status_rect,
        )

        self.draw_text(
            self.status_message,
            (
                10,
                SCREEN_HEIGHT - 27,
            ),
            TEXT_COLOUR,
        )

        if self.selected_element:

            self.draw_text(
                (
                    "Selected: "
                    f"{self.selected_element.element_id}"
                    " | "
                    f"{TOOL_NAMES.get(
                        self.selected_element.element_type,
                        self.selected_element.element_type,
                    )}"
                ),
                (
                    600,
                    SCREEN_HEIGHT - 27,
                ),
                TEXT_COLOUR,
            )

    def draw_text(
        self,
        text: str,
        position: tuple[float, float],
        colour: tuple[int, int, int],
        small: bool = False,
    ) -> None:

        font = (
            self.small_font
            if small
            else self.font
        )

        surface = font.render(
            text,
            True,
            colour,
        )

        self.screen.blit(
            surface,
            position,
        )

    # ------------------------------------------------------------------
    # Miscellaneous
    # ------------------------------------------------------------------

    @staticmethod
    def get_element_radius(
        element: EditorElement,
    ) -> float:

        radius = element.properties.get(
            "radius",
            20,
        )

        return float(
            radius
        )


# ---------------------------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Starts the cave level editor.
    """

    editor = LevelEditor()

    editor.run()


if __name__ == "__main__":
    main()