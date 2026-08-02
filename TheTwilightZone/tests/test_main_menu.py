import pygame

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
