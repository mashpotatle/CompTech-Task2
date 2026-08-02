import pygame

from ui.menus import PauseMenu


def test_pause_menu_quit_confirmation_flow():
    pygame.init()
    menu = PauseMenu(800, 600)

    quit_event = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        {"button": 1, "pos": menu.btn_quit.rect.center},
    )

    assert menu.handle_events(quit_event, menu.btn_quit.rect.center) is None
    assert menu.confirming_quit is True

    no_event = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        {"button": 1, "pos": menu.btn_no.rect.center},
    )

    assert menu.handle_events(no_event, menu.btn_no.rect.center) is None
    assert menu.confirming_quit is False

    assert menu.handle_events(quit_event, menu.btn_quit.rect.center) is None
    assert menu.confirming_quit is True

    yes_event = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        {"button": 1, "pos": menu.btn_yes.rect.center},
    )

    assert menu.handle_events(yes_event, menu.btn_yes.rect.center) == "QUIT_TO_MENU"
    assert menu.confirming_quit is False
