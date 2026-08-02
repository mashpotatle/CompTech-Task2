import pygame

from game.game import Game
from game.game_state import GameState


def test_play_click_from_main_menu_opens_endless_confirmation(monkeypatch):
    pygame.init()
    game = Game()
    game.game_state = GameState.MAIN_MENU

    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: game.main_menu.btn_play.rect.center)

    pygame.event.clear()
    pygame.event.post(
        pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"button": 1, "pos": game.main_menu.btn_play.rect.center},
        )
    )

    game.handle_events()

    assert game.game_state == GameState.MAIN_MENU
    assert game.showing_endless_confirmation is True
