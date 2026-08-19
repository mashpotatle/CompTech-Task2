import pygame

from game.game import Game
from game.game_state import GameState
from ui.menus import MainMenu


def test_main_menu_buttons_trigger_actions():
    pygame.init()
    menu = MainMenu(800, 600)

    play_event = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        {"button": 1, "pos": menu.btn_play.rect.center},
    )
    assert menu.handle_events(play_event, menu.btn_play.rect.center) == "PLAY"

    exit_event = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        {"button": 1, "pos": menu.btn_exit.rect.center},
    )
    assert menu.handle_events(exit_event, menu.btn_exit.rect.center) == "EXIT"


def test_restart_starts_a_fresh_run_state():
    pygame.init()
    game = Game()

    game.inventory.slots = ["med_kit", "oxygen_tank", None, None, None]
    game.inventory.active_index = 1
    game.oxygen_system.current = 0.0
    game.player.health = 0
    game.game_state = GameState.DEAD

    game._start_new_run()

    assert game.inventory.slots == [None, None, None, None, None]
    assert game.inventory.active_index == 0
    assert game.oxygen_system.current == game.oxygen_system.max_oxygen
    assert game.player.health == 100
    assert game.game_state == GameState.DEAD


def test_player_uses_horizontal_diver_sprite_and_hitbox():
    pygame.init()

    from entities.player import Player

    player = Player((0, 0))

    assert player.sprite.get_size() == (player.rect.width, player.rect.height)
    assert player.rect.width > player.rect.height
