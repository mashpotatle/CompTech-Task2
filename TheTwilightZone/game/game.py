"""
Main game controller for The Twilight Zone.

This module manages the main Pygame loop and coordinates the game's
initialisation, event handling, updating, rendering, and shutdown.

The Game class coordinates the major game systems but does not own
the level data itself. Level data is managed by LevelManager.
"""

import json
import math
import random
from pathlib import Path

import pygame
from pygame import mixer

from data.assets.lore_model import create_lore_sprite
from data.assets.med_kit_model import create_med_kit_sprite
from data.assets.o2_tank_model import create_oxygen_tank_sprite
from game.game_state import GameState
from entities.player import Player
from levels.level_manager import LevelManager
from levels.cave_section import LevelElement
from systems.collision import CollisionSystem
from systems.camera import Camera
from systems.inventory import Inventory
from systems.oxygen import OxygenSystem
from ui.menus import EndlessRunConfirmation, LoreCollectionScreen, MainMenu, PauseMenu
from ui.hud import HUD
from ui.hotbar import Hotbar
from ui.death_screen import DeathScreen
from entities.fish import Fish
from entities.silt_cloud import SiltCloud
from entities.spiky_plant import SpikyPlant
from entities.thermal_vent import ThermalVent
from entities.current import Current

from settings import (
    DEBUG_MODE,
    DEBUG_PLAYER_COLLISION,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SETTINGS,
    TARGET_FPS,
    WINDOW_TITLE,
    save_settings,
)
from paths import ASSETS_DIR, CAVE_SECTIONS_DIR, DATA_DIR


