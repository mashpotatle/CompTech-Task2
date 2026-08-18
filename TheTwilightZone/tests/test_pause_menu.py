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


def test_pause_menu_inventory_swap_uses_real_slots():
    menu = PauseMenu(800, 600)
    menu.pending_slot_selection = 0

    inventory = ["med_kit", "oxygen_tank", None, None, None]
    slot_2 = menu.inventory_slot_rects(800, 600)[1]

    old_mods = pygame.key.get_mods()
    pygame.key.set_mods(pygame.KMOD_SHIFT)
    try:
        click_event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"button": 1, "pos": slot_2.center},
        )
        action = menu.handle_events(click_event, slot_2.center, inventory)
    finally:
        pygame.key.set_mods(old_mods)

    assert action == ("SWAP_SLOTS", (0, 1))
    assert menu.pending_slot_selection is None
