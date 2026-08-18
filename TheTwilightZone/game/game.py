"""
Main game controller for The Twilight Zone.

This module manages the main Pygame loop and coordinates the game's
initialisation, event handling, updating, rendering, and shutdown.

The Game class coordinates the major game systems but does not own
the level data itself. Level data is managed by LevelManager.
"""

import pygame
import random

from assets.med_kit_model import create_med_kit_sprite
from assets.o2_tank_model import create_oxygen_tank_sprite
from game.game_state import GameState
from entities.player import Player
from levels.level_manager import LevelManager
from levels.cave_section import LevelElement
from systems.collision import CollisionSystem
from systems.camera import Camera
from systems.inventory import Inventory
from systems.oxygen import OxygenSystem
from ui.menus import EndlessRunConfirmation, MainMenu, PauseMenu
from ui.hud import HUD
from ui.hotbar import Hotbar
from ui.death_screen import DeathScreen
from entities.fish import Fish
from entities.silt_cloud import SiltCloud
from entities.spiky_plant import SpikyPlant
from entities.thermal_vent import ThermalVent
from entities.current import Current

from settings import (
    DEBUG_COLLISION,
    DEBUG_MODE,
    DEBUG_PLAYER_COLLISION,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SETTINGS,
    TARGET_FPS,
    WINDOW_TITLE,
)
from paths import CAVE_SECTIONS_DIR


