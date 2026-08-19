from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any
import logging
import traceback

import pygame

from model import DIRECTIONS, ENTITY_DEFINITIONS, ITEM_PRESET_IDS, Element, Level


WIDTH, HEIGHT = 1440, 900
SIDEBAR = 330
TOPBAR = 58
STATUSBAR = 30

BG = (13, 19, 24)
PANEL = (24, 32, 39)
PANEL_2 = (31, 41, 49)
BORDER = (62, 76, 86)
TEXT = (225, 233, 238)
MUTED = (150, 164, 173)
ACCENT = (70, 190, 180)
WHITE = (245, 245, 245)
RED = (225, 90, 90)
GREEN = (85, 205, 120)
GRID = (34, 47, 56)
GRID_MAJOR = (47, 61, 71)

DATA_DIR = (Path(__file__).resolve().parents[1] / "TheTwilightZone" / "data" / "cave_sections").resolve()
LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "level_creator.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("twilightzone.levelcreator")
SECTION_FILENAME_RE = re.compile(r"^section_(\d+)\.json$")


class LevelEditor:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("The Twilight Zone — Level Creator")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()

        self.font = pygame.font.Font(None, 21)
        self.small = pygame.font.Font(None, 17)
        self.title = pygame.font.Font(None, 27)
        self.mono = pygame.font.Font(None, 18)

        self.level = Level()
        self.current_file: Path | None = None
        self.tool = "select"
        self.selected: Element | None = None
        self.drawing: list[list[float]] = []

        self.camera = pygame.Vector2(0, 0)
        self.zoom = 0.85
        self.dragging = False
        self.dragging_element = False
        self.last_mouse = pygame.Vector2()
        self.drag_origin_world = pygame.Vector2()
        self.drag_origin_element = pygame.Vector2()
        self.running = True

        self.status = "Ready"
        logger.info("Editor started; data_dir=%s", DATA_DIR)
        self.status_error = False

        self.history: list[dict[str, Any]] = []
        self.future: list[dict[str, Any]] = []
        self.typing_field: str | None = None
        self.typing_value = ""

        self.tool_order = [
            "select",
            "wall",
            "obstacle",
            "fish_spawn",
            "spiky_plant",
            "thermal_vent",
            "silt_cloud",
            "current",
            "item",
            "lore_fragment",
        ]

        self.ensure_data_dir()
        self.fit_level()

    # ---------- state ----------

    def ensure_data_dir(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def snapshot(self) -> dict[str, Any]:
        return copy.deepcopy(self.level.to_dict())

    def restore_snapshot(self, snap: dict[str, Any]) -> None:
        self.level = Level.from_dict(snap)
        self.selected = None

    def commit(self) -> None:
        self.history.append(self.snapshot())
        logger.debug("Committed edit; history=%d", len(self.history))
        if len(self.history) > 80:
            self.history.pop(0)
        self.future.clear()

    def undo(self) -> None:
        if not self.history:
            self.set_status("Nothing to undo.", error=True)
            return
        logger.info("Undo requested")
        self.future.append(self.snapshot())
        self.restore_snapshot(self.history.pop())
        self.set_status("Undo.")

    def redo(self) -> None:
        if not self.future:
            self.set_status("Nothing to redo.", error=True)
            return
        logger.info("Redo requested")
        self.history.append(self.snapshot())
        self.restore_snapshot(self.future.pop())
        self.set_status("Redo.")

    def set_status(self, text: str, error: bool = False) -> None:
        self.status = text
        self.status_error = error
        logger.warning(text) if error else logger.info(text)

    def next_id(self, element_type: str) -> str:
        prefix = element_type
        used = {e.element_id for e in self.level.elements}
        n = 1
        while f"{prefix}_{n:03d}" in used:
            n += 1
        return f"{prefix}_{n:03d}"

    # ---------- coordinate system ----------

    def canvas_rect(self) -> pygame.Rect:
        w, h = self.screen.get_size()
        return pygame.Rect(0, TOPBAR, max(1, w - SIDEBAR), max(1, h - TOPBAR - STATUSBAR))

    def world_to_screen(self, p: pygame.Vector2) -> pygame.Vector2:
        c = self.canvas_rect()
        return pygame.Vector2(
            c.left + (p.x - self.camera.x) * self.zoom,
            c.top + (p.y - self.camera.y) * self.zoom,
        )

    def screen_to_world(self, p: pygame.Vector2) -> pygame.Vector2:
        c = self.canvas_rect()
        return pygame.Vector2(
            (p.x - c.left) / self.zoom + self.camera.x,
            (p.y - c.top) / self.zoom + self.camera.y,
        )

    def fit_level(self) -> None:
        c = self.canvas_rect()
        self.zoom = min(c.width / self.level.width, c.height / self.level.height) * 0.92
        self.zoom = max(0.25, min(3.0, self.zoom))
        self.camera.x = self.level.width / 2 - c.width / (2 * self.zoom)
        self.camera.y = self.level.height / 2 - c.height / (2 * self.zoom)

    def zoom_at(self, factor: float, mouse: pygame.Vector2) -> None:
        before = self.screen_to_world(mouse)
        self.zoom = max(0.2, min(4.0, self.zoom * factor))
        after = self.screen_to_world(mouse)
        self.camera += before - after

    # ---------- input ----------

    def run(self) -> None:
        try:
            while self.running:
                dt = self.clock.tick(60) / 1000.0
                self.handle_events()
                self.draw()
        except Exception:
            logger.exception("Fatal editor exception")
            raise
        finally:
            pygame.quit()

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)

            elif event.type == pygame.KEYDOWN:
                self.key_down(event)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.mouse_down(event)

            elif event.type == pygame.MOUSEBUTTONUP:
                self.mouse_up(event)

            elif event.type == pygame.MOUSEMOTION:
                self.mouse_motion(event)

            elif event.type == pygame.MOUSEWHEEL:
                self.zoom_at(1.12 if event.y > 0 else 1 / 1.12, pygame.Vector2(pygame.mouse.get_pos()))

    def key_down(self, event: pygame.event.Event) -> None:
        if self.typing_field is not None:
            if event.key == pygame.K_ESCAPE:
                self.typing_field = None
                return
            if event.key == pygame.K_RETURN:
                self.apply_typed_field()
                return
            if event.key == pygame.K_BACKSPACE:
                self.typing_value = self.typing_value[:-1]
                return
            if event.unicode and event.unicode.isprintable():
                self.typing_value += event.unicode
            return

        mods = pygame.key.get_mods()
        if event.key == pygame.K_z and mods & pygame.KMOD_CTRL:
            self.undo()
            return
        if event.key == pygame.K_y and mods & pygame.KMOD_CTRL:
            self.redo()
            return
        if event.key == pygame.K_s and mods & pygame.KMOD_CTRL:
            self.save_level()
            return
        if event.key == pygame.K_F4:
            self.save_as_dialog()
            return
        if event.key == pygame.K_o and mods & pygame.KMOD_CTRL:
            self.open_level_dialog()
            return
        if event.key == pygame.K_n and mods & pygame.KMOD_CTRL:
            self.new_level()
            return

        if event.key == pygame.K_ESCAPE:
            self.drawing.clear()
            self.selected = None
            self.tool = "select"
            self.set_status("Selection cleared.")
            return

        if event.key == pygame.K_DELETE:
            self.delete_selected()
            return

        if event.key == pygame.K_f:
            self.fit_level()
            return

        if event.key == pygame.K_r and self.selected:
            self.rotate_selected()
            return

        if event.key == pygame.K_q:
            self.tool = "select"
            return

        number_tools = {
            pygame.K_1: "wall",
            pygame.K_2: "obstacle",
            pygame.K_3: "fish_spawn",
            pygame.K_4: "spiky_plant",
            pygame.K_5: "thermal_vent",
            pygame.K_6: "silt_cloud",
            pygame.K_7: "current",
            pygame.K_8: "item",
            pygame.K_9: "lore_fragment",
        }
        if event.key in number_tools:
            self.tool = number_tools[event.key]
            self.drawing.clear()
            return

        if self.selected:
            delta = pygame.Vector2()
            if event.key == pygame.K_LEFT:
                delta.x = -1
            elif event.key == pygame.K_RIGHT:
                delta.x = 1
            elif event.key == pygame.K_UP:
                delta.y = -1
            elif event.key == pygame.K_DOWN:
                delta.y = 1
            if delta.length_squared():
                self.commit()
                self.selected.x += delta.x
                self.selected.y += delta.y
                if self.selected.element_type == "wall":
                    self.clip_element_to_bounds(self.selected)

    def mouse_down(self, event: pygame.event.Event) -> None:
        pos = pygame.Vector2(event.pos)

        if event.button == 2:
            self.dragging = True
            self.last_mouse = pos
            return

        if event.button != 1:
            return

        if not self.canvas_rect().collidepoint(pos):
            self.handle_sidebar_click(pos)
            return

        world = self.screen_to_world(pos)
        if self.tool == "select":
            if self.selected and self.contains(self.selected, world):
                self.begin_drag_selected(pos, world)
                return
            self.select_at(world)
        elif self.tool in ("wall", "obstacle"):
            self.drawing.append([world.x, world.y])
        elif self.tool in ENTITY_DEFINITIONS:
            self.place_object(self.tool, world)

    def mouse_up(self, event: pygame.event.Event) -> None:
        if event.button == 2:
            self.dragging = False
        elif event.button == 1 and self.dragging_element:
            self.finish_drag_selected()
        elif event.button == 3 and self.tool in ("wall", "obstacle"):
            self.finish_polygon()

    def mouse_motion(self, event: pygame.event.Event) -> None:
        if self.dragging_element and self.selected:
            self.move_dragged_element(pygame.Vector2(event.pos))
            return
        if not self.dragging:
            return
        pos = pygame.Vector2(event.pos)
        self.camera -= (pos - self.last_mouse) / self.zoom
        self.last_mouse = pos

    def begin_drag_selected(self, mouse_pos: pygame.Vector2, world_pos: pygame.Vector2 | None = None) -> None:
        if not self.selected:
            return
        self.commit()
        self.dragging_element = True
        self.drag_origin_world = world_pos if world_pos is not None else self.screen_to_world(mouse_pos)
        self.drag_origin_element = pygame.Vector2(self.selected.x, self.selected.y)
        self.set_status(f"Dragging {self.selected.element_id}.")

    def move_dragged_element(self, mouse_pos: pygame.Vector2) -> None:
        if not self.selected or not self.dragging_element:
            return
        world = self.screen_to_world(mouse_pos)
        delta = world - self.drag_origin_world
        self.selected.x = self.drag_origin_element.x + delta.x
        self.selected.y = self.drag_origin_element.y + delta.y
        if self.selected.element_type == "wall":
            self.clip_element_to_bounds(self.selected)

    def finish_drag_selected(self) -> None:
        self.dragging_element = False
        if self.selected:
            self.set_status(f"Moved {self.selected.element_id}.")

    # ---------- editing ----------

    def place_object(self, element_type: str, world: pygame.Vector2) -> None:
        self.commit()
        definition = ENTITY_DEFINITIONS[element_type]
        props: dict[str, Any] = {}
        for field, (_, default) in definition.get("fields", {}).items():
            if field in ("direction_x", "direction_y"):
                continue
            props[field] = copy.deepcopy(default)

        if element_type == "fish_spawn":
            props["direction"] = [1.0, 0.0]
        elif element_type == "current":
            props["direction"] = [1.0, 0.0]
        elif element_type == "thermal_vent":
            props["direction"] = [1.0, 0.0]

        e = Element(
            self.next_id(element_type),
            element_type,
            world.x,
            world.y,
            properties=props,
        )
        self.level.elements.append(e)
        self.selected = e
        logger.info("Placed %s id=%s at=(%.2f, %.2f)", element_type, e.element_id, e.x, e.y)
        self.set_status(f"Placed {definition['label']}.")

    def finish_polygon(self) -> None:
        if len(self.drawing) < 3:
            self.drawing.clear()
            self.set_status("Polygon needs at least 3 points.", error=True)
            return

        self.commit()

        # Walls are clipped to the level rectangle before they become an element.
        # This prevents the editor from ever writing wall geometry outside the
        # playable bounds. The clipping is done in world coordinates so only the
        # portion inside the cave survives.
        world_points = [(float(x), float(y)) for x, y in self.drawing]
        if self.tool == "wall":
            world_points = self.clip_polygon_to_bounds(
                world_points, self.level.width, self.level.height
            )
            if len(world_points) < 3 or abs(self.polygon_area(world_points)) < 1e-3:
                self.drawing.clear()
                self.set_status("Wall is completely outside the level bounds.", error=True)
                logger.warning("Rejected wall: no geometry remained after bounds clipping")
                return

        min_x = min(p[0] for p in world_points)
        min_y = min(p[1] for p in world_points)
        local = [[x - min_x, y - min_y] for x, y in world_points]

        material = {}
        if self.tool == "wall":
            material = {
                "texture": None,
                "mapping": {
                    "mode": "world",
                    "origin": [0, 0],
                    "scale": [1.0, 1.0],
                    "rotation": 0,
                },
            }

        e = Element(
            self.next_id(self.tool),
            self.tool,
            min_x,
            min_y,
            points=local,
            material=material,
        )
        self.level.elements.append(e)
        self.selected = e
        self.drawing.clear()
        self.set_status(f"Created {self.tool}.")

    @staticmethod
    def polygon_area(points: list[tuple[float, float]]) -> float:
        return 0.5 * sum(
            points[i][0] * points[(i + 1) % len(points)][1]
            - points[(i + 1) % len(points)][0] * points[i][1]
            for i in range(len(points))
        )

    @staticmethod
    def clip_polygon_to_bounds(
        points: list[tuple[float, float]], width: float, height: float
    ) -> list[tuple[float, float]]:
        """Sutherland-Hodgman clip against the rectangular level bounds."""
        def clip(poly, inside, intersect):
            if not poly:
                return []
            out = []
            previous = poly[-1]
            previous_inside = inside(previous)
            for current in poly:
                current_inside = inside(current)
                if current_inside != previous_inside:
                    out.append(intersect(previous, current))
                if current_inside:
                    out.append(current)
                previous, previous_inside = current, current_inside
            return out

        def vertical(boundary, previous, current):
            x1, y1 = previous; x2, y2 = current
            dx = x2 - x1
            if abs(dx) < 1e-9:
                return (boundary, y1)
            t = (boundary - x1) / dx
            return (boundary, y1 + (y2 - y1) * t)

        def horizontal(boundary, previous, current):
            x1, y1 = previous; x2, y2 = current
            dy = y2 - y1
            if abs(dy) < 1e-9:
                return (x1, boundary)
            t = (boundary - y1) / dy
            return (x1 + (x2 - x1) * t, boundary)

        poly = points
        poly = clip(poly, lambda p: p[0] >= 0, lambda a,b: vertical(0, a,b))
        poly = clip(poly, lambda p: p[0] <= width, lambda a,b: vertical(width, a,b))
        poly = clip(poly, lambda p: p[1] >= 0, lambda a,b: horizontal(0, a,b))
        poly = clip(poly, lambda p: p[1] <= height, lambda a,b: horizontal(height, a,b))

        # Remove consecutive duplicates created by clipping.
        cleaned = []
        for point in poly:
            if not cleaned or abs(point[0] - cleaned[-1][0]) > 1e-6 or abs(point[1] - cleaned[-1][1]) > 1e-6:
                cleaned.append(point)
        if len(cleaned) > 1 and abs(cleaned[0][0] - cleaned[-1][0]) < 1e-6 and abs(cleaned[0][1] - cleaned[-1][1]) < 1e-6:
            cleaned.pop()
        return cleaned

    def clip_element_to_bounds(self, e: Element) -> None:
        if e.element_type != "wall" or not e.points:
            return
        world_points = [(e.x + p[0], e.y + p[1]) for p in e.points]
        clipped = self.clip_polygon_to_bounds(world_points, self.level.width, self.level.height)
        if len(clipped) < 3 or abs(self.polygon_area(clipped)) < 1e-3:
            logger.warning("Wall %s moved/rotated completely out of bounds; removing it", e.element_id)
            self.level.elements = [item for item in self.level.elements if item.element_id != e.element_id]
            if self.selected is e:
                self.selected = None
            self.set_status(f"Wall {e.element_id} left the level and was removed.", error=True)
            return
        min_x = min(x for x, _ in clipped)
        min_y = min(y for _, y in clipped)
        e.x = min_x
        e.y = min_y
        e.points = [[x - min_x, y - min_y] for x, y in clipped]
        logger.debug("Clipped wall %s to level bounds", e.element_id)

    def select_at(self, world: pygame.Vector2) -> None:
        self.selected = None
        for e in reversed(self.level.elements):
            if self.contains(e, world):
                self.selected = e
                self.set_status(f"Selected {e.element_id}.")
                return
        self.set_status("Nothing selected.")

    def contains(self, e: Element, p: pygame.Vector2) -> bool:
        if e.points:
            poly = [pygame.Vector2(e.x + x, e.y + y) for x, y in e.points]
            return self.point_in_poly(p, poly)

        definition = ENTITY_DEFINITIONS.get(e.element_type, {})
        if e.element_type == "current":
            w = float(e.properties.get("width", definition.get("default_width", 100)))
            h = float(e.properties.get("height", definition.get("default_height", 100)))
            return pygame.Rect(e.x - w/2, e.y - h/2, w, h).collidepoint(p.x, p.y)

        r = float(e.properties.get("radius", definition.get("default_radius", 20)))
        return p.distance_to((e.x, e.y)) <= r

    @staticmethod
    def point_in_poly(p: pygame.Vector2, poly: list[pygame.Vector2]) -> bool:
        inside = False
        j = len(poly) - 1
        for i in range(len(poly)):
            xi, yi = poly[i]
            xj, yj = poly[j]
            if ((yi > p.y) != (yj > p.y)) and (p.x < (xj - xi) * (p.y - yi) / ((yj - yi) or 1e-9) + xi):
                inside = not inside
            j = i
        return inside

    def delete_selected(self) -> None:
        if not self.selected:
            self.set_status("Nothing selected.", error=True)
            return

        selected_id = self.selected.element_id
        if not any(e.element_id == selected_id for e in self.level.elements):
            self.selected = None
            self.typing_field = None
            self.set_status("Selection was stale; cleared it.", error=True)
            return

        self.commit()
        before = len(self.level.elements)
        self.level.elements = [
            e for e in self.level.elements if e.element_id != selected_id
        ]
        logger.info("Deleted id=%s", selected_id)
        removed = before - len(self.level.elements)
        self.selected = None
        self.typing_field = None
        self.typing_value = ""
        self.set_status(f"Deleted {selected_id}.") if removed else self.set_status(
            f"Could not delete {selected_id}.", error=True
        )

    def rotate_selected(self) -> None:
        if not self.selected:
            return
        e = self.selected
        if e.element_type in ("fish_spawn", "current", "thermal_vent"):
            self.commit()
            d = e.properties.get("direction", [1.0, 0.0])
            e.properties["direction"] = [-float(d[1]), float(d[0])]
            self.set_status("Rotated direction.")
        elif e.points:
            self.commit()
            cx = sum(p[0] for p in e.points) / len(e.points)
            cy = sum(p[1] for p in e.points) / len(e.points)
            e.points = [[-(y-cy)+cx, (x-cx)+cy] for x, y in e.points]
            if e.element_type == "wall":
                self.clip_element_to_bounds(e)
            self.set_status("Rotated polygon.")

    # ---------- files ----------

    def new_level(self) -> None:
        self.level = Level()
        self.current_file = None
        self.selected = None
        self.drawing.clear()
        self.typing_field = None
        self.typing_value = ""
        self.history.clear()
        self.future.clear()
        self.fit_level()
        self.set_status("New unsaved level created.")

    def selector_level_files(self) -> list[Path]:
        return sorted(DATA_DIR.glob("*.json"))

    def is_current_file_active_in_selector(self) -> bool:
        if self.current_file is None:
            return False
        return any(path == self.current_file for path in self.selector_level_files())

    def next_available_section_path(self) -> Path:
        used_numbers: set[int] = set()
        for path in self.selector_level_files():
            match = SECTION_FILENAME_RE.match(path.name)
            if match:
                used_numbers.add(int(match.group(1)))

        next_number = 1
        while next_number in used_numbers:
            next_number += 1

        return DATA_DIR / f"section_{next_number:02d}.json"

    def save_level(self, assign_new_if_inactive: bool = True) -> None:
        created_new_slot = False
        if assign_new_if_inactive and not self.is_current_file_active_in_selector():
            self.current_file = self.next_available_section_path()
            self.level.level_id = self.current_file.stem
            self.level.name = self.level.name or self.level.level_id
            created_new_slot = True
        elif self.current_file is None:
            self.current_file = DATA_DIR / f"{self.level.level_id}.json"

        errors = self.level.validate()
        if errors:
            self.set_status(f"Cannot save: {errors[0]}", error=True)
            return
        self.level.save(self.current_file)
        logger.info("Saved level id=%s path=%s elements=%d", self.level.level_id, self.current_file, len(self.level.elements))
        if created_new_slot:
            self.set_status(f"Saved new level {self.current_file.name}.")
        else:
            self.set_status(f"Saved {self.current_file.name}.")

    def open_level_dialog(self) -> None:
        files = self.selector_level_files()
        if not files:
            self.set_status("No JSON levels found in levelcreator/levels.", error=True)
            return
        # Open the first level for keyboard-driven minimal mode.
        # The file list is also shown in the sidebar.
        self.open_level(files[0])

    def open_level(self, path: Path) -> None:
        try:
            self.commit()
            logger.info("Loading level path=%s", path)
            self.level = Level.load(path)
            self.current_file = path
            self.selected = None
            self.drawing.clear()
            self.fit_level()
            self.set_status(f"Loaded {path.name}.")
        except Exception as exc:
            logger.exception("Load failed for %s", path)
            self.set_status(f"Load failed: {exc}", error=True)

    # ---------- sidebar ----------

    def sidebar_rect(self) -> pygame.Rect:
        w, h = self.screen.get_size()
        return pygame.Rect(w - SIDEBAR, TOPBAR, SIDEBAR, h - TOPBAR - STATUSBAR)

    def handle_sidebar_click(self, pos: pygame.Vector2) -> None:
        rect = self.sidebar_rect()
        if not rect.collidepoint(pos):
            return

        # Tool buttons occupy the left column only.
        y = rect.top + 42
        for i, tool in enumerate(self.tool_order[:10]):
            button = pygame.Rect(rect.left + 12, y, 145, 30)
            if button.collidepoint(pos):
                self.commit()
                self.tool = tool
                self.drawing.clear()
                self.typing_field = None
                self.set_status(f"Tool: {tool}")
                return
            y += 34

        # File list occupies the right column only.
        for i, path in enumerate(self.selector_level_files()[:8]):
            button = pygame.Rect(rect.left + 160, rect.top + 42 + i * 27, 158, 24)
            if button.collidepoint(pos):
                self.open_level(path)
                return

        # Inspector is below the divider. It must never intercept tool/file clicks.
        if self.selected:
            self.handle_inspector_click(pos)

    def handle_inspector_click(self, pos: pygame.Vector2) -> None:
        rect = self.sidebar_rect()
        iy = rect.top + 410
        if pos.y < iy + 80:
            return

        fields = []
        definition = ENTITY_DEFINITIONS.get(self.selected.element_type, {})
        for name, (kind, default) in definition.get("fields", {}).items():
            if name in ("direction_x", "direction_y"):
                continue
            fields.append((name, kind, default))

        y = iy + 86
        for name, kind, default in fields:
            row = pygame.Rect(rect.left + 12, y, 305, 25)
            if row.collidepoint(pos):
                if kind == "item_id":
                    self.commit()
                    current = str(self.selected.properties.get(name, default))
                    try:
                        next_index = (ITEM_PRESET_IDS.index(current) + 1) % len(ITEM_PRESET_IDS)
                    except ValueError:
                        next_index = 0
                    self.selected.properties[name] = ITEM_PRESET_IDS[next_index]
                    self.set_status(f"Item preset: {ITEM_PRESET_IDS[next_index]}.")
                    return
                self.typing_field = name
                self.typing_value = str(self.selected.properties.get(name, default))
                self.set_status(f"Editing {name}; Enter applies, Esc cancels.")
                return
            y += 29

    def save_as_dialog(self) -> None:
        # Simple in-app filename prompt. Avoids relying on platform-specific dialogs.
        self.typing_field = "__filename__"
        self.typing_value = self.level.level_id
        self.set_status("Type a filename in the inspector area, then press Enter. Esc cancels.")

    def apply_typed_field(self) -> None:
        if self.typing_field == "__filename__":
            name = self.typing_value.strip()
            if not name:
                self.set_status("Filename cannot be empty.", error=True)
                return
            if not name.lower().endswith(".json"):
                name += ".json"
            safe = Path(name).name
            if safe in (".", "..") or not safe:
                self.set_status("Invalid filename.", error=True)
                return
            self.current_file = DATA_DIR / safe
            self.level.level_id = Path(safe).stem
            self.level.name = self.level.name or self.level.level_id
            self.typing_field = None
            self.typing_value = ""
            self.save_level(assign_new_if_inactive=False)
            return

        if not self.selected or self.typing_field is None:
            return
        name = self.typing_field
        raw = self.typing_value
        kind = ENTITY_DEFINITIONS.get(self.selected.element_type, {}).get("fields", {}).get(name, ("str", ""))[0]
        try:
            if kind == "int":
                value: Any = int(raw)
            elif kind == "float":
                value = float(raw)
            else:
                value = raw
            self.commit()
            self.selected.properties[name] = value
            self.typing_field = None
            self.typing_value = ""
            self.set_status(f"Updated {name}.")
        except ValueError:
            self.set_status(f"Invalid value for {name}.", error=True)

    # ---------- drawing ----------

    def draw(self) -> None:
        self.screen.fill(BG)
        self.draw_topbar()
        self.draw_canvas()
        self.draw_sidebar()
        self.draw_statusbar()
        pygame.display.flip()

    def draw_topbar(self) -> None:
        pygame.draw.rect(self.screen, PANEL, (0, 0, self.screen.get_width(), TOPBAR))
        pygame.draw.line(self.screen, BORDER, (0, TOPBAR-1), (self.screen.get_width(), TOPBAR-1))
        self.text("THE TWILIGHT ZONE  /  LEVEL CREATOR", (16, 16), self.title, TEXT)
        self.text(f"{self.level.level_id}   {self.level.width}×{self.level.height}", (500, 19), self.font, MUTED)
        controls = "Ctrl+S Save   Ctrl+O Open   Ctrl+N New   Ctrl+Z Undo   Ctrl+Y Redo   F Fit   R Rotate"
        self.text(controls, (760, 20), self.small, MUTED)

    def draw_canvas(self) -> None:
        c = self.canvas_rect()
        pygame.draw.rect(self.screen, BG, c)
        self.draw_grid(c)
        self.draw_level_bounds()
        self.draw_elements()
        self.draw_entry_exit()
        self.draw_drawing()
        self.draw_cursor_hint()

    def draw_grid(self, c: pygame.Rect) -> None:
        step = 32 * self.zoom
        if step < 7:
            return
        start_x = c.left - ((self.camera.x * self.zoom) % step)
        start_y = c.top - ((self.camera.y * self.zoom) % step)
        x = start_x
        while x < c.right:
            major = round((x - c.left) / step) % 4 == 0
            pygame.draw.line(self.screen, GRID_MAJOR if major else GRID, (round(x), c.top), (round(x), c.bottom))
            x += step
        y = start_y
        while y < c.bottom:
            major = round((y - c.top) / step) % 4 == 0
            pygame.draw.line(self.screen, GRID_MAJOR if major else GRID, (c.left, round(y)), (c.right, round(y)))
            y += step

    def draw_level_bounds(self) -> None:
        tl = self.world_to_screen(pygame.Vector2(0, 0))
        br = self.world_to_screen(pygame.Vector2(self.level.width, self.level.height))
        pygame.draw.rect(self.screen, BORDER, pygame.Rect(tl.x, tl.y, br.x-tl.x, br.y-tl.y), 2)

    def draw_elements(self) -> None:
        for e in self.level.elements:
            self.draw_element(e)

    def draw_element(self, e: Element) -> None:
        definition = ENTITY_DEFINITIONS.get(e.element_type, {})
        colour = definition.get("colour", WHITE)

        if e.points:
            pts = [self.world_to_screen(pygame.Vector2(e.x+x, e.y+y)) for x, y in e.points]
            if len(pts) >= 3:
                pygame.draw.polygon(self.screen, colour, [(p.x, p.y) for p in pts])
                pygame.draw.lines(self.screen, WHITE if e is self.selected else colour, True, [(p.x, p.y) for p in pts], max(1, round(2*self.zoom)))
        elif e.element_type == "current":
            w = float(e.properties.get("width", 260))
            h = float(e.properties.get("height", 120))
            center = self.world_to_screen(pygame.Vector2(e.x, e.y))
            rr = pygame.Rect(center.x - w*self.zoom/2, center.y - h*self.zoom/2, w*self.zoom, h*self.zoom)
            pygame.draw.rect(self.screen, (*colour, 75), rr)
            pygame.draw.rect(self.screen, colour, rr, max(1, round(2*self.zoom)))
            d = pygame.Vector2(e.properties.get("direction", [1,0]))
            if d.length_squared():
                d = d.normalize()
            end = center + d * min(w, h) * self.zoom * 0.35
            pygame.draw.line(self.screen, WHITE, center, end, 3)
            self.arrowhead(center, end, WHITE)
        else:
            radius = float(e.properties.get("radius", definition.get("default_radius", 20))) * self.zoom
            center = self.world_to_screen(pygame.Vector2(e.x, e.y))
            pygame.draw.circle(self.screen, colour, (round(center.x), round(center.y)), max(4, round(radius)), 0 if e.element_type != "silt_cloud" else 2)
            if e.element_type == "fish_spawn":
                self.arrow_at(center, e.properties.get("direction", [1,0]), colour)
            if e.element_type == "thermal_vent":
                heat = float(e.properties.get("heat_radius", 100)) * self.zoom
                pygame.draw.circle(self.screen, (*colour, 80), (round(center.x), round(center.y)), max(4, round(heat)), 1)
                self.draw_thermal_vent_preview(e, center, colour)

        if e is self.selected:
            self.draw_selection(e)

        label_pos = self.world_to_screen(pygame.Vector2(e.x, e.y))
        self.text(e.element_id, (label_pos.x + 8, label_pos.y - 18), self.small, TEXT)

    def draw_selection(self, e: Element) -> None:
        if e.points:
            pts = [self.world_to_screen(pygame.Vector2(e.x+x, e.y+y)) for x, y in e.points]
            pygame.draw.lines(self.screen, WHITE, True, [(p.x,p.y) for p in pts], 3)
        else:
            p = self.world_to_screen(pygame.Vector2(e.x, e.y))
            pygame.draw.circle(self.screen, WHITE, (round(p.x), round(p.y)), 10, 2)

    def draw_thermal_vent_preview(
        self,
        e: Element,
        center: pygame.Vector2,
        colour: tuple[int, int, int],
    ) -> None:
        direction = pygame.Vector2(e.properties.get("direction", [1.0, 0.0]))
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1.0, 0.0)
        else:
            direction = direction.normalize()

        side = pygame.Vector2(-direction.y, direction.x)
        haze_length = max(18.0, float(e.properties.get("haze_length", 95.0)) * self.zoom)
        haze_width = max(8.0, float(e.properties.get("haze_width", 30.0)) * self.zoom)

        # Yellow-to-orange plume that originates from the vent mouth.
        for i in range(14):
            t = (i + 1) / 14.0
            start = center + direction * (haze_length * (t - 0.12))
            end = center + direction * (haze_length * t)
            half_width = haze_width * (0.12 + (1.0 - t) * 0.9)
            polygon = [
                start - side * half_width,
                end + side * half_width * 0.7,
                end - side * half_width * 0.7,
                start + side * half_width,
            ]
            color_t = min(1.0, t * 1.2)
            red = 255
            green = int(240 - (240 - 150) * color_t)
            blue = int(70 + (180 - 70) * (1.0 - color_t))
            alpha = int(80 + (170 - 80) * (1.0 - t))
            pygame.draw.polygon(self.screen, (red, green, blue, alpha), [(p.x, p.y) for p in polygon])

        bubble_count = max(6, int(e.properties.get("bubble_count", 14)))
        bubble_spread = max(2.0, float(e.properties.get("bubble_spread", 15.0)) * self.zoom)
        for i in range(bubble_count):
            t = (i + 1) / (bubble_count + 1)
            wobble = ((i % 2) * 2 - 1) * bubble_spread * 0.5 * (0.3 + (1.0 - t))
            bubble_pos = center + direction * (haze_length * t) + side * wobble
            bubble_radius = max(1, round((1.0 - t) * 2.5))
            alpha = max(45, round(160 * (1.0 - t)))
            pygame.draw.circle(self.screen, (255, 236, 190, alpha), (round(bubble_pos.x), round(bubble_pos.y)), bubble_radius)

        pygame.draw.circle(self.screen, (255, 210, 110, 210), (round(center.x), round(center.y)), max(2, round(4*self.zoom)))

    def draw_entry_exit(self) -> None:
        for label, x, y, colour, direction in (
            ("ENTRY", self.level.entry_x, self.level.entry_y, GREEN, self.level.entry_direction),
            ("EXIT", self.level.exit_x, self.level.exit_y, RED, self.level.exit_direction),
        ):
            p = self.world_to_screen(pygame.Vector2(x, y))
            pygame.draw.circle(self.screen, colour, (round(p.x), round(p.y)), 10)
            self.text(label, (p.x+14, p.y-9), self.small, colour)

    def draw_drawing(self) -> None:
        if not self.drawing:
            return
        pts = [self.world_to_screen(pygame.Vector2(x,y)) for x,y in self.drawing]
        if len(pts) > 1:
            pygame.draw.lines(self.screen, WHITE, False, [(p.x,p.y) for p in pts], 2)
        for p in pts:
            pygame.draw.circle(self.screen, WHITE, (round(p.x), round(p.y)), 4)

    def draw_cursor_hint(self) -> None:
        if self.tool in ("wall", "obstacle"):
            self.text("Left click: add point   Right click: finish polygon", (12, TOPBAR+10), self.small, MUTED)

    def draw_sidebar(self) -> None:
        r = self.sidebar_rect()
        pygame.draw.rect(self.screen, PANEL, r)
        pygame.draw.line(self.screen, BORDER, (r.left, r.top), (r.left, r.bottom), 2)

        self.text("TOOLS", (r.left+12, r.top+12), self.font, TEXT)
        y = r.top + 42
        for i, tool in enumerate(self.tool_order):
            if i == 10:
                break
            x = r.left + 12
            bw = 145
            button = pygame.Rect(x, y, bw, 30)
            active = self.tool == tool
            pygame.draw.rect(self.screen, PANEL_2 if active else BG, button)
            pygame.draw.rect(self.screen, ACCENT if active else BORDER, button, 1)
            label = "Select" if tool == "select" else ENTITY_DEFINITIONS.get(tool, {}).get("label", tool)
            self.text(f"{i+1 if tool != 'select' else ''} {label}".strip(), (x+8,y+7), self.small, TEXT)
            y += 34

        # File list
        self.text("LEVEL FILES", (r.left+170, r.top+12), self.font, TEXT)
        files = self.selector_level_files()
        for i, path in enumerate(files[:8]):
            by = r.top + 42 + i * 27
            button = pygame.Rect(r.left+160, by, 158, 24)
            pygame.draw.rect(self.screen, PANEL_2 if path == self.current_file else BG, button)
            self.text(path.stem[:22], (button.x+5, button.y+5), self.small, TEXT)

        # Inspector
        iy = r.top + 410
        pygame.draw.line(self.screen, BORDER, (r.left+10, iy), (r.right-10, iy))
        self.text("INSPECTOR", (r.left+12, iy+12), self.font, TEXT)

        if not self.selected:
            self.text("Select an entity to edit it.", (r.left+12, iy+42), self.small, MUTED)
            self.text("Entry: x=0, center     Exit: x=width, center", (r.left+12, iy+61), self.small, MUTED)
        else:
            self.text(self.selected.element_id, (r.left+12, iy+40), self.small, ACCENT)
            self.text(self.selected.element_type, (r.left+12, iy+58), self.small, MUTED)
            y = iy + 86
            fields = ENTITY_DEFINITIONS.get(self.selected.element_type, {}).get("fields", {})
            for name, (kind, default) in fields.items():
                if name in ("direction_x", "direction_y"):
                    continue
                value = self.selected.properties.get(name, default)
                box = pygame.Rect(r.left+12, y, 305, 25)
                pygame.draw.rect(self.screen, BG, box)
                pygame.draw.rect(self.screen, ACCENT if self.typing_field == name else BORDER, box, 1)
                suffix = " (click to cycle)" if kind == "item_id" else ""
                self.text(f"{name}: {value}{suffix}", (box.x+5, box.y+5), self.small, TEXT)
                y += 29

        # File actions
        bottom = r.bottom - 78
        self.text("FILE", (r.left+12, bottom), self.font, TEXT)
        self.text("Ctrl+S save   Ctrl+O open   Ctrl+N new", (r.left+12, bottom+24), self.small, MUTED)
        self.text("Delete selected   R rotate   F fit view", (r.left+12, bottom+44), self.small, MUTED)
        self.text("Build thermal vent structures with wall tool", (r.left+12, bottom+60), self.small, MUTED)

    def draw_statusbar(self) -> None:
        y = self.screen.get_height() - STATUSBAR
        pygame.draw.rect(self.screen, PANEL, (0, y, self.screen.get_width(), STATUSBAR))
        colour = RED if self.status_error else ACCENT
        self.text(self.status, (12, y+7), self.small, colour)
        if self.current_file:
            self.text(str(self.current_file), (400, y+7), self.small, MUTED)
        self.text(f"Zoom {self.zoom:.2f}   Elements {len(self.level.elements)}", (self.screen.get_width()-260, y+7), self.small, MUTED)

    def arrow_at(self, center: pygame.Vector2, direction: list[float], colour: tuple[int,int,int]) -> None:
        d = pygame.Vector2(direction)
        if d.length_squared() == 0:
            return
        d = d.normalize()
        end = center + d * 18
        pygame.draw.line(self.screen, WHITE, center, end, 2)
        self.arrowhead(center, end, WHITE)

    def arrowhead(self, start: pygame.Vector2, end: pygame.Vector2, colour: tuple[int,int,int]) -> None:
        d = end - start
        if d.length_squared() == 0:
            return
        d = d.normalize()
        side = pygame.Vector2(-d.y, d.x)
        pts = [end, end - d*8 + side*5, end - d*8 - side*5]
        pygame.draw.polygon(self.screen, colour, [(p.x,p.y) for p in pts])

    def text(self, value: str, pos: tuple[float,float], font: pygame.font.Font, colour: tuple[int,int,int]) -> None:
        self.screen.blit(font.render(str(value), True, colour), pos)
