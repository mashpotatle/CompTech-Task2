"""Shared visual style constants for all menu/UI screens.

Centralising these values keeps button sizes, spacing, borders, and
colors consistent across the main menu, pause menu, confirmation
dialogs, HUD, hotbar, and death screen instead of each screen picking
its own one-off numbers.
"""

from __future__ import annotations

import pygame

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------

COLOR_BACKGROUND = (8, 12, 20)
COLOR_OVERLAY = (5, 12, 18, 190)
COLOR_PANEL = (34, 42, 50)
COLOR_BORDER = (255, 255, 255)
COLOR_TEXT = (255, 255, 255)
COLOR_ACCENT = (180, 120, 60)

COLOR_BUTTON = (80, 80, 80)
COLOR_BUTTON_HOVER = (120, 120, 120)
COLOR_BUTTON_CONFIRM_HOVER = (60, 190, 90)
COLOR_BUTTON_DANGER_HOVER = (200, 60, 60)

# ---------------------------------------------------------------------------
# Borders
# ---------------------------------------------------------------------------

BUTTON_BORDER_RADIUS = 8
BUTTON_BORDER_WIDTH = 2
PANEL_BORDER_RADIUS = 12
PANEL_BORDER_WIDTH = 2
BAR_BORDER_RADIUS = 6

# ---------------------------------------------------------------------------
# Button sizing / spacing
# ---------------------------------------------------------------------------

# Stacked full-size action buttons (Play/Exit, Resume/Quit).
BUTTON_WIDTH = 240
BUTTON_HEIGHT = 56
BUTTON_SPACING = 18

# Paired Yes/No confirmation buttons, shared by every confirmation dialog.
CONFIRM_BUTTON_WIDTH = 140
CONFIRM_BUTTON_HEIGHT = 52
CONFIRM_BUTTON_SPACING = 24

# ---------------------------------------------------------------------------
# Font sizes
# ---------------------------------------------------------------------------

FONT_TITLE = 84
FONT_HEADLINE = 60
FONT_LARGE = 40
FONT_MEDIUM = 30
FONT_SMALL = 24
FONT_TINY = 20


def draw_gradient_background(surface: pygame.Surface, width: int, height: int, bands: int = 8) -> None:
    """Fill a full screen with the shared dark teal ambient gradient."""
    surface.fill(COLOR_BACKGROUND)
    for band in range(bands):
        alpha = 18 + band * 7
        gradient = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(gradient, (15, 30, 42, alpha), gradient.get_rect())
        surface.blit(gradient, (0, 0))


def draw_modal_overlay(surface: pygame.Surface, width: int, height: int, bands: int = 4) -> None:
    """Darken the screen behind an in-game modal (pause menu, confirmations)."""
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill(COLOR_OVERLAY)
    surface.blit(overlay, (0, 0))

    band_height = height / bands
    for band in range(bands):
        band_rect = pygame.Rect(0, int(band * band_height), width, int(band_height))
        pygame.draw.rect(surface, (20, 40, 52, 30), band_rect)


def confirm_button_positions(center_x: int, y: int) -> tuple[pygame.Rect, pygame.Rect]:
    """Return (yes_rect, no_rect) for a centered Yes/No confirmation pair."""
    total_width = (CONFIRM_BUTTON_WIDTH * 2) + CONFIRM_BUTTON_SPACING
    start_x = center_x - total_width // 2
    yes_rect = pygame.Rect(start_x, y, CONFIRM_BUTTON_WIDTH, CONFIRM_BUTTON_HEIGHT)
    no_rect = pygame.Rect(
        start_x + CONFIRM_BUTTON_WIDTH + CONFIRM_BUTTON_SPACING, y, CONFIRM_BUTTON_WIDTH, CONFIRM_BUTTON_HEIGHT
    )
    return yes_rect, no_rect