class Game:
    """
    Controls the main game loop.

    The Game class coordinates:

    - Pygame initialisation
    - Player input and movement
    - Level loading and stitching
    - Collision detection
    - Camera movement
    - Rendering
    - Application shutdown

    The LevelManager is responsible for managing the currently loaded
    cave sections and converting their local coordinates into world
    coordinates.
    """

    def __init__(self):
        """
        Initialise Pygame and create the game window.
        """

        pygame.init()

        # ----------------------------------------------------------
        # Display
        # ----------------------------------------------------------

        self.screen = pygame.display.set_mode(
            (
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
            )
        )

        pygame.display.set_caption(
            WINDOW_TITLE
        )

        # ----------------------------------------------------------
        # Game clock
        # ----------------------------------------------------------

        # The clock controls the maximum frame rate and provides
        # delta time for frame-independent game logic.
        self.clock = pygame.time.Clock()

        # ----------------------------------------------------------
        # Game state
        # ----------------------------------------------------------

        # Start on the main menu so the new launch screen is visible.
        self.game_state = GameState.MAIN_MENU

        self.pause_menu = PauseMenu(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
        )
        self.main_menu = MainMenu(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
        )
        self.endless_run_confirmation = EndlessRunConfirmation(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
        )
        self.showing_endless_confirmation = False

        self.hud = HUD()
        self.hotbar = Hotbar()
        self.inventory = Inventory()
        self.death_screen = DeathScreen(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
        )

        # Set by damage handlers so the death screen can report why the
        # player died.
        self.cause_of_death = "Unknown"
        self.distance_travelled = 0.0
        self.oxygen_system = OxygenSystem(max_oxygen=100.0, drain_rate=6.0)
        self.oxygen_percent = self.oxygen_system.percent
        self.active_item_label = ""

        # Controls whether the main game loop continues running.
        self.running = True

        # ----------------------------------------------------------
        # Project paths
        # ----------------------------------------------------------

        self.level_data_directory = CAVE_SECTIONS_DIR

        # ----------------------------------------------------------
        # Camera
        # ----------------------------------------------------------

        self.camera = Camera(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
        )

        self._start_new_run()

    def _start_new_run(self):
        """
        (Re)create the level, player, and entities for a fresh run.

        Used both by __init__ and by the death screen's restart action.
        """

        # ----------------------------------------------------------
        # Level manager
        # ----------------------------------------------------------

        # LevelManager is responsible for loading and stitching
        # cave sections together.
        #
        # The available section pool is configured inside LevelManager.
        # New sections are selected randomly when the player reaches
        # the end of the currently generated world.

        available_sections = [
            path.name
            for path in sorted(
                self.level_data_directory.glob("*.json")
            )
            if path.is_file()
        ]

        self.level_manager = LevelManager(
            self.level_data_directory,
            available_sections=available_sections,
        )

        # Load the first section into the world.

        self.current_section_instance = (
            self.level_manager.load_initial_section(
                "section_01.json"
            )
        )

        self.cave_section = (
            self.current_section_instance.section
        )

        # ----------------------------------------------------------
        # Player
        # ----------------------------------------------------------

        # Start the player at the entry position of the first section.
        #
        # The entry position is stored in world coordinates relative
        # to the first section. Since the first section has an offset
        # of (0, 0), this is also the initial world position.
        self.player = Player(
            self.cave_section.entry_position.copy()
        )
        self._run_start_x = self.player.position.x
        self.distance_travelled = 0.0
        self.cause_of_death = "Unknown"

        # ----------------------------------------------------------
        # Fish
        # ----------------------------------------------------------

        self.fish = pygame.sprite.Group()

        self.spawn_fish_from_level()

        # ----------------------------------------------------------
        # Spiky Plants
        # ----------------------------------------------------------

        self.spiky_plants = pygame.sprite.Group()

        self.spawn_spiky_plants_from_level()

        # ----------------------------------------------------------
        # Currents
        # ----------------------------------------------------------

        self.currents = pygame.sprite.Group()

        self.spawn_currents_from_level()

        # ----------------------------------------------------------
        # Environmental hazards
        # ----------------------------------------------------------

        self.silt_clouds = pygame.sprite.Group()
        self.thermal_vents = pygame.sprite.Group()

        self.spawn_silt_clouds_from_level()
        self.spawn_thermal_vents_from_level()

        # ----------------------------------------------------------
        # Collision system
        # ----------------------------------------------------------

        # Create the collision system.
        self.collision_system = CollisionSystem()

        # Give the collision system all currently loaded level
        # elements that contain solid geometry.
        self.update_collision_geometry()

        # Update the camera once so the player begins at the correct
        # position.
        self.update_camera()

    # ==================================================================
    # EVENT HANDLING
    # ==================================================================

    def handle_events(self):
        """
        Process events received from Pygame.

        This currently handles application shutdown.
        Additional keyboard and menu events can be added later.
        """

        mouse_pos = pygame.mouse.get_pos()

        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():

            # pygame.QUIT is generated when the player closes
            # the application window.
            if event.type == pygame.QUIT:
                self.running = False

            if self.game_state == GameState.MAIN_MENU and not self.showing_endless_confirmation:
                action = self.main_menu.handle_events(event, mouse_pos)
                if action == "PLAY":
                    self.showing_endless_confirmation = True
                elif action == "EXIT":
                    self.running = False

            if self.showing_endless_confirmation:
                action = self.endless_run_confirmation.handle_events(event, mouse_pos)
                if action == "START_ENDLESS":
                    self.showing_endless_confirmation = False
                    self.game_state = GameState.PLAYING
                elif action == "CANCEL":
                    self.showing_endless_confirmation = False

            if self.game_state == GameState.PLAYING and event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.game_state = GameState.PAUSED
                self.pause_menu.confirming_quit = False

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.game_state == GameState.PLAYING:
                    self.game_state = GameState.PAUSED
                elif self.game_state == GameState.PAUSED:
                    self.game_state = GameState.PLAYING
                    self.pause_menu.confirming_quit = False

            if self.game_state == GameState.PLAYING:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_q, pygame.K_z):
                        self.use_active_item()
                    elif event.key == pygame.K_x:
                        self.drop_active_item()
                    elif pygame.K_1 <= event.key <= pygame.K_5:
                        self.inventory.active_index = event.key - pygame.K_1
                elif event.type == pygame.MOUSEWHEEL:
                    self.inventory.cycle(event.y)

            if self.game_state == GameState.PAUSED:
                action = self.pause_menu.handle_events(event, mouse_pos, self.inventory.slots)
                if action == "RESUME":
                    self.game_state = GameState.PLAYING
                    self.pause_menu.confirming_quit = False
                elif action == "QUIT_TO_MENU":
                    self.game_state = GameState.MAIN_MENU
                    self.pause_menu.confirming_quit = False
                elif isinstance(action, tuple) and action[0] == "SWAP_SLOTS":
                    first, second = action[1]
                    self.inventory.swap_slots(first, second)
                    self.pause_menu.pending_slot_selection = None
                elif isinstance(action, tuple) and action[0] == "SELECT_SLOT":
                    self.inventory.active_index = action[1]

            if self.game_state == GameState.DEAD:
                action = self.death_screen.handle_events(event, mouse_pos)
                if action == "RESTART":
                    self._start_new_run()
                    self.game_state = GameState.PLAYING
                elif action == "MAIN_MENU":
                    self.game_state = GameState.MAIN_MENU

    # ==================================================================
    # GAME UPDATE
    # ==================================================================

    def update(
        self,
        delta_time: float,
    ):
        """
        Update game logic.

        Args:
            delta_time:
                Time in seconds since the previous frame.
        """

        if self.game_state == GameState.MAIN_MENU:

            self.update_main_menu(
                delta_time
            )

        elif self.game_state == GameState.PLAYING:

            self.update_gameplay(
                delta_time
            )

        elif self.game_state == GameState.PAUSED:

            self.update_pause_menu(
                delta_time
            )

        elif self.game_state == GameState.DEAD:

            self.update_death_screen(
                delta_time
            )

    # ==================================================================
    # MAIN MENU
    # ==================================================================

    def update_main_menu(
        self,
        delta_time: float,
    ):
        """Handle main-menu state transitions."""

        pass

    # ==================================================================
    # GAMEPLAY
    # ==================================================================

    def update_gameplay(
        self,
        delta_time: float,
    ):
        """
        Update all active gameplay systems.

        The update order is:

        1. Read player input.
        2. Move the player.
        3. Update the active section.
        4. Generate the next random section when the player
        reaches the end of the generated world.
        5. Update collision geometry.
        6. Update the camera.
        """

        # ----------------------------------------------------------
        # Player input
        # ----------------------------------------------------------

        self.player.handle_input()

        # ----------------------------------------------------------
        # Oxygen / survival
        # ----------------------------------------------------------

        self.oxygen_system.update(delta_time, in_water=True)
        self.oxygen_percent = self.oxygen_system.percent

        if self.oxygen_system.is_empty:
            self.cause_of_death = "Drowning"
            self.game_state = GameState.DEAD
            return

        # ----------------------------------------------------------
        # Player movement
        # ----------------------------------------------------------

        self.player.update(
            delta_time,
            self.collision_system,
        )

        self.check_item_pickups()

        # ----------------------------------------------------------
        # Fish
        # ----------------------------------------------------------

        for fish in self.fish:

            fish.update(
                delta_time,
                self.player.position,
            )

            if fish.check_player_collision(
                self.player.rect
            ):
                self.handle_fish_damage(fish)

        # ----------------------------------------------------------
        # Spiky plants
        # ----------------------------------------------------------

        for plant in self.spiky_plants:

            plant.update(delta_time)

            if plant.check_player_collision(self.player.rect):
                self.handle_spiky_plant_damage(plant)

        # ----------------------------------------------------------
        # Currents
        # ----------------------------------------------------------

        for current in self.currents:

            current.update(delta_time)

            # Apply any movement the current imposes on the player, with collision checks.
            movement = current.apply_to_player(self.player, delta_time, self.collision_system)

            # If movement occurred, trigger a visual wobble effect on the player
            # proportional to the force magnitude.
            if movement.length_squared() > 0:
                # Approximate force magnitude (pixels / s) from movement and dt
                force_mag = movement.length() / max(delta_time, 1e-6)
                wobble_strength = min(2.0, force_mag / 100.0)
                self.player.add_wobble(wobble_strength, 0.5)

        # ----------------------------------------------------------
        # Silt clouds
        # ----------------------------------------------------------

        for cloud in self.silt_clouds:
            cloud.update(delta_time)
            offset = cloud.position - self.player.position
            if offset.length() <= cloud.effect_radius:
                self.player.velocity *= 1.0 - min(0.75, cloud.speed_reduction * 0.75)

        # ----------------------------------------------------------
        # Thermal vents
        # ----------------------------------------------------------

        for vent in self.thermal_vents:
            vent.update(delta_time)
            distance = self.player.position.distance_to(vent.position)
            if distance <= vent.damage_radius:
                damage = vent.get_damage_at_distance(distance) * delta_time
                if damage > 0:
                    self.player.apply_damage(int(damage))
                    if self.player.health <= 0:
                        self.cause_of_death = "Thermal vent"
                        self.game_state = GameState.DEAD
                        return

        # ----------------------------------------------------------
        # Active section
        # ----------------------------------------------------------

        self.level_manager.update_active_section(
            self.player.position
        )
        self.current_section_instance = (
            self.level_manager.get_current_section()
        )

        if self.current_section_instance is not None:
            self.cave_section = (
                self.current_section_instance.section
            )

        self.active_item_label = self.inventory.active_item or ""

        # ----------------------------------------------------------
        # Generate more world
        # ----------------------------------------------------------

        self.check_section_exit()

        # ----------------------------------------------------------
        # Distance travelled
        # ----------------------------------------------------------

        # Placeholder "metres" until a real distance/unit system exists;
        # tracks horizontal displacement from the run's starting point.
        self.distance_travelled = max(
            self.distance_travelled,
            abs(self.player.position.x - self._run_start_x),
        )

        # ----------------------------------------------------------
        # Camera
        # ----------------------------------------------------------

        self.update_camera()

    def check_section_exit(self):
        current_instance = (
            self.level_manager.get_current_section()
        )

        if current_instance is None:
            return

        exit_position = (
            self.level_manager.get_last_exit_position(
            )
        )

        if exit_position is None:
            return

        distance_to_exit = (
            self.player.position.distance_to(
                exit_position
            )
        )

        if distance_to_exit <= 100:
            self.load_next_section()

    def load_next_section(self):
        """
        Move into the next generated section instance if one exists,
        or generate a new random section when the player reaches the
        current section's exit.
        """

        next_instance = (
            self.level_manager.transition_to_next_section(
                self.player.position,
                self.player.velocity,
            )
        )

        if next_instance is None:
            print(
                "No more sections available for generation."
            )
            return

        self.current_section_instance = next_instance
        self.cave_section = next_instance.section

        self.update_collision_geometry()

        self.spawn_fish_from_level()
        self.spawn_spiky_plants_from_level()
        self.spawn_currents_from_level()
        self.spawn_silt_clouds_from_level()
        self.spawn_thermal_vents_from_level()

        self.update_camera()
        
    # ==================================================================
    # COLLISION
    # ==================================================================

    def update_collision_geometry(self):
        """
        Update the collision system using all currently loaded
        cave geometry.

        LevelManager returns elements in world coordinates.
        """

        world_elements = (
            self.level_manager.get_all_elements()
        )

        geometry_elements = [
            element
            for element in world_elements
            if element.element_type
            in (
                "wall",
                "obstacle",
            )
        ]

        self.collision_system.set_level_elements(
            geometry_elements
        )

    # ==================================================================
    # CAMERA
    # ==================================================================

    def update_camera(self):
        """
        Update the camera to follow the player.

        Horizontal camera movement is not restricted by the currently
        loaded section window. This prevents camera snapping when
        sections are loaded or unloaded.
        """

        self.camera.update(
            self.player.position,
            self.level_manager.get_world_bounds(),
        )

    # ==================================================================
    # PAUSE MENU
    # ==================================================================

    def update_pause_menu(
        self,
        delta_time: float,
    ):
        """
        Update the pause and inventory manager.

        Gameplay systems should not be updated while this state
        is active.
        """

        pass

    # ==================================================================
    # DEATH SCREEN
    # ==================================================================

    def update_death_screen(
        self,
        delta_time: float,
    ):
        """
        Update the death screen.
        """

        is_new_high_score = self.distance_travelled > SETTINGS.max_distance_travelled
        if is_new_high_score:
            SETTINGS.max_distance_travelled = int(self.distance_travelled)

        self.death_screen.set_result(
            self.distance_travelled,
            self.cause_of_death,
            is_new_high_score,
        )

    # ==================================================================
    # RENDERING
    # ==================================================================

    def render(self):
        """
        Render the current game state to the display.
        """

        # Clear the screen before drawing the current frame.
        self.screen.fill(
            (
                10,
                25,
                30,
            )
        )

        if self.game_state in (GameState.PLAYING, GameState.PAUSED):

            # ------------------------------------------------------
            # Draw level geometry
            # ------------------------------------------------------

            self.draw_level()

            # ------------------------------------------------------
            # Draw currents
            # ------------------------------------------------------

            for current in self.currents:
                current.draw(
                    self.screen,
                    self.camera,
                )

            # ------------------------------------------------------
            # Draw silt clouds
            # ------------------------------------------------------

            for cloud in self.silt_clouds:
                cloud.draw(
                    self.screen,
                    self.camera,
                )

            # ------------------------------------------------------
            # Draw thermal vents
            # ------------------------------------------------------

            for vent in self.thermal_vents:
                vent.draw(
                    self.screen,
                    self.camera,
                )

            # ------------------------------------------------------
            # Draw fish
            # ------------------------------------------------------

            for fish in self.fish:
                fish.draw(
                    self.screen,
                    self.camera,
                )

            # ------------------------------------------------------
            # Draw spiky plants
            # ------------------------------------------------------

            for plant in self.spiky_plants:
                plant.draw(
                    self.screen,
                    self.camera,
                )

            # ------------------------------------------------------
            # Draw player
            # ------------------------------------------------------

            self.player.draw(
                self.screen,
                self.camera,
            )

            # ------------------------------------------------------
            # Draw player
            # ------------------------------------------------------

            self.player.draw(
                self.screen,
                self.camera,
            )

            # ------------------------------------------------------
            # Debug player collision rectangle
            # ------------------------------------------------------

            if DEBUG_PLAYER_COLLISION:

                screen_position = (
                    self.camera.world_to_screen(
                        pygame.Vector2(
                            self.player.rect.topleft
                        )
                    )
                )

                debug_rect = pygame.Rect(
                    round(
                        screen_position.x
                    ),
                    round(
                        screen_position.y
                    ),
                    self.player.rect.width,
                    self.player.rect.height,
                )

                pygame.draw.rect(
                    self.screen,
                    (
                        255,
                        0,
                        0,
                    ),
                    debug_rect,
                    1,
                )

            # ------------------------------------------------------
            # Draw HUD and hotbar
            # ------------------------------------------------------

            self.hud.draw(self.screen, self.player.health, self.oxygen_percent)
            self.hotbar.draw(
                self.screen,
                self.inventory.slots,
                active_index=self.inventory.active_index,
            )

        if self.game_state == GameState.PAUSED:
            self.pause_menu.draw(self.screen, self.inventory.slots)
        elif self.game_state == GameState.MAIN_MENU:
            self.main_menu.draw(self.screen)
        elif self.game_state == GameState.DEAD:
            self.death_screen.draw(self.screen)

        if self.showing_endless_confirmation:
            self.endless_run_confirmation.draw(self.screen)

        # ----------------------------------------------------------
        # Debug information
        # ----------------------------------------------------------

        if DEBUG_MODE:

            self.render_debug_information()

        pygame.display.flip()

    # ==================================================================
    # LEVEL RENDERING
    # ==================================================================

    def draw_level(self):
        """
        Draw all currently loaded level elements.

        LevelManager provides elements in world coordinates.
        The camera converts those coordinates into screen coordinates.
        """

        elements = (
            self.level_manager.get_all_elements()
        )

        for element in elements:

            if element.element_type == "wall":

                self.draw_wall(
                    element
                )

            elif element.element_type == "obstacle":

                self.draw_obstacle(
                    element
                )

            elif element.element_type == "item":

                self.draw_item(
                    element
                )

    def draw_wall(
        self,
        element: LevelElement,
    ):
        """
        Draw a cave wall.

        Wall polygon points are stored in local element coordinates.
        LevelManager has already moved the element position into
        world coordinates.

        The camera then converts each point into screen coordinates.
        """

        screen_points = [
            self.camera.world_to_screen(
                point
            )
            for point in element.get_world_points()
        ]

        if len(screen_points) < 3:
            return

        # ----------------------------------------------------------
        # Temporary wall rendering
        # ----------------------------------------------------------

        # This will eventually be replaced by textured polygon
        # rendering using the wall's material settings.
        pygame.draw.polygon(
            self.screen,
            (
                70,
                80,
                85,
            ),
            screen_points,
        )

        # ----------------------------------------------------------
        # Debug wall outline
        # ----------------------------------------------------------

        if DEBUG_COLLISION:

            pygame.draw.lines(
                self.screen,
                (
                    120,
                    130,
                    135,
                ),
                True,
                screen_points,
                2,
            )

    def draw_obstacle(
        self,
        element: LevelElement,
    ):
        """
        Draw a solid cave obstacle.

        Obstacles use the same polygon geometry system as cave walls.
        """

        screen_points = [
            self.camera.world_to_screen(
                point
            )
            for point in element.get_world_points()
        ]

        if len(screen_points) < 3:
            return

        pygame.draw.polygon(
            self.screen,
            (
                80,
                90,
                95,
            ),
            screen_points,
        )

        if DEBUG_COLLISION:

            pygame.draw.lines(
                self.screen,
                (
                    130,
                    140,
                    145,
                ),
                True,
                screen_points,
                2,
            )

    def draw_item(
        self,
        element: LevelElement,
    ):
        """Draw a temporary collectible marker with debug metadata."""
        if element.properties.get("collected"):
            return

        screen_position = self.camera.world_to_screen(
            element.position
        )
        radius = max(10, int(float(element.properties.get("pickup_radius", 18.0)) * 0.25))

        item_type = str(element.properties.get("item_type", "oxygen_tank"))
        if item_type == "oxygen_tank":
            sprite = create_oxygen_tank_sprite(28, 28)
            sprite_rect = sprite.get_rect(center=(int(screen_position.x), int(screen_position.y)))
            self.screen.blit(sprite, sprite_rect)
        elif item_type == "med_kit":
            sprite = create_med_kit_sprite(28, 28)
            sprite_rect = sprite.get_rect(center=(int(screen_position.x), int(screen_position.y)))
            self.screen.blit(sprite, sprite_rect)
        else:
            pygame.draw.circle(
                self.screen,
                (210, 200, 80),
                (int(screen_position.x), int(screen_position.y)),
                radius,
            )
            pygame.draw.circle(
                self.screen,
                (50, 50, 50),
                (int(screen_position.x), int(screen_position.y)),
                max(2, radius - 4),
                2,
            )

        if DEBUG_MODE:
            label = pygame.font.Font(None, 20).render(
                element.element_id,
                True,
                (255, 255, 255),
            )
            self.screen.blit(
                label,
                (
                    int(screen_position.x + radius + 8),
                    int(screen_position.y - radius - 8),
                ),
            )

    # ==================================================================
    # DEBUG INFORMATION
    # ==================================================================

    def render_debug_information(self):
        """
        Display temporary information useful during development.
        """

        font = pygame.font.Font(
            None,
            36,
        )

        debug_text = (
            f"State: {self.game_state.name} | "
            f"FPS: {self.clock.get_fps():.1f} | "
            f"Sections: "
            f"{len(self.level_manager.sections)}"
        )

        text_surface = font.render(
            debug_text,
            True,
            (
                255,
                255,
                255,
            ),
        )

        self.screen.blit(
            text_surface,
            (
                20,
                20,
            ),
        )

    def spawn_fish_from_level(self):
        """
        Create fish from all fish_spawn elements in the
        currently loaded world.

        Fish spawn positions are already converted into world
        coordinates by LevelManager.
        """

        self.fish.empty()

        elements = (
            self.level_manager.get_all_elements()
        )

        for element in elements:

            if element.element_type != "fish_spawn":
                continue

            properties = element.properties

            count = int(
                properties.get(
                    "count",
                    1,
                )
            )

            speed = float(
                properties.get(
                    "speed",
                    70,
                )
            )

            detection_range = float(
                properties.get(
                    "detection_range",
                    180,
                )
            )

            damage = int(
                properties.get(
                    "damage",
                    10,
                )
            )

            patrol_distance = float(
                properties.get(
                    "patrol_distance",
                    150,
                )
            )

            direction = properties.get(
                "direction",
                [1, 0],
            )

            for index in range(count):

                # Spread members of a fish group around
                # the spawn point rather than stacking them.
                spawn_position = (
                    element.position
                    + pygame.Vector2(
                        random.uniform(-30, 30),
                        random.uniform(-30, 30),
                    )
                )

                fish = Fish(
                    position=spawn_position,
                    spawn_id=element.element_id,
                    patrol_direction=direction,
                    patrol_distance=patrol_distance,
                    speed=speed,
                    detection_range=detection_range,
                    damage=damage,
                )

                self.fish.add(fish)

    def spawn_spiky_plants_from_level(self):
        """
        Create all spiky plants from the loaded level.
        """

        self.spiky_plants.empty()

        elements = self.level_manager.get_all_elements()

        for element in elements:

            if element.element_type != "spiky_plant":
                continue

            properties = element.properties

            plant = SpikyPlant(
                position=element.position,
                plant_id=element.element_id,
                damage=properties.get("damage", 15),
                radius=properties.get("radius", 24),
            )

            self.spiky_plants.add(plant)


    def spawn_currents_from_level(self):
        """
        Create current entities from the loaded level.
        """

        self.currents.empty()

        elements = self.level_manager.get_all_elements()

        for element in elements:

            if element.element_type != "current":
                continue

            properties = element.properties

            # Map level JSON "width"/"height" into an effect radius.
            width = float(properties.get("width", 0.0))
            height = float(properties.get("height", 0.0))
            radius = max(width, height) / 2.0 if (width or height) else properties.get("effect_radius", 60.0)

            strength = float(properties.get("strength", 100.0))

            direction = properties.get("direction", [1.0, 0.0])

            current = Current(
                position=element.position,
                direction=direction,
                current_id=element.element_id,
                strength=strength,
                effect_radius=radius,
            )

            self.currents.add(current)

    def spawn_silt_clouds_from_level(self):
        """Create floating silt cloud hazards from level data."""

        self.silt_clouds.empty()

        for element in self.level_manager.get_all_elements():
            if element.element_type != "silt_cloud":
                continue

            properties = element.properties
            radius = float(properties.get("radius", 120.0))
            visibility = float(properties.get("visibility", 0.15))
            cloud = SiltCloud(
                position=element.position,
                cloud_id=element.element_id,
                radius=radius,
                visibility=visibility,
                speed_reduction=0.5,
            )
            self.silt_clouds.add(cloud)

    def spawn_thermal_vents_from_level(self):
        """Create thermal vent hazards from level data."""

        self.thermal_vents.empty()

        for element in self.level_manager.get_all_elements():
            if element.element_type != "thermal_vent":
                continue

            properties = element.properties
            vent = ThermalVent(
                position=element.position,
                vent_id=element.element_id,
                direction=tuple(properties.get("direction", [1.0, 0.0])),
                radius=float(properties.get("radius", 26.0)),
                heat_radius=float(properties.get("heat_radius", 100.0)),
                heat_damage=float(properties.get("heat_damage", 5.0)),
                eruption_damage=float(properties.get("eruption_damage", 20.0)),
                eruption_duration=float(properties.get("eruption_duration", 1.0)),
                eruption_interval=float(properties.get("eruption_interval", 5.0)),
                haze_length=float(properties.get("haze_length", 95.0)),
                haze_width=float(properties.get("haze_width", 30.0)),
                haze_alpha=int(properties.get("haze_alpha", 65)),
                bubble_count=int(properties.get("bubble_count", 14)),
                bubble_spread=float(properties.get("bubble_spread", 15.0)),
                bubble_speed=float(properties.get("bubble_speed", 1.0)),
            )
            self.thermal_vents.add(vent)


    def check_item_pickups(self):
        """Collect nearby world items into the hotbar when a slot is free."""
        for section_instance in self.level_manager.sections:
            for element in section_instance.section.elements:
                if element.element_type != "item":
                    continue

                if element.properties.get("collected"):
                    continue

                radius = float(element.properties.get("pickup_radius", 48.0))
                if self.player.position.distance_to(element.position) <= radius:
                    item_type = str(element.properties.get("item_type", "oxygen_tank"))
                    if self.inventory.add_item(item_type):
                        element.properties["collected"] = True
                        element.properties["in_inventory"] = True

                        # Also hide dropped runtime items if they are represented in the section runtime state.
                        runtime_state = section_instance.runtime_state.get("dropped_items", [])
                        for dropped_item in runtime_state:
                            if dropped_item.element_id == element.element_id:
                                dropped_item.properties["collected"] = True
                                dropped_item.properties["in_inventory"] = True

    def use_active_item(self):
        """Apply the active item effect to the player and remove it.

        Supported consumables:
        - oxygen_tank: refill oxygen
        - med_kit: restore health
        """
        item_name = self.inventory.use_active()
        if item_name is None:
            return

        if item_name == "oxygen_tank":
            self.oxygen_system.restore(35.0)
            self.oxygen_percent = self.oxygen_system.percent
        elif item_name == "med_kit":
            self.player.health = min(100, self.player.health + 25)

    def drop_active_item(self):
        """Drop the currently selected hotbar item into the world."""
        item_name = self.inventory.drop_active()
        if item_name is None:
            return

        current_section = self.level_manager.get_current_section()
        if current_section is None:
            return

        dropped = LevelElement(
            element_id=f"dropped_{item_name}_{abs(hash((self.player.position.x, self.player.position.y, item_name)))}",
            element_type="item",
            position=self.player.position.copy(),
            properties={
                "item_type": item_name,
                "pickup_radius": 48.0,
                "collected": False,
                "in_inventory": False,
            },
        )

        self.level_manager.add_dropped_item(current_section, dropped)

    def handle_fish_damage(
        self,
        fish: Fish,
    ) -> None:
        """
        Handle damage caused by a fish.

        This is intentionally kept separate from Fish so the entity
        does not need to know about the game's health/death system.
        """

        print(
            f"Fish {fish.spawn_id} hit the player "
            f"for {fish.damage} damage."
        )

        # Apply damage to player health
        if hasattr(self.player, "apply_damage"):
            self.player.apply_damage(fish.damage)

        if getattr(self.player, "health", 1) <= 0:
            print("Player died from fish damage.")
            self.cause_of_death = "Eaten by a fish"
            self.game_state = GameState.DEAD

    def handle_spiky_plant_damage(
        self,
        plant: SpikyPlant,
    ) -> None:
        """
        Temporary damage handler.
        """

        print(
            f"Plant {plant.plant_id} hit player "
            f"for {plant.damage} damage."
        )

        # Apply damage to player health
        if hasattr(self.player, "apply_damage"):
            self.player.apply_damage(plant.damage)

        if getattr(self.player, "health", 1) <= 0:
            print("Player died from plant damage.")
            self.cause_of_death = "Spiky plant"
            self.game_state = GameState.DEAD

    # ==================================================================
    # MAIN LOOP
    # ==================================================================

    def run(self):
        """
        Start and maintain the main game loop.

        The loop follows the standard Pygame structure:

        1. Process events.
        2. Calculate delta time.
        3. Update game logic.
        4. Render the current frame.
        5. Limit the frame rate.
        """

        while self.running:

            # ------------------------------------------------------
            # Process events
            # ------------------------------------------------------

            self.handle_events()

            # ------------------------------------------------------
            # Calculate delta time
            # ------------------------------------------------------

            delta_time = (
                self.clock.tick(
                    TARGET_FPS
                )
                / 1000.0
            )

            # ------------------------------------------------------
            # Update game systems
            # ------------------------------------------------------

            self.update(
                delta_time
            )

            # ------------------------------------------------------
            # Render current frame
            # ------------------------------------------------------

            self.render()

        # Always shut down Pygame cleanly when the game loop ends.
        pygame.quit()