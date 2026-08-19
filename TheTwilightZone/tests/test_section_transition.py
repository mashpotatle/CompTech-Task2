import os
import unittest

import pygame

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from game.game import Game
from levels.level_manager import LevelManager


class SectionTransitionTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.game = Game()

    def test_check_section_exit_advances_when_player_reaches_current_section_exit(self) -> None:
        current_instance = self.game.level_manager.get_current_section()
        self.assertIsNotNone(current_instance)

        current_exit_world = (
            current_instance.world_offset + current_instance.section.exit_position
        )

        self.game.player.position = current_exit_world + pygame.Vector2(-30, 0)
        self.game.player.velocity = pygame.Vector2(1.0, 0.0)
        self.game.player.rect.center = (
            round(self.game.player.position.x),
            round(self.game.player.position.y),
        )

        self.game.check_section_exit()

        self.assertIsNotNone(self.game.current_section_instance)
        self.assertNotEqual(
            self.game.current_section_instance.template_filename,
            current_instance.template_filename,
        )

    def test_prunes_sections_once_player_has_moved_past_them(self) -> None:
        level_manager = LevelManager(
            os.path.join(os.path.dirname(__file__), "..", "data", "cave_sections"),
            [
                "section_01.json",
                "section_02.json",
                "section_04.json",
                "section_05.json",
            ],
            preload_section_count=0,
        )

        level_manager.load_initial_section("section_01.json")
        level_manager.stitch_next_section("section_02.json")
        level_manager.stitch_next_section("section_04.json")

        level_manager.current_section_index = 2
        level_manager._prune_old_sections()

        self.assertEqual(len(level_manager.sections), 2)
        self.assertEqual(
            [instance.template_filename for instance in level_manager.sections],
            ["section_02.json", "section_04.json"],
        )
        self.assertEqual(level_manager.current_section_index, 1)


if __name__ == "__main__":
    unittest.main()
