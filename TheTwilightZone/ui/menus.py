import pygame

from settings import SETTINGS
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

        self.label = self.font.render(text, True, (255, 255, 255))
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
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2, border_radius=6)
        surface.blit(self.label, self.label_rect)


class MainMenu:
    """A simple main menu with play, exit, and settings options."""

    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height
        self.font_title = pygame.font.Font(None, 84)
        self.font_large = pygame.font.Font(None, 56)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 28)

        self.text_color = (255, 255, 255)
        self.panel_color = (40, 40, 40)
        self.btn_color = (80, 80, 80)
        self.btn_hover = (120, 120, 120)
        self.accent_color = (180, 120, 60)

        self.max_distance = SETTINGS.max_distance_travelled
        self.color_blind_enabled = SETTINGS.color_blind_mode

        # Rects/text are authored visually with the uicreator tool and saved
        # to data/ui/main_menu.json; the hardcoded rects below are only a
        # fallback in case that file is missing.
        self.layout = load_layout("main_menu")

        play_rect = self.layout.rect("btn_play", pygame.Rect(120, 220, 220, 54))
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
        exit_rect = self.layout.rect("btn_exit", pygame.Rect(120, 300, 220, 54))
        self.btn_exit = UIButton(
            exit_rect.x,
            exit_rect.y,
            exit_rect.width,
            exit_rect.height,
            self.layout.get("btn_exit", "text", "X Exit Game"),
            self.font_large,
            self.btn_color,
            (200, 50, 50),
        )
        self.panel_rect = self.layout.rect("panel_settings", pygame.Rect(self.width - 280, 180, 220, 260))

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
                return None

            self._handle_slider_click(event.pos)

        if event.type == pygame.MOUSEMOTION and event.buttons[0]:
            self._handle_slider_drag(event.pos)

        return None

    def draw(self, surface):
        surface.fill((8, 12, 20))

        title_surf = self.font_title.render("The Twilight Zone", True, self.text_color)
        title_rect = title_surf.get_rect(center=(self.width // 2, 90))
        surface.blit(title_surf, title_rect)

        pygame.draw.circle(surface, self.text_color, (self.width // 2, 180), 70, 2)
        pygame.draw.circle(surface, self.text_color, (self.width // 2, 180), 45, 1)

        distance_label = self.font_medium.render("Max Distance", True, self.text_color)
        distance_value = self.font_large.render(f"{self.max_distance} m", True, self.accent_color)
        surface.blit(distance_label, (120, 170))
        surface.blit(distance_value, (120, 205))

        self.btn_play.draw(surface)
        self.btn_exit.draw(surface)

        panel_rect = self.panel_rect
        pygame.draw.rect(surface, self.panel_color, panel_rect, border_radius=10)
        pygame.draw.rect(surface, (255, 255, 255), panel_rect, 2, border_radius=10)

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
                return

    def _handle_slider_drag(self, pos):
        self._handle_slider_click(pos)

    def _draw_volume_slider(self, surface, x, y, label, percent):
        label_surf = self.font_small.render(label, True, self.text_color)
        surface.blit(label_surf, (x, y))

        bar_rect = pygame.Rect(x, y + 22, 150, 8)
        pygame.draw.rect(surface, (70, 70, 70), bar_rect, border_radius=4)
        fill_width = int(150 * (percent / 100))
        pygame.draw.rect(surface, self.accent_color, pygame.Rect(x, y + 22, fill_width, 8), border_radius=4)
        percent_surf = self.font_small.render(f"{percent}%", True, self.text_color)
        surface.blit(percent_surf, (x + 165, y - 2))


class EndlessRunConfirmation:
    """A confirmation overlay for starting an endless run."""

    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height
        self.font_large = pygame.font.Font(None, 64)
        self.font_medium = pygame.font.Font(None, 36)

        self.text_color = (255, 255, 255)
        self.btn_color = (80, 80, 80)
        self.btn_hover = (120, 120, 120)

        btn_w, btn_h = 140, 50
        center_x = self.width // 2 - btn_w // 2

        self.btn_yes = UIButton(
            center_x - 90,
            270,
            btn_w,
            btn_h,
            "Yes",
            self.font_medium,
            self.btn_color,
            (50, 200, 50),
        )
        self.btn_no = UIButton(
            center_x + 50,
            270,
            btn_w,
            btn_h,
            "No",
            self.font_medium,
            self.btn_color,
            (200, 50, 50),
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
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        prompt_surf = self.font_large.render("Do you want to start an endless run?", True, self.text_color)
        prompt_rect = prompt_surf.get_rect(center=(self.width // 2, 150))
        surface.blit(prompt_surf, prompt_rect)

        self.btn_yes.draw(surface)
        self.btn_no.draw(surface)


class PauseMenu:
    """A lightweight pause overlay with resume and quit confirmation actions."""

    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height
        self.font_large = pygame.font.Font(None, 64)
        self.font_medium = pygame.font.Font(None, 36)

        self.confirming_quit = False

        self.bg_color = (40, 40, 40)
        self.btn_color = (80, 80, 80)
        self.btn_hover = (120, 120, 120)
        self.text_color = (255, 255, 255)

        btn_w, btn_h = 200, 50
        center_x = self.width // 2 - btn_w // 2

        self.btn_resume = UIButton(
            center_x,
            200,
            btn_w,
            btn_h,
            "Resume",
            self.font_medium,
            self.btn_color,
            self.btn_hover,
        )
        self.btn_quit = UIButton(
            center_x,
            270,
            btn_w,
            btn_h,
            "Quit to Menu",
            self.font_medium,
            self.btn_color,
            (200, 50, 50),
        )

        self.btn_yes = UIButton(
            center_x - 110,
            270,
            100,
            50,
            "Yes",
            self.font_medium,
            self.btn_color,
            (50, 200, 50),
        )
        self.btn_no = UIButton(
            center_x + 10,
            270,
            100,
            50,
            "No",
            self.font_medium,
            self.btn_color,
            (200, 50, 50),
        )

    def handle_events(self, event, mouse_pos):
        if not self.confirming_quit:
            self.btn_resume.check_hover(mouse_pos)
            self.btn_quit.check_hover(mouse_pos)
        else:
            self.btn_yes.check_hover(mouse_pos)
            self.btn_no.check_hover(mouse_pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.confirming_quit:
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

    def draw(self, surface):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        if not self.confirming_quit:
            title_surf = self.font_large.render("PAUSED", True, self.text_color)
            title_rect = title_surf.get_rect(center=(self.width // 2, 120))
            surface.blit(title_surf, title_rect)

            self.btn_resume.draw(surface)
            self.btn_quit.draw(surface)
        else:
            prompt_surf = self.font_large.render("Are you sure?", True, self.text_color)
            prompt_rect = prompt_surf.get_rect(center=(self.width // 2, 150))
            surface.blit(prompt_surf, prompt_rect)

            self.btn_yes.draw(surface)
            self.btn_no.draw(surface)

        self._draw_inventory_placeholders(surface)

    def _draw_inventory_placeholders(self, surface):
        slot_radius = 30
        spacing = 20
        total_width = (slot_radius * 2 * 5) + (spacing * 4)
        start_x = (self.width // 2) - (total_width // 2) + slot_radius
        start_y = self.height - 100

        for index in range(5):
            x = start_x + (index * (slot_radius * 2 + spacing))
            pygame.draw.circle(surface, (200, 200, 200), (x, start_y), slot_radius, 3)
            pygame.draw.circle(surface, (50, 50, 50), (x, start_y), slot_radius - 3)
