from __future__ import annotations

import random
from pathlib import Path

import pygame

from settings import PRELOAD_SECTION_COUNT
from levels.cave_section import (
    CaveSection,
    LevelElement,
    SectionInstance,
)
from levels.level_loader import LevelLoader


class LevelManager:
    """
    Manages cave sections generated and placed into the persistent
    game world.

    Cave sections are modular pre-built level chunks. Each section
    stores its geometry in local coordinates, while LevelManager
    assigns it a permanent position in world space.

    Sections are randomly selected from the available section pool.

    Once a section has been generated and placed:

    - Its world position never changes.
    - It remains available for backtracking.
    - Its runtime state is preserved.
    - Dropped items can remain in the section.
    - Previously visited sections can be revisited.

    This allows the cave to behave as a persistent, procedurally
    assembled world rather than a fixed linear sequence.
    """

    def __init__(
        self,
        data_directory: str | Path,
        available_sections: list[str],
        preload_section_count: int | None = None,
    ):
        """
        Initialise the level manager.

        Args:
            data_directory:
                Directory containing cave section JSON files.

            available_sections:
                List of JSON filenames that may be randomly selected
                during cave generation.
        """

        self.loader = LevelLoader(
            data_directory
        )

        # ----------------------------------------------------------
        # Available section pool
        # ----------------------------------------------------------

        # These are the pre-built cave sections that can be selected
        # during procedural generation.

        discovered_sections = [
            path.name
            for path in sorted(
                (Path(data_directory)).glob("*.json")
            )
            if path.is_file()
        ]

        self.available_sections = list(
            dict.fromkeys(
                [*available_sections, *discovered_sections]
            )
        )

        self.preload_section_count = (
            preload_section_count
            if preload_section_count is not None
            else PRELOAD_SECTION_COUNT
        )

        # ----------------------------------------------------------
        # Loaded sections
        # ----------------------------------------------------------

        # Sections are stored in the order in which they exist
        # physically through the generated world.

        self.sections: list[
            SectionInstance
        ] = []

        # Runtime state is kept on each instance so the same template
        # can be instantiated multiple times without sharing state.

        # ----------------------------------------------------------
        # Active section
        # ----------------------------------------------------------

        # Index of the section currently containing the player.

        self.current_section_index = 0

        # ----------------------------------------------------------
        # Generation bookkeeping
        # ----------------------------------------------------------

        # Number of sections generated during this run.

        self.generated_section_count = 0

        # Filename of the most recently generated section.

        self.last_generated_filename: str | None = None

    # ==================================================================
    # INITIAL LOADING
    # ==================================================================

    def load_initial_section(
        self,
        filename: str,
    ) -> SectionInstance:
        """
        Load the initial cave section.

        The initial section is placed at world coordinate (0, 0).

        This completely resets the current generated world.
        """

        section = self.loader.load_section(
            filename
        )

        # ----------------------------------------------------------
        # Reset current world
        # ----------------------------------------------------------

        self.sections.clear()

        # ----------------------------------------------------------
        # Add initial section
        # ----------------------------------------------------------

        instance = SectionInstance(
            instance_id=0,
            template_filename=filename,
            section=section,
            world_offset=pygame.Vector2(0, 0),
            runtime_state={},
        )

        self.sections.append(instance)

        # ----------------------------------------------------------
        # Generation state
        # ----------------------------------------------------------

        self.current_section_index = 0

        self.generated_section_count = 1

        self.last_generated_filename = (
            filename
        )

        self._preload_following_sections()

        return instance

    def _get_loaded_sections_ahead_count(self) -> int:
        """
        Return how many loaded section instances sit after the current
        active section.
        """

        if not self.sections:
            return 0

        if not (
            0
            <= self.current_section_index
            < len(self.sections)
        ):
            return 0

        return max(
            0,
            len(self.sections)
            - self.current_section_index
            - 1,
        )

    def _preload_following_sections(self) -> None:
        """
        Ensure the current active section has the configured number of
        sections loaded ahead of it so transitions remain smooth.
        """

        if self.preload_section_count <= 0:
            return

        while (
            self._get_loaded_sections_ahead_count()
            < self.preload_section_count
        ):
            next_filename = (
                self.get_random_section_filename()
            )

            if next_filename is None:
                return

            self.stitch_next_section(
                next_filename
            )

    # ==================================================================
    # RANDOM SECTION SELECTION
    # ==================================================================

    def get_random_section_filename(
        self,
    ) -> str | None:
        """
        Select a random available cave section.

        The selection system is intentionally independent of the
        physical order of sections in the world.

        A section that is already loaded is avoided where possible.
        This prevents the generated cave from immediately producing
        duplicate chunks.

        The previously generated section is also avoided where
        possible to reduce immediate repetition.

        Returns:
            A filename suitable for generating the next section,
            or None if no suitable section is available.
        """

        if not self.available_sections:
            return None

        # ----------------------------------------------------------
        # Find valid files
        # ----------------------------------------------------------

        valid_sections = []

        for filename in self.available_sections:

            path = (
                self.loader.data_directory
                / filename
            )

            if path.exists():

                valid_sections.append(
                    filename
                )

        if not valid_sections:
            return None

        # ----------------------------------------------------------
        # Prefer sections that are not currently loaded
        # ----------------------------------------------------------

        unloaded_sections = [
            filename
            for filename in valid_sections
            if filename
            not in {
                instance.template_filename
                for instance in self.sections
            }
        ]

        if unloaded_sections:

            candidates = (
                unloaded_sections
            )

        else:

            # If every available section is already loaded,
            # allow reuse.
            #
            # This is important because a finite collection of
            # pre-built sections must be able to generate an
            # effectively longer cave.

            candidates = valid_sections

        # ----------------------------------------------------------
        # Avoid immediately repeating the previous section
        # ----------------------------------------------------------

        if (
            self.last_generated_filename
            in candidates
            and len(candidates) > 1
        ):

            candidates = [
                filename
                for filename in candidates
                if filename
                != self.last_generated_filename
            ]

        if not candidates:
            return None

        return random.choice(
            candidates
        )

    # ==================================================================
    # RANDOM GENERATION
    # ==================================================================

    def generate_next_random_section(
        self,
    ) -> SectionInstance | None:
        """
        Generate and stitch a randomly selected cave section.

        The selected section is attached to the end of the currently
        generated world.

        Its entry point is aligned with the previous section's exit.

        The section receives a permanent world offset.

        Returns:
            The newly generated CaveSection, or None if no section
            could be selected.
        """

        filename = (
            self.get_random_section_filename()
        )

        if filename is None:
            return None

        return self.stitch_next_section(
            filename
        )

    # ==================================================================
    # FORWARD STITCHING
    # ==================================================================

    def stitch_next_section(
        self,
        filename: str,
    ) -> SectionInstance:
        """
        Load and attach a section after the current final section.

        The section's entry position is aligned with the current
        final section's exit position.

        Once placed, the section's world offset never changes.

        If the requested filename is already loaded, the existing
        section is returned instead of creating a duplicate.
        """

        if not self.sections:

            return self.load_initial_section(
                filename
            )

        # ----------------------------------------------------------
        # Current final section
        # ----------------------------------------------------------

        current_instance = (
            self.sections[-1]
        )

        current_section = (
            current_instance.section
        )

        current_offset = (
            current_instance.world_offset
        )

        # ----------------------------------------------------------
        # Load next section
        # ----------------------------------------------------------

        next_section = (
            self.loader.load_section(
                filename
            )
        )

        # ----------------------------------------------------------
        # Calculate current exit in world coordinates
        # ----------------------------------------------------------

        current_exit_world = (
            current_offset
            + current_section.exit_position
        )

        # ----------------------------------------------------------
        # Calculate permanent world offset
        # ----------------------------------------------------------

        next_offset = (
            current_exit_world
            - next_section.entry_position
        )

        # ----------------------------------------------------------
        # Add section
        # ----------------------------------------------------------

        next_instance = SectionInstance(
            instance_id=self.generated_section_count,
            template_filename=filename,
            section=next_section,
            world_offset=next_offset,
            runtime_state={},
        )

        self.sections.append(next_instance)

        # ----------------------------------------------------------
        # Update generation state
        # ----------------------------------------------------------

        self.generated_section_count += 1

        self.last_generated_filename = (
            filename
        )

        return next_instance

    # ==================================================================
    # BACKWARD STITCHING
    # ==================================================================

    def stitch_previous_section(
        self,
        filename: str,
    ) -> SectionInstance:
        """
        Load and attach a section before the current first section.

        The previous section's exit is aligned with the current first
        section's entry.

        Existing sections are never moved.

        This is useful when expanding the world backwards, although
        normal gameplay currently generates new sections forwards
        and preserves them for backtracking.
        """

        if not self.sections:

            return self.load_initial_section(
                filename
            )

        # ----------------------------------------------------------
        # Current first section
        # ----------------------------------------------------------

        current_instance = (
            self.sections[0]
        )

        current_section = (
            current_instance.section
        )

        current_offset = (
            current_instance.world_offset
        )

        # ----------------------------------------------------------
        # Load previous section
        # ----------------------------------------------------------

        previous_section = (
            self.loader.load_section(
                filename
            )
        )

        # ----------------------------------------------------------
        # Calculate current entry in world coordinates
        # ----------------------------------------------------------

        current_entry_world = (
            current_offset
            + current_section.entry_position
        )

        # ----------------------------------------------------------
        # Calculate permanent world offset
        # ----------------------------------------------------------

        previous_offset = (
            current_entry_world
            - previous_section.exit_position
        )

        # ----------------------------------------------------------
        # Insert section
        # ----------------------------------------------------------

        previous_instance = SectionInstance(
            instance_id=self.generated_section_count,
            template_filename=filename,
            section=previous_section,
            world_offset=previous_offset,
            runtime_state={},
        )

        self.sections.insert(0, previous_instance)

        # ----------------------------------------------------------
        # Update active section index
        # ----------------------------------------------------------

        self.current_section_index += 1

        self.generated_section_count += 1

        return previous_instance

    # ==================================================================
    # ACTIVE SECTION
    # ==================================================================

    def update_active_section(
        self,
        player_position: pygame.Vector2,
    ):
        """
        Determine which loaded section currently contains the player.

        The active section index is updated when the player moves
        between sections.
        """

        for index, instance in enumerate(
            self.sections
        ):

            section = instance.section
            offset = instance.world_offset

            section_rect = pygame.Rect(
                round(
                    offset.x
                ),
                round(
                    offset.y
                ),
                round(
                    section.width
                ),
                round(
                    section.height
                ),
            )

            if section_rect.collidepoint(
                player_position
            ):

                self.current_section_index = (
                    index
                )

                self._preload_following_sections()

                return index

        return None

    def get_current_section(
        self,
    ) -> SectionInstance | None:
        """
        Return the section instance currently marked as active.
        """

        if not self.sections:
            return None

        if not (
            0
            <= self.current_section_index
            < len(
                self.sections
            )
        ):
            return None

        return self.sections[
            self.current_section_index
        ]

    def transition_to_next_section(
        self,
        player_position: pygame.Vector2,
        movement_direction: pygame.Vector2 | None = None,
    ) -> SectionInstance | None:
        """
        Move the player to the next section instance if they have
        reached the current section's exit.

        If the next section instance already exists in the generated
        world, the player is moved into that instance directly.
        Otherwise a new random section is generated and stitched to
        the end of the world.
        """

        current_instance = (
            self.get_current_section()
        )

        if current_instance is None:
            return None

        current_exit_world = (
            current_instance.world_offset
            + current_instance.section.exit_position
        )

        if movement_direction is not None:
            if movement_direction.x < 0:
                return None
            if movement_direction.x == 0 and movement_direction.y == 0:
                return None

        if (
            player_position.distance_to(
                current_exit_world
            )
            > 100
        ):
            return None

        next_index = (
            self.current_section_index + 1
        )

        if next_index < len(self.sections):
            self.current_section_index = (
                next_index
            )
            self._preload_following_sections()
            return self.sections[next_index]

        next_instance = (
            self.generate_next_random_section()
        )

        if next_instance is None:
            return None

        self.current_section_index = (
            len(self.sections) - 1
        )

        self._preload_following_sections()

        return next_instance

    # ==================================================================
    # WORLD ELEMENTS
    # ==================================================================

    def get_all_elements(
        self,
    ) -> list[LevelElement]:
        """
        Return all loaded elements in world coordinates.

        Static level data is copied before applying the section's
        permanent world offset.

        Runtime elements such as dropped items are also included.
        """

        world_elements = []

        for instance in self.sections:

            section = instance.section
            offset = instance.world_offset

            # ------------------------------------------------------
            # Static section elements
            # ------------------------------------------------------

            for element in section.elements:

                world_element = (
                    self._copy_element(
                        element
                    )
                )

                world_element.position += (
                    offset
                )

                world_elements.append(
                    world_element
                )

            # ------------------------------------------------------
            # Runtime elements
            # ------------------------------------------------------

            runtime_state = instance.runtime_state

            dropped_items = (
                runtime_state.get(
                    "dropped_items",
                    [],
                )
            )

            for item in dropped_items:

                runtime_element = (
                    self._copy_element(
                        item
                    )
                )

                runtime_element.position += (
                    offset
                )

                world_elements.append(
                    runtime_element
                )

        return world_elements

    # ==================================================================
    # RUNTIME STATE
    # ==================================================================

    def get_runtime_state(
        self,
        instance: SectionInstance,
    ) -> dict:
        """
        Return mutable runtime state belonging to a section instance.

        The state is created automatically if required.
        """

        if not instance.runtime_state:
            instance.runtime_state = {}

        return instance.runtime_state

    def add_dropped_item(
        self,
        instance: SectionInstance,
        item: LevelElement,
    ):
        """
        Add a dropped item to a section's runtime state.

        The item should use section-local coordinates.

        Its position is converted to world coordinates only when
        get_all_elements() is called.
        """

        runtime_state = (
            self.get_runtime_state(
                instance
            )
        )

        if (
            "dropped_items"
            not in runtime_state
        ):

            runtime_state[
                "dropped_items"
            ] = []

        runtime_state[
            "dropped_items"
        ].append(
            self._copy_element(
                item
            )
        )

    def remove_dropped_item(
        self,
        instance: SectionInstance,
        element_id: str,
    ):
        """
        Remove a dropped item from a section's runtime state.
        """

        runtime_state = (
            self.get_runtime_state(
                instance
            )
        )

        dropped_items = (
            runtime_state.get(
                "dropped_items",
                [],
            )
        )

        runtime_state[
            "dropped_items"
        ] = [
            item
            for item in dropped_items
            if item.element_id
            != element_id
        ]

    # ==================================================================
    # WORLD BOUNDS
    # ==================================================================

    def get_world_bounds(
        self,
    ) -> pygame.Rect:
        """
        Return the world-space bounds of all loaded sections.

        Because sections are never unloaded during normal gameplay,
        the bounds expand as the player explores further.
        """

        if not self.sections:

            return pygame.Rect(
                0,
                0,
                0,
                0,
            )

        minimum_x = float(
            "inf"
        )

        minimum_y = float(
            "inf"
        )

        maximum_x = float(
            "-inf"
        )

        maximum_y = float(
            "-inf"
        )

        for instance in self.sections:

            offset = instance.world_offset
            section = instance.section

            minimum_x = min(
                minimum_x,
                offset.x,
            )

            minimum_y = min(
                minimum_y,
                offset.y,
            )

            maximum_x = max(
                maximum_x,
                offset.x
                + section.width,
            )

            maximum_y = max(
                maximum_y,
                offset.y
                + section.height,
            )

        return pygame.Rect(
            round(
                minimum_x
            ),
            round(
                minimum_y
            ),
            round(
                maximum_x
                - minimum_x
            ),
            round(
                maximum_y
                - minimum_y
            ),
        )

    # ==================================================================
    # ENTRY / EXIT POSITIONS
    # ==================================================================

    def get_last_exit_position(
        self,
    ) -> pygame.Vector2 | None:
        """
        Return the world-space exit position of the final loaded
        section.
        """

        if not self.sections:

            return None

        instance = (
            self.sections[-1]
        )

        offset = instance.world_offset
        section = instance.section

        return (
            offset
            + section.exit_position
        )

    def get_first_entry_position(
        self,
    ) -> pygame.Vector2 | None:
        """
        Return the world-space entry position of the first loaded
        section.
        """

        if not self.sections:

            return None

        instance = (
            self.sections[0]
        )

        offset = instance.world_offset
        section = instance.section

        return (
            offset
            + section.entry_position
        )

    # ==================================================================
    # SECTION LOOKUP
    # ==================================================================

    def get_section_index(
        self,
        filename: str,
    ) -> int | None:
        """
        Return the loaded list index of a section.

        Returns None if the section is not currently loaded.
        """

        return self._find_section_index(
            filename
        )

    def get_section_filename(
        self,
        index: int,
    ) -> str | None:
        """
        Return the template filename associated with a loaded section
        instance index.
        """

        if not (
            0
            <= index
            < len(
                self.sections
            )
        ):

            return None

        return self.sections[
            index
        ].template_filename

    def get_loaded_section_count(
        self,
    ) -> int:
        """
        Return the number of sections currently loaded in memory.
        """

        return len(
            self.sections
        )

    # ==================================================================
    # INTERNAL HELPERS
    # ==================================================================

    def _find_section_index(
        self,
        filename: str,
    ) -> int | None:
        """
        Find a currently loaded section by template filename.
        """

        for index, instance in enumerate(
            self.sections
        ):
            if instance.template_filename == filename:
                return index

        return None

    @staticmethod
    def _copy_element(
        element: LevelElement,
    ) -> LevelElement:
        """
        Create a deep-enough copy of a LevelElement.

        Geometry vectors are copied so the original section data
        cannot accidentally be modified.
        """

        return LevelElement(
            element_id=element.element_id,
            element_type=element.element_type,
            position=element.position.copy(),
            points=[
                point.copy()
                for point in element.points
            ],
            properties=dict(
                element.properties
            ),
            material=dict(
                element.material
            ),
        )