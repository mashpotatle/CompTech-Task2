import math

import pygame

from data.assets.player_model import create_player_sprite
from settings import SETTINGS, save_settings
from ui import theme
from ui.layout import load_layout


class UIButton:
    """A tiny button built from Pygame rectangles and text."""

    def __init__(self, x, y, width, height, text, font, base_color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.base_color = base_color
        self.hover_color = hover_color
        self.hovered = False

        self.label = self.font.render(text, True, theme.COLOR_TEXT)
        self.label_rect = self.label.get_rect(center=self.rect.center)

    def check_hover(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
        return self.hovered

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False

    def draw(self, surface):
        color = self.hover_color if self.hovered else self.base_color
        pygame.draw.rect(surface, color, self.rect, border_radius=theme.BUTTON_BORDER_RADIUS)
        pygame.draw.rect(
            surface, theme.COLOR_BORDER, self.rect, theme.BUTTON_BORDER_WIDTH, border_radius=theme.BUTTON_BORDER_RADIUS
        )
        surface.blit(self.label, self.label_rect)


class MainMenu:
    """A simple main menu with play, exit, and settings options."""

    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height
        self.font_title = pygame.font.Font(None, theme.FONT_TITLE)
        self.font_headline = pygame.font.Font(None, theme.FONT_HEADLINE)
        self.font_large = pygame.font.Font(None, theme.FONT_LARGE)
        self.font_medium = pygame.font.Font(None, theme.FONT_MEDIUM)
        self.font_small = pygame.font.Font(None, theme.FONT_SMALL)

        self.text_color = theme.COLOR_TEXT
        self.panel_color = theme.COLOR_PANEL
        self.btn_color = theme.COLOR_BUTTON
        self.btn_hover = theme.COLOR_BUTTON_HOVER
        self.accent_color = theme.COLOR_ACCENT

        self.max_distance = SETTINGS.max_distance_travelled
        self.color_blind_enabled = SETTINGS.color_blind_mode

        # Rects/text are authored visually with the uicreator tool and saved
        # to data/ui/main_menu.json; the hardcoded rects below are only a
        # fallback in case that file is missing.
        self.layout = load_layout("main_menu")
        self.preview_time = 0.0
        self.preview_player = create_player_sprite(136, 74)

        button_x = 120
        play_y = 285
        exit_y = play_y + theme.BUTTON_HEIGHT + theme.BUTTON_SPACING

        play_rect = self.layout.rect(
            "btn_play", pygame.Rect(button_x, play_y, theme.BUTTON_WIDTH, theme.BUTTON_HEIGHT)
        )
        self.btn_play = UIButton(
            play_rect.x,
            play_rect.y,
            play_rect.width,
            play_rect.height,
            self.layout.get("btn_play", "text", "-> Play"),
            self.font_large,
            self.btn_color,
            self.btn_hover,
        )
        exit_rect = self.layout.rect(
            "btn_exit", pygame.Rect(button_x, exit_y, theme.BUTTON_WIDTH, theme.BUTTON_HEIGHT)
        )
        self.btn_exit = UIButton(
            exit_rect.x,
            exit_rect.y,
            exit_rect.width,
            exit_rect.height,
            self.layout.get("btn_exit", "text", "X Exit Game"),
            self.font_large,
            self.btn_color,
            theme.COLOR_BUTTON_DANGER_HOVER,
        )
        self.panel_rect = self.layout.rect(
            "panel_settings",
            pygame.Rect(self.width - 374, 145, 350, 360),
        )

    def update(self, delta_time):
        """Advance the small animated diver shown behind the menu."""
        self.preview_time += max(0.0, delta_time)

    def _draw_preview(self, surface):
        theme.draw_gradient_background(surface, self.width, self.height)

        player_x = int(self.width * 0.52)
        player_y = int(self.height * 0.52 + math.sin(self.preview_time * 1.8) * 8)
        player_rect = self.preview_player.get_rect(center=(player_x, player_y))
        surface.blit(self.preview_player, player_rect)

    def handle_events(self, event, mouse_pos):
        self.btn_play.check_hover(mouse_pos)
        self.btn_exit.check_hover(mouse_pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_play.handle_event(event):
                return "PLAY"
            if self.btn_exit.handle_event(event):
                return "EXIT"

            toggle_rect = pygame.Rect(self.panel_rect.x + 20, self.panel_rect.y + 70, 24, 24)
            if toggle_rect.collidepoint(event.pos):
                SETTINGS.color_blind_mode = not SETTINGS.color_blind_mode
                self.color_blind_enabled = SETTINGS.color_blind_mode
                save_settings(SETTINGS)
                return None

            self._handle_slider_click(event.pos)

        if event.type == pygame.MOUSEMOTION and event.buttons[0]:
            self._handle_slider_drag(event.pos)

        return None

    def draw(self, surface):
        self._draw_preview(surface)

        pygame.draw.circle(surface, (20, 120, 140), (self.width // 2, 180), 88, 2)
        pygame.draw.circle(surface, (20, 120, 140), (self.width // 2, 180), 58, 1)
        pygame.draw.circle(surface, self.accent_color, (self.width // 2, 180), 22, 2)

        title_surf = self.font_title.render("The Twilight Zone", True, self.text_color)
        title_rect = title_surf.get_rect(center=(self.width // 2, 90))
        surface.blit(title_surf, title_rect)

        distance_label = self.font_medium.render("Max Distance", True, self.text_color)
        distance_value = self.font_headline.render(f"{self.max_distance} m", True, self.accent_color)
        surface.blit(distance_label, (120, 170))
        surface.blit(distance_value, (120, 205))

        self.btn_play.draw(surface)
        self.btn_exit.draw(surface)

        panel_rect = self.panel_rect
        pygame.draw.rect(surface, self.panel_color, panel_rect, border_radius=theme.PANEL_BORDER_RADIUS)
        pygame.draw.rect(
            surface, theme.COLOR_BORDER, panel_rect, theme.PANEL_BORDER_WIDTH, border_radius=theme.PANEL_BORDER_RADIUS
        )

        panel_title = self.font_medium.render(
            self.layout.get("panel_settings", "text", "Settings"), True, self.text_color
        )
        surface.blit(panel_title, (panel_rect.x + 20, panel_rect.y + 18))

        toggle_rect = pygame.Rect(panel_rect.x + 20, panel_rect.y + 70, 24, 24)
        pygame.draw.rect(surface, self.text_color, toggle_rect)
        if self.color_blind_enabled:
            pygame.draw.rect(surface, self.accent_color, toggle_rect.inflate(-8, -8))

        toggle_label = self.font_small.render("Color Blind Mode", True, self.text_color)
        surface.blit(toggle_label, (panel_rect.x + 56, panel_rect.y + 72))

        self._draw_volume_slider(surface, panel_rect.x + 25, panel_rect.y + 130, "Master", SETTINGS.master_volume)
        self._draw_volume_slider(surface, panel_rect.x + 25, panel_rect.y + 175, "Ambience", SETTINGS.ambience_volume)
        self._draw_volume_slider(surface, panel_rect.x + 25, panel_rect.y + 220, "Menus", SETTINGS.menus_volume)
        self._draw_volume_slider(surface, panel_rect.x + 25, panel_rect.y + 265, "Game", SETTINGS.game_volume)

    def _handle_slider_click(self, pos):
        panel_rect = self.panel_rect
        slider_positions = [
            (panel_rect.x + 25, panel_rect.y + 130),
            (panel_rect.x + 25, panel_rect.y + 175),
            (panel_rect.x + 25, panel_rect.y + 220),
            (panel_rect.x + 25, panel_rect.y + 265),
        ]

        for index, (x, y) in enumerate(slider_positions):
            bar_rect = pygame.Rect(x, y + 22, 150, 8)
            if bar_rect.collidepoint(pos):
                local_x = max(0, min(150, pos[0] - x))
                percent = int((local_x / 150) * 100)
                if index == 0:
                    SETTINGS.master_volume = percent
                elif index == 1:
                    SETTINGS.ambience_volume = percent
                elif index == 2:
                    SETTINGS.menus_volume = percent
                elif index == 3:
                    SETTINGS.game_volume = percent
                save_settings(SETTINGS)
                return

    def _handle_slider_drag(self, pos):
        self._handle_slider_click(pos)

    def _draw_volume_slider(self, surface, x, y, label, percent):
        label_surf = self.font_small.render(label, True, self.text_color)
        surface.blit(label_surf, (x, y))

        bar_rect = pygame.Rect(x, y + 22, 150, 8)
        pygame.draw.rect(surface, (70, 70, 70), bar_rect, border_radius=theme.BAR_BORDER_RADIUS)
        fill_width = int(150 * (percent / 100))
        pygame.draw.rect(
            surface, self.accent_color, pygame.Rect(x, y + 22, fill_width, 8), border_radius=theme.BAR_BORDER_RADIUS
        )
        percent_surf = self.font_small.render(f"{percent}%", True, self.text_color)
        surface.blit(percent_surf, (x + 165, y - 2))


class EndlessRunConfirmation:
    """A confirmation overlay for starting an endless run."""

    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height
        self.font_headline = pygame.font.Font(None, theme.FONT_HEADLINE)
        self.font_large = pygame.font.Font(None, theme.FONT_LARGE)

        self.text_color = theme.COLOR_TEXT
        self.btn_color = theme.COLOR_BUTTON
        self.btn_hover = theme.COLOR_BUTTON_HOVER

        yes_rect, no_rect = theme.confirm_button_positions(self.width // 2, 270)

        self.btn_yes = UIButton(
            yes_rect.x,
            yes_rect.y,
            yes_rect.width,
            yes_rect.height,
            "Yes",
            self.font_large,
            self.btn_color,
            theme.COLOR_BUTTON_CONFIRM_HOVER,
        )
        self.btn_no = UIButton(
            no_rect.x,
            no_rect.y,
            no_rect.width,
            no_rect.height,
            "No",
            self.font_large,
            self.btn_color,
            theme.COLOR_BUTTON_DANGER_HOVER,
        )

    def handle_events(self, event, mouse_pos):
        self.btn_yes.check_hover(mouse_pos)
        self.btn_no.check_hover(mouse_pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_no.handle_event(event):
                return "CANCEL"
            if self.btn_yes.handle_event(event):
                return "START_ENDLESS"

        return None

    def draw(self, surface):
        theme.draw_modal_overlay(surface, self.width, self.height)

        prompt_surf = self.font_headline.render("Do you want to start an endless run?", True, self.text_color)
        prompt_rect = prompt_surf.get_rect(center=(self.width // 2, 150))
        surface.blit(prompt_surf, prompt_rect)

        self.btn_yes.draw(surface)
        self.btn_no.draw(surface)


class LoreCollectionScreen:
    """Modal panel showing a located lore fragment snippet."""

    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height
        self.layout = load_layout("lore_collection")
        self.font_headline = pygame.font.Font(None, theme.FONT_HEADLINE)
        self.font_small = pygame.font.Font(None, theme.FONT_SMALL)
        self.text_color = theme.COLOR_TEXT
        self.panel_color = theme.COLOR_PANEL
        self.btn_color = theme.COLOR_BUTTON
        self.btn_hover = theme.COLOR_BUTTON_HOVER

        self.visible = False
        self.text = "The cave keeps its secrets."

        self.panel_rect = self.layout.rect("panel", pygame.Rect(220, 170, 584, 360))
        dismiss_rect = self.layout.rect("btn_dismiss", pygame.Rect(392, 455, 240, 48))
        self.btn_dismiss = UIButton(
            dismiss_rect.x,
            dismiss_rect.y,
            dismiss_rect.width,
            dismiss_rect.height,
            "Dismiss",
            self.font_small,
            self.btn_color,
            self.btn_hover,
        )

    def set_text(self, text: str):
        self.text = text or "The cave keeps its secrets."
        self.visible = True

    def handle_events(self, event, mouse_pos):
        if not self.visible:
            return None
        self.btn_dismiss.check_hover(mouse_pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_dismiss.handle_event(event):
                self.visible = False
                return "DISMISS"
        return None

    def draw(self, surface):
        if not self.visible:
            return

        theme.draw_modal_overlay(surface, self.width, self.height)

        pygame.draw.rect(surface, self.panel_color, self.panel_rect, border_radius=theme.PANEL_BORDER_RADIUS)
        pygame.draw.rect(
            surface, theme.COLOR_BORDER, self.panel_rect, theme.PANEL_BORDER_WIDTH, border_radius=theme.PANEL_BORDER_RADIUS
        )

        title_rect = self.layout.rect("title", pygame.Rect(512, 210, 200, 40))
        title_surf = self.font_headline.render("Lore Fragment", True, self.text_color)
        surface.blit(title_surf, title_surf.get_rect(center=title_rect.center))

        body_rect = self.layout.rect("body", pygame.Rect(270, 260, 480, 160))
        lines = self._wrap_text(self.text, body_rect.width)
        start_y = body_rect.y + 8
        for index, line in enumerate(lines[:6]):
            label = self.font_small.render(line, True, self.text_color)
            surface.blit(label, (body_rect.x + 8, start_y + index * 28))

        self.btn_dismiss.draw(surface)

    def _wrap_text(self, text: str, width_px: int) -> list[str]:
        words = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            rendered = self.font_small.render(test, True, self.text_color)
            if rendered.get_width() > width_px and current:
                lines.append(current)
                current = word
            else:
                current = test
        if current:
            lines.append(current)
        return lines or [text]


class PauseMenu:
    """A pause overlay with a visible 5-slot hotbar and quit confirmation."""

    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height
        self.font_headline = pygame.font.Font(None, theme.FONT_HEADLINE)
        self.font_large = pygame.font.Font(None, theme.FONT_LARGE)
        self.font_tiny = pygame.font.Font(None, theme.FONT_TINY)

        self.confirming_quit = False
        self.pending_slot_selection = None

        self.bg_color = theme.COLOR_PANEL
        self.btn_color = theme.COLOR_BUTTON
        self.btn_hover = theme.COLOR_BUTTON_HOVER
        self.text_color = theme.COLOR_TEXT

        button_x = (self.width - theme.BUTTON_WIDTH) // 2
        resume_y = 200
        quit_y = resume_y + theme.BUTTON_HEIGHT + theme.BUTTON_SPACING

        self.btn_resume = UIButton(
            button_x,
            resume_y,
            theme.BUTTON_WIDTH,
            theme.BUTTON_HEIGHT,
            "Resume",
            self.font_large,
            self.btn_color,
            self.btn_hover,
        )
        self.btn_quit = UIButton(
            button_x,
            quit_y,
            theme.BUTTON_WIDTH,
            theme.BUTTON_HEIGHT,
            "Quit to Menu",
            self.font_large,
            self.btn_color,
            theme.COLOR_BUTTON_DANGER_HOVER,
        )
        close_rect = pygame.Rect(self.width - 76, 28, 48, 48)
        self.btn_close = UIButton(
            close_rect.x,
            close_rect.y,
            close_rect.width,
            close_rect.height,
            "X",
            self.font_large,
            self.btn_color,
            theme.COLOR_BUTTON_DANGER_HOVER,
        )

        yes_rect, no_rect = theme.confirm_button_positions(self.width // 2, 270)

        self.btn_yes = UIButton(
            yes_rect.x,
            yes_rect.y,
            yes_rect.width,
            yes_rect.height,
            "Yes",
            self.font_large,
            self.btn_color,
            theme.COLOR_BUTTON_CONFIRM_HOVER,
        )
        self.btn_no = UIButton(
            no_rect.x,
            no_rect.y,
            no_rect.width,
            no_rect.height,
            "No",
            self.font_large,
            self.btn_color,
            theme.COLOR_BUTTON_DANGER_HOVER,
        )

    def inventory_slot_rects(self, screen_width=None, screen_height=None):
        screen_width = screen_width or self.width
        screen_height = screen_height or self.height
        slot_radius = 30
        spacing = 20
        total_width = (slot_radius * 2 * 5) + (spacing * 4)
        start_x = (screen_width // 2) - (total_width // 2) + slot_radius
        start_y = screen_height - 100

        rects = []
        for index in range(5):
            x = start_x + (index * (slot_radius * 2 + spacing))
            rects.append(pygame.Rect(x - slot_radius, start_y - slot_radius, slot_radius * 2, slot_radius * 2))
        return rects

    def handle_events(self, event, mouse_pos, inventory=None):
        if not self.confirming_quit:
            self.btn_resume.check_hover(mouse_pos)
            self.btn_quit.check_hover(mouse_pos)
            self.btn_close.check_hover(mouse_pos)
            if inventory is not None:
                for index, rect in enumerate(self.inventory_slot_rects()):
                    if rect.collidepoint(mouse_pos):
                        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                                if self.pending_slot_selection is None:
                                    self.pending_slot_selection = index
                                else:
                                    first = self.pending_slot_selection
                                    second = index
                                    self.pending_slot_selection = None
                                    return ("SWAP_SLOTS", (first, second))
                            else:
                                self.pending_slot_selection = None
                                return ("SELECT_SLOT", index)
        else:
            self.btn_yes.check_hover(mouse_pos)
            self.btn_no.check_hover(mouse_pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.confirming_quit:
                if self.btn_close.handle_event(event):
                    return "RESUME"
                if self.btn_resume.handle_event(event):
                    return "RESUME"
                if self.btn_quit.handle_event(event):
                    self.confirming_quit = True
            else:
                if self.btn_no.handle_event(event):
                    self.confirming_quit = False
                if self.btn_yes.handle_event(event):
                    self.confirming_quit = False
                    return "QUIT_TO_MENU"

        return None

    def draw(self, surface, inventory=None):
        theme.draw_modal_overlay(surface, self.width, self.height)

        if not self.confirming_quit:
            title_surf = self.font_headline.render("PAUSED", True, self.text_color)
            title_rect = title_surf.get_rect(center=(self.width // 2, 120))
            surface.blit(title_surf, title_rect)

            self.btn_close.draw(surface)
            self.btn_resume.draw(surface)
            self.btn_quit.draw(surface)
        else:
            prompt_surf = self.font_headline.render("Are you sure?", True, self.text_color)
            prompt_rect = prompt_surf.get_rect(center=(self.width // 2, 150))
            surface.blit(prompt_surf, prompt_rect)

            self.btn_yes.draw(surface)
            self.btn_no.draw(surface)

        self._draw_inventory(surface, inventory)

    def _draw_inventory(self, surface, inventory):
        slot_radius = 30
        spacing = 20
        total_width = (slot_radius * 2 * 5) + (spacing * 4)
        start_x = (self.width // 2) - (total_width // 2) + slot_radius
        start_y = self.height - 100

        inventory = list(inventory) if inventory is not None else [None] * 5

        for index in range(5):
            x = start_x + (index * (slot_radius * 2 + spacing))
            rect = pygame.Rect(x - slot_radius, start_y - slot_radius, slot_radius * 2, slot_radius * 2)
            pygame.draw.circle(surface, (200, 200, 200), (x, start_y), slot_radius, 3)
            pygame.draw.circle(surface, (50, 50, 50), (x, start_y), slot_radius - 3)

            item = inventory[index]
            if item:
                text = "O₂" if item == "oxygen_tank" else "HP" if item == "med_kit" else item[:2].upper()
                label = self.font_tiny.render(text, True, self.text_color)
                surface.blit(label, label.get_rect(center=rect.center))

            if self.pending_slot_selection == index:
                pygame.draw.circle(surface, theme.COLOR_ACCENT, (x, start_y), slot_radius, 2)
