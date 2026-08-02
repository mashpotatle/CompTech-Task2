"""
Main game controller for The Twilight Zone.

This module manages the main Pygame loop and coordinates the game's
initialisation, event handling, updating, rendering, and shutdown.

The Game class coordinates the major game systems but does not own
the level data itself. Level data is managed by LevelManager.
"""

from pathlib import Path

import pygame

from game.game_state import GameState
from entities.player import Player
from levels.level_manager import LevelManager
from levels.cave_section import LevelElement
from systems.collision import CollisionSystem
from systems.camera import Camera

from settings import (
    DEBUG_COLLISION,
    DEBUG_MODE,
    DEBUG_PLAYER_COLLISION,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TARGET_FPS,
    WINDOW_TITLE,
)


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

        # Gameplay is currently started directly.
        # The main menu system can be connected here later.
        self.game_state = GameState.PLAYING

        # Controls whether the main game loop continues running.
        self.running = True

        # ----------------------------------------------------------
        # Project paths
        # ----------------------------------------------------------

        # Determine the root directory of the game project.
        #
        # __file__ is:
        # TheTwilightZone/game/game.py
        #
        # parent        -> game/
        # parent.parent -> TheTwilightZone/
        project_root = (
            Path(__file__)
            .resolve()
            .parent
            .parent
        )

        level_data_directory = (
            project_root
            / "data"
            / "cave_sections"
            )

        # ----------------------------------------------------------
        # Level manager
        # ----------------------------------------------------------

        # LevelManager is responsible for loading and stitching
        # cave sections together.
        #
        # The available section pool is configured inside LevelManager.
        # New sections are selected randomly when the player reaches
        # the end of the currently generated world.

        self.level_manager = LevelManager(
            level_data_directory,
            available_sections=[
                "section_01.json",
                "section_02.json",
                "section_03.json",
                "section_04.json",
            ],
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

        # ----------------------------------------------------------
        # Collision system
        # ----------------------------------------------------------

        # Create the collision system.
        self.collision_system = CollisionSystem()

        # Give the collision system all currently loaded level
        # elements that contain solid geometry.
        self.update_collision_geometry()

        # ----------------------------------------------------------
        # Camera
        # ----------------------------------------------------------

        self.camera = Camera(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
        )

        # Update the camera once during initialisation so that the
        # player begins at the correct position.
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

        for event in pygame.event.get():

            # pygame.QUIT is generated when the player closes
            # the application window.
            if event.type == pygame.QUIT:
                self.running = False

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
        """
        Update logic for the main menu.

        Main menu functionality will be implemented later.
        """

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
        # Player movement
        # ----------------------------------------------------------

        self.player.update(
            delta_time,
            self.collision_system,
        )

        # ----------------------------------------------------------
        # Active section
        # ----------------------------------------------------------

        self.level_manager.update_active_section(
            self.player.position
        )

        # ----------------------------------------------------------
        # Generate more world
        # ----------------------------------------------------------

        self.check_section_exit()

        # ----------------------------------------------------------
        # Camera
        # ----------------------------------------------------------

        self.update_camera()

    def check_section_exit(self):
        exit_position = (
            self.level_manager.get_last_exit_position()
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
        Generate and stitch the next random cave section.
        """

        next_instance = (
            self.level_manager.generate_next_random_section()
        )

        if next_instance is None:
            print(
                "No more sections available for generation."
            )
            return

        self.current_section_instance = next_instance
        self.cave_section = next_instance.section

        self.update_collision_geometry()
        
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

        target_x = (
            self.player.position.x
            - SCREEN_WIDTH / 2
        )

        target_y = (
            self.player.position.y
            - SCREEN_HEIGHT / 2
        )

        self.camera.position.x = max(
            0,
            target_x,
        )

        self.camera.position.y = max(
            0,
            target_y,
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

        pass

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

        if self.game_state == GameState.PLAYING:

            # ------------------------------------------------------
            # Draw level geometry
            # ------------------------------------------------------

            self.draw_level()

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