WALL_TEXTURE_PATH = ASSETS_DIR / "cave_wall.png"


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

        try:
            pygame.mixer.init()
            self.audio_enabled = True
        except pygame.error:
            self.audio_enabled = False

        self._sound_cache = {}
        self._sound_categories = {}
        self._init_audio()

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

        self.wall_texture = self._load_wall_texture()
        self.wall_polygon_cache: dict[str, tuple[pygame.Surface, int, int]] = {}
        self.item_sprites = {
            "oxygen_tank": create_oxygen_tank_sprite(70, 70),
            "med_kit": create_med_kit_sprite(70, 70),
            "lore_fragment": create_lore_sprite(70, 70),
        }
        self.overlay_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.debug_font_small = pygame.font.Font(None, 20)
        self.debug_font_large = pygame.font.Font(None, 36)

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
        self.hotbar.set_item_icons(self.item_sprites)
        self.death_screen = DeathScreen(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
        )
        self.lore_collection = LoreCollectionScreen(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
        )

        # Set by damage handlers so the death screen can report why the
        # player died.
        self.cause_of_death = "Unknown"
        self.distance_travelled = 0.0
        self.oxygen_system = OxygenSystem(max_oxygen=100.0, drain_rate=2.0)
        self.oxygen_percent = self.oxygen_system.percent
        self.oxygen_fade_timer = 0.0
        self.oxygen_fade_duration = 3.0
        self.damage_flash_timer = 0.0
        self.damage_flash_duration = 0.35
        self.damage_flash_color = (255, 60, 60)
        self.damage_flash_elapsed = 0.0
        self.silt_intensity = 0.0
        self.low_oxygen_intensity = 0.0
        self.low_oxygen_audio_active = False
        self.current_audio_active = False
        self.silt_audio_active = False
        self.thermal_audio_active = False
        self.heartbeat_audio_active = False
        self.death_audio_played = False
        self.active_item_label = ""
        self.showing_endless_confirmation = False

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

    def _init_audio(self):
        """Load supplied audio and create generated feedback sounds."""
        if not self.audio_enabled:
            return

        ambience_path = ASSETS_DIR / "Thalassophobia.mp3"
        scrape_path = ASSETS_DIR / "scrape.mp3"
        self._sound_cache = {
            "menu": self._make_sound_tone(880.0, 0.08, 0.12),
            "pickup": self._make_sound_tone(660.0, 0.12, 0.18),
            "damage": self._make_sound_tone(200.0, 0.20, 0.25),
            "confirm": self._make_sound_tone(1040.0, 0.10, 0.18),
            "oxygen_warning": self._make_sound_tone(520.0, 0.16, 0.20),
            "drowning": self._make_sound_tone(110.0, 0.45, 0.24),
            "current": self._make_sound_tone(150.0, 0.30, 0.12),
            "silt": self._make_sound_tone(75.0, 0.35, 0.10),
            "thermal": self._make_sound_tone(95.0, 0.40, 0.14),
            "heartbeat": self._make_sound_tone(62.0, 0.18, 0.26),
            "death": self._make_sound_tone(55.0, 0.75, 0.30),
            "scrape": pygame.mixer.Sound(str(scrape_path)) if scrape_path.exists() else None,
        }
        self._sound_categories = {
            "menu": "menu",
            "confirm": "menu",
            "oxygen_warning": "game",
            "drowning": "game",
            "current": "game",
            "silt": "game",
            "thermal": "game",
            "heartbeat": "game",
            "death": "game",
            "damage": "game",
            "scrape": "game",
            "pickup": "game",
        }

        if ambience_path.exists():
            pygame.mixer.music.load(str(ambience_path))
            pygame.mixer.music.play(loops=-1)

        self.update_audio_volumes()

    def _make_sound_tone(self, frequency: float, duration: float = 0.08, volume: float = 0.18):
        """Generate a simple sine-wave sound effect without external assets."""
        if not self.audio_enabled:
            return None

        sample_rate = 22050
        frame_count = max(1, int(sample_rate * duration))
        raw = bytearray()
        for index in range(frame_count):
            t = index / sample_rate
            value = math.sin(2 * math.pi * frequency * t)
            amplitude = int(max(-1.0, min(1.0, value)) * 32767 * volume)
            raw.extend((amplitude & 0xFF, (amplitude >> 8) & 0xFF))
        sound = pygame.mixer.Sound(buffer=bytes(raw))
        sound.set_volume(1.0)
        return sound

    def update_audio_volumes(self) -> None:
        """Apply persisted master and per-channel volumes immediately."""
        if not self.audio_enabled:
            return

        master = max(0.0, min(1.0, SETTINGS.master_volume / 100.0))
        ambience = max(0.0, min(1.0, SETTINGS.ambience_volume / 100.0))
        menu = max(0.0, min(1.0, SETTINGS.menus_volume / 100.0))
        game = max(0.0, min(1.0, SETTINGS.game_volume / 100.0))
        pygame.mixer.music.set_volume(master * ambience)

        for name, sound in self._sound_cache.items():
            if sound is None:
                continue
            category = self._sound_categories.get(name, "game")
            category_volume = menu if category == "menu" else game
            sound.set_volume(master * category_volume)

    def play_sound(self, name: str):
        """Play a cached generated sound if audio is enabled."""
        if not self.audio_enabled:
            return
        self.update_audio_volumes()
        sound = self._sound_cache.get(name)
        if sound is not None:
            if sound.get_num_channels() > 0:
                sound.stop()
            sound.play()

    def start_looping_sound(self, name: str) -> None:
        """Start a cached sound loop without restarting an active loop."""
        if not self.audio_enabled:
            return
        sound = self._sound_cache.get(name)
        if sound is not None and sound.get_num_channels() == 0:
            sound.play(loops=-1)

    def stop_sound(self, name: str) -> None:
        """Stop a cached sound if it is currently playing."""
        if not self.audio_enabled:
            return
        sound = self._sound_cache.get(name)
        if sound is not None:
            sound.stop()

    def trigger_death_audio(self) -> None:
        """Stop hazard loops and play the death cue once per run."""
        if self.death_audio_played:
            return
        for sound_name in ("heartbeat", "thermal"):
            self.stop_sound(sound_name)
        self.play_sound("death")
        self.death_audio_played = True

    def trigger_damage_feedback(self, color: tuple[int, int, int] | None = None, duration: float | None = None) -> None:
        """Trigger a brief screen flash to communicate damage or hazard contact."""
        if self.damage_flash_timer <= 0:
            self.damage_flash_elapsed = 0.0
        self.damage_flash_color = color or (255, 60, 60)
        self.damage_flash_duration = duration if duration is not None else 0.35
        self.damage_flash_timer = self.damage_flash_duration

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
            if path.is_file() and path.name != "section_00.json"
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
        # Player / run state
        # ----------------------------------------------------------

        # Reset the run-specific state so each restart starts from a clean
        # slate instead of reusing the previous death state's inventory,
        # oxygen, and traversal data.
        self.inventory = Inventory()
        self.oxygen_system = OxygenSystem(max_oxygen=100.0, drain_rate=2.0)
        self.oxygen_percent = self.oxygen_system.percent
        self.oxygen_fade_timer = 0.0
        self.damage_flash_timer = 0.0
        self.silt_intensity = 0.0
        self.vent_heat_intensity = 0.0
        self.low_oxygen_intensity = 0.0
        self.low_oxygen_audio_active = False
        self.current_audio_active = False
        self.silt_audio_active = False
        self.thermal_audio_active = False
        self.heartbeat_audio_active = False
        self.death_audio_played = False
        self.active_item_label = ""
        self.showing_endless_confirmation = False
        self.lore_collection_active = False

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

        if self.lore_collection_active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                action = self.lore_collection.handle_events(event, mouse_pos)
                if action == "DISMISS":
                    self.lore_collection_active = False
                    self.play_sound("menu")
            return

        for event in pygame.event.get():

            # pygame.QUIT is generated when the player closes
            # the application window.
            if event.type == pygame.QUIT:
                self.save_progress()
                self.running = False

            if self.game_state == GameState.MAIN_MENU and not self.showing_endless_confirmation:
                action = self.main_menu.handle_events(event, mouse_pos)
                if action == "PLAY":
                    self.play_sound("menu")
                    self.showing_endless_confirmation = True
                elif action == "EXIT":
                    self.play_sound("menu")
                    self.save_progress()
                    self.running = False

            if self.showing_endless_confirmation:
                action = self.endless_run_confirmation.handle_events(event, mouse_pos)
                if action == "START_ENDLESS":
                    self.play_sound("confirm")
                    self.showing_endless_confirmation = False
                    self.game_state = GameState.PLAYING
                elif action == "CANCEL":
                    self.play_sound("menu")
                    self.showing_endless_confirmation = False

            if self.game_state == GameState.PLAYING and event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.play_sound("menu")
                self.game_state = GameState.PAUSED
                self.pause_menu.confirming_quit = False

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.game_state == GameState.PLAYING:
                    self.play_sound("menu")
                    self.game_state = GameState.PAUSED
                elif self.game_state == GameState.PAUSED:
                    self.play_sound("menu")
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
                    self.play_sound("menu")
                    self.game_state = GameState.PLAYING
                    self.pause_menu.confirming_quit = False
                elif action == "QUIT_TO_MENU":
                    self.play_sound("menu")
                    self.save_progress()
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
                    self.play_sound("confirm")
                    self._start_new_run()
                    self.game_state = GameState.PLAYING
                elif action == "MAIN_MENU":
                    self.play_sound("menu")
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

        self.update_audio_volumes()

        if self.lore_collection_active:
            return

        self.damage_flash_timer = max(0.0, self.damage_flash_timer - delta_time)
        if self.damage_flash_timer > 0:
            self.damage_flash_elapsed = min(
                self.damage_flash_duration,
                self.damage_flash_elapsed + delta_time,
            )
        else:
            self.damage_flash_elapsed = 0.0
        self.silt_intensity = max(0.0, self.silt_intensity - (delta_time * 0.8))
        self.low_oxygen_intensity = max(0.0, self.low_oxygen_intensity - (delta_time * 1.0))
        self.inventory.update(delta_time)

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
        """Keep the menu display synced with persisted settings."""

        # The menu reads the latest saved max-distance and colour-blind
        # preference each frame so it reflects the most recent state without
        # requiring a full menu rebuild.
        self.main_menu.max_distance = SETTINGS.max_distance_travelled
        self.main_menu.color_blind_enabled = SETTINGS.color_blind_mode
        self.main_menu.update(delta_time)

    def update_pause_menu(
        self,
        delta_time: float,
    ):
        """Keep the pause overlay state coherent while gameplay is frozen."""

        # The pause screen is a modal overlay; no gameplay simulation should run
        # while it is active. The menu only needs to remain in sync with the
        # current inventory and selection state.
        self.pause_menu.pending_slot_selection = getattr(
            self.pause_menu,
            "pending_slot_selection",
            None,
        )

        # Ensure the visible inventory and active selection stay aligned with the
        # current run data.
        self.pause_menu.draw(self.screen, self.inventory.slots)

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
            if self.oxygen_fade_timer <= 0.0:
                self.oxygen_fade_timer = self.oxygen_fade_duration
                self.cause_of_death = "Drowning"
                self.play_sound("drowning")
            else:
                self.oxygen_fade_timer = max(0.0, self.oxygen_fade_timer - delta_time)
                if self.oxygen_fade_timer <= 0.0:
                    self.trigger_death_audio()
                    self.game_state = GameState.DEAD
                    return
            return

        self.oxygen_fade_timer = 0.0

        # ----------------------------------------------------------
        # Player movement
        # ----------------------------------------------------------

        self.player.update(
            delta_time,
            self.collision_system,
        )

        if self.player.wall_touching:
            self.start_looping_sound("scrape")
            if self.player.consume_wall_scrape():
                self.trigger_damage_feedback((120, 120, 130), 0.08)
        else:
            self.stop_sound("scrape")
            self.player.wall_scrape_buffer = 0.0
            self.player.end_wall_scrape()

        self.check_item_pickups()
        self.update_item_physics(delta_time)

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

        current_active = any(
            current.get_force_at_position(self.player.position).length_squared() > 0
            for current in self.currents
        )
        if current_active and not self.current_audio_active:
            self.play_sound("current")
        self.current_audio_active = current_active

        # ----------------------------------------------------------
        # Silt clouds
        # ----------------------------------------------------------

        silt_active = False
        for cloud in self.silt_clouds:
            cloud.update(delta_time)
            offset = cloud.position - self.player.position
            if offset.length() <= cloud.effect_radius:
                silt_active = True
                self.silt_intensity = max(self.silt_intensity, 0.85)
                self.player.velocity *= 1.0 - min(0.75, cloud.speed_reduction * 0.75)
        if not silt_active:
            self.silt_intensity = max(0.0, self.silt_intensity - (delta_time * 1.5))
        if silt_active and not self.silt_audio_active:
            self.play_sound("silt")
        self.silt_audio_active = silt_active

        # ----------------------------------------------------------
        # Thermal vents
        # ----------------------------------------------------------

        thermal_active = False
        for vent in self.thermal_vents:
            vent.update(delta_time)
            damage = vent.get_damage_at_position(self.player.position) * delta_time
            if damage > 0:
                thermal_active = True
                self.player.apply_damage(damage)
                self.trigger_damage_feedback((255, 160, 40), 0.2)
                if self.player.health <= 0:
                    self.cause_of_death = "Thermal vent"
                    self.trigger_death_audio()
                    self.game_state = GameState.DEAD
                    return
        if thermal_active:
            self.start_looping_sound("thermal")
        elif self.thermal_audio_active:
            self.stop_sound("thermal")
        self.thermal_audio_active = thermal_active

        if self.oxygen_percent < 25.0:
            self.low_oxygen_intensity = max(self.low_oxygen_intensity, 1.0)
            if not self.low_oxygen_audio_active:
                self.play_sound("oxygen_warning")
            self.low_oxygen_audio_active = True
        else:
            self.low_oxygen_intensity = max(0.0, self.low_oxygen_intensity - (delta_time * 1.2))
            self.low_oxygen_audio_active = False

        if self.player.health <= 25:
            self.start_looping_sound("heartbeat")
            self.heartbeat_audio_active = True
        elif self.heartbeat_audio_active:
            self.stop_sound("heartbeat")
            self.heartbeat_audio_active = False

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

    def save_progress(self) -> None:
        """Persist settings and the best distance reached by the current run."""
        if self.distance_travelled > SETTINGS.max_distance_travelled:
            SETTINGS.max_distance_travelled = int(self.distance_travelled)
        save_settings(SETTINGS)

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

        self.save_progress()

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

        if SETTINGS.color_blind_mode and self.game_state in (GameState.PLAYING, GameState.PAUSED):
            # Lift the darkest pixels so cave geometry and actors remain visible.
            self.screen.fill((28, 28, 28), special_flags=pygame.BLEND_RGB_ADD)

        if self.game_state in (GameState.PLAYING, GameState.PAUSED):

            # ------------------------------------------------------
            # Draw thermal vents behind all gameplay geometry and actors.
            # ------------------------------------------------------

            for vent in self.thermal_vents:
                vent.draw(
                    self.screen,
                    self.camera,
                )

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

        if self.lore_collection_active:
            self.lore_collection.draw(self.screen)

        if self.damage_flash_timer > 0:
            fade_in = min(1.0, self.damage_flash_elapsed / 0.06)
            fade_out = self.damage_flash_timer / max(self.damage_flash_duration, 0.01)
            alpha = int(min(fade_in, fade_out) * 60)
            flash_color = (255, 220, 40) if SETTINGS.color_blind_mode else self.damage_flash_color
            self.overlay_surface.fill((*flash_color, alpha))
            self.screen.blit(self.overlay_surface, (0, 0))

        if self.oxygen_fade_timer > 0:
            fade_progress = 1.0 - (self.oxygen_fade_timer / max(self.oxygen_fade_duration, 0.01))
            fade_alpha = int(fade_progress * 220)
            self.overlay_surface.fill((0, 0, 0, fade_alpha))
            self.screen.blit(self.overlay_surface, (0, 0))

        if self.silt_intensity > 0.05:
            alpha = int(self.silt_intensity * (120 if SETTINGS.color_blind_mode else 180))
            silt_color = (55, 55, 30) if SETTINGS.color_blind_mode else (12, 22, 26)
            self.overlay_surface.fill((*silt_color, alpha))
            self.screen.blit(self.overlay_surface, (0, 0))

        if self.low_oxygen_intensity > 0.05:
            alpha = int(self.low_oxygen_intensity * 80)
            oxygen_color = (0, 180, 220) if SETTINGS.color_blind_mode else (40, 120, 170)
            self.overlay_surface.fill((*oxygen_color, alpha))
            self.screen.blit(self.overlay_surface, (0, 0))

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
                self.draw_wall(element)
            elif element.element_type == "obstacle":
                self.draw_obstacle(element)

        for element in elements:
            if element.element_type in ("item", "lore_fragment"):
                self.draw_item(element)

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

        world_points = element.get_world_points()

        if len(world_points) < 3:
            return

        cache_key = f"{element.element_id}:{round(element.position.x)}:{round(element.position.y)}"

        self._draw_tiled_polygon(
            self.screen,
            world_points,
            self.wall_texture,
            cache_key,
        )

    def _load_wall_texture(self) -> pygame.Surface:
        """Load the seamless cave wall texture used for tiled walls."""

        return pygame.image.load(
            str(WALL_TEXTURE_PATH)
        ).convert_alpha()

    def _draw_tiled_polygon(
        self,
        screen: pygame.Surface,
        world_points: list[pygame.Vector2],
        texture: pygame.Surface,
        cache_key: str,
    ) -> None:
        """Tile a texture across a polygon and clip it to the polygon shape."""

        cached = self.wall_polygon_cache.get(cache_key)

        if cached is None:
            min_x = math.floor(
                min(point.x for point in world_points)
            )
            min_y = math.floor(
                min(point.y for point in world_points)
            )
            max_x = math.ceil(
                max(point.x for point in world_points)
            )
            max_y = math.ceil(
                max(point.y for point in world_points)
            )

            width = max(1, max_x - min_x)
            height = max(1, max_y - min_y)

            tiled_surface = pygame.Surface(
                (width, height),
                pygame.SRCALPHA,
            )

            tile_width, tile_height = texture.get_size()
            start_x = math.floor(min_x / tile_width) * tile_width
            start_y = math.floor(min_y / tile_height) * tile_height

            for y in range(start_y, max_y + tile_height, tile_height):
                for x in range(start_x, max_x + tile_width, tile_width):
                    tiled_surface.blit(
                        texture,
                        (
                            x - min_x,
                            y - min_y,
                        ),
                    )

            clip_surface = pygame.Surface(
                (width, height),
                pygame.SRCALPHA,
            )

            local_points = [
                (
                    point.x - min_x,
                    point.y - min_y,
                )
                for point in world_points
            ]

            pygame.draw.polygon(
                clip_surface,
                (
                    255,
                    255,
                    255,
                    255,
                ),
                local_points,
            )

            tiled_surface.blit(
                clip_surface,
                (0, 0),
                special_flags=pygame.BLEND_RGBA_MULT,
            )

            cached = (tiled_surface, min_x, min_y)
            self.wall_polygon_cache[cache_key] = cached

        tiled_surface, min_x, min_y = cached

        screen_origin = self.camera.world_to_screen(pygame.Vector2(min_x, min_y))
        destination_rect = tiled_surface.get_rect(
            topleft=(
                math.floor(screen_origin.x),
                math.floor(screen_origin.y),
            )
        )

        if not destination_rect.colliderect(self.screen.get_rect()):
            return

        screen.blit(
            tiled_surface,
            destination_rect,
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
        rotation = float(element.properties.get("rotation", 0.0))
        if item_type == "oxygen_tank":
            sprite = self.item_sprites["oxygen_tank"]
            rotated_sprite = pygame.transform.rotate(sprite, rotation)
            sprite_rect = rotated_sprite.get_rect(center=(int(screen_position.x), int(screen_position.y)))
            self.screen.blit(rotated_sprite, sprite_rect)
        elif item_type == "med_kit":
            sprite = self.item_sprites["med_kit"]
            rotated_sprite = pygame.transform.rotate(sprite, rotation)
            sprite_rect = rotated_sprite.get_rect(center=(int(screen_position.x), int(screen_position.y)))
            self.screen.blit(rotated_sprite, sprite_rect)
        elif item_type == "lore_fragment":
            sprite = self.item_sprites["lore_fragment"]
            rotated_sprite = pygame.transform.rotate(sprite, rotation)
            sprite_rect = rotated_sprite.get_rect(center=(int(screen_position.x), int(screen_position.y)))
            self.screen.blit(rotated_sprite, sprite_rect)
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
            label = self.debug_font_small.render(
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

        debug_text = (
            f"State: {self.game_state.name} | "
            f"FPS: {self.clock.get_fps():.1f} | "
            f"Sections: "
            f"{len(self.level_manager.sections)}"
        )

        text_surface = self.debug_font_large.render(
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
                radius=float(properties.get("radius", 24)) * 2.5,
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
                radius=float(properties.get("radius", 26.0)) * 2.5,
                heat_radius=float(properties.get("heat_radius", 100.0)) * 2.5,
                heat_damage=float(properties.get("heat_damage", 5.0)),
                eruption_damage=float(properties.get("eruption_damage", 20.0)),
                eruption_duration=1.0,
                eruption_interval=5.0,
                haze_length=float(properties.get("haze_length", 95.0)) * 2.5,
                vent_width=float(properties.get("vent_width", 30.0)) * 2.5,
                haze_alpha=int(properties.get("haze_alpha", 65)),
                bubble_count=int(properties.get("bubble_count", 14)),
                bubble_speed=float(properties.get("bubble_speed", 1.0)),
            )
            self.thermal_vents.add(vent)


    def _random_lore_snippet(self) -> str:
        """Load a random lore snippet from the data file."""
        path = DATA_DIR / "lore_snippets.json"
        try:
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            snippets = payload.get("snippets", [])
            if snippets:
                return random.choice(snippets)
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass
        return "The cave keeps its secrets."

    def trigger_lore_collection(self, element: LevelElement) -> None:
        """Open a lore modal instead of placing the item into the hotbar."""
        if self.lore_collection_active:
            return
        if element.properties.get("lore_seen"):
            return

        element.properties["lore_seen"] = True
        self.lore_collection.set_text(self._random_lore_snippet())
        self.lore_collection_active = True
        self.play_sound("pickup")

    def check_item_pickups(self):
        """Collect nearby world items into the hotbar when a slot is free."""
        for section_instance in self.level_manager.sections:
            dropped_items = section_instance.runtime_state.get("dropped_items", [])
            for element in [*section_instance.section.elements, *dropped_items]:
                if element.element_type == "lore_fragment":
                    radius = float(element.properties.get("interaction_radius", 48.0))
                    item_position = element.position + section_instance.world_offset
                    if self.player.position.distance_to(item_position) <= radius:
                        self.trigger_lore_collection(element)
                    continue

                if element.element_type != "item":
                    continue

                if element.properties.get("collected"):
                    continue

                radius = float(element.properties.get("pickup_radius", 48.0))
                item_position = element.position + section_instance.world_offset
                if self.player.position.distance_to(item_position) <= radius:
                    item_type = str(element.properties.get("item_type", "oxygen_tank"))
                    if item_type == "lore_fragment":
                        self.trigger_lore_collection(element)
                        continue
                    if not self.inventory.can_pickup(item_type):
                        continue
                    if self.inventory.add_item(item_type):
                        element.properties["collected"] = True
                        element.properties["in_inventory"] = True
                        self.play_sound("pickup")

    ITEM_SINK_SPEED = 60.0
    ITEM_SINK_SIZE = 16

    def update_item_physics(self, delta_time: float) -> None:
        """Make world items (placed or dropped) sink until they rest on a wall."""
        half_size = self.ITEM_SINK_SIZE / 2
        fall_distance = self.ITEM_SINK_SPEED * delta_time

        for section_instance in self.level_manager.sections:
            world_offset = section_instance.world_offset
            dropped_items = section_instance.runtime_state.get("dropped_items", [])

            for element in [*section_instance.section.elements, *dropped_items]:
                if element.element_type != "item":
                    continue
                if element.properties.get("collected"):
                    continue

                world_position = element.position + world_offset
                new_y = world_position.y + fall_distance

                probe_rect = pygame.Rect(
                    world_position.x - half_size,
                    new_y - half_size,
                    self.ITEM_SINK_SIZE,
                    self.ITEM_SINK_SIZE,
                )

                if self.collision_system.check_collision(probe_rect):
                    continue

                element.position.y += fall_distance

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
            self.play_sound("pickup")
        elif item_name == "med_kit":
            self.player.health = min(100, self.player.health + 25)
            self.play_sound("pickup")

    def drop_active_item(self):
        """Drop the currently selected hotbar item into the world."""
        item_name = self.inventory.drop_active()
        if item_name is None:
            return

        current_section = self.level_manager.get_current_section()
        if current_section is None:
            if self.level_manager.sections:
                current_section = self.level_manager.sections[0]
            else:
                return

        world_offset = getattr(current_section, "world_offset", pygame.Vector2(0, 0))
        # Eject the item slightly behind the player so it appears visibly in open water
        ejection_offset = pygame.Vector2(-self.player.facing * 75.0, 10.0)
        drop_pos = self.player.position + ejection_offset
        local_pos = drop_pos - world_offset

        dropped = LevelElement(
            element_id=f"dropped_{item_name}_{abs(hash((drop_pos.x, drop_pos.y, item_name)))}",
            element_type="item",
            position=local_pos,
            properties={
                "item_type": item_name,
                "pickup_radius": 48.0,
                "collected": False,
                "in_inventory": False,
                "rotation": random.uniform(0.0, 360.0),
            },
        )

        self.level_manager.add_dropped_item(current_section, dropped)
        self.play_sound("pickup")

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
            self.trigger_damage_feedback()
            self.play_sound("damage")
            self.trigger_death_audio()
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
            self.trigger_damage_feedback()
            self.play_sound("damage")
            self.trigger_death_audio()
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
        self.save_progress()
        if self.audio_enabled:
            pygame.mixer.music.stop()
        pygame.quit()