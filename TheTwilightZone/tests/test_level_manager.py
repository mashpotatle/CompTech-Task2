import unittest
from pathlib import Path

import pygame

from levels.level_manager import LevelManager


class LevelManagerTransitionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data_dir = Path(__file__).resolve().parents[1] / "data" / "cave_sections"
        self.manager = LevelManager(
            self.data_dir,
            available_sections=["section_02.json"],
            preload_section_count=0,
        )
        self.manager.load_initial_section("section_01.json")

    def test_transition_allows_zero_velocity_at_exit(self) -> None:
        current_instance = self.manager.get_current_section()
        self.assertIsNotNone(current_instance)

        exit_world_position = (
            current_instance.world_offset + current_instance.section.exit_position
        )

        next_instance = self.manager.transition_to_next_section(
            exit_world_position,
            pygame.Vector2(0.0, 0.0),
        )

        self.assertIsNotNone(next_instance)
        self.assertNotEqual(
            next_instance.template_filename,
            current_instance.template_filename,
        )


if __name__ == "__main__":
    unittest.main()
