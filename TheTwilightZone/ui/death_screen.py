"""Death screen template — matches the wireframe's post-run summary.

Shows whether the run ended in a new high score, the cause of death,
distance travelled, and a restart/main-menu prompt. Rects/text come
from `data/ui/death_screen.json`, editable with the `uicreator` tool.
"""

from __future__ import annotations

import pygame

from ui.layout import load_layout
from ui.menus import UIButton


class DeathScreen:
    """Post-run summary screen with a restart confirmation prompt."""

    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height
        self.layout = load_layout("death_screen")

        self.font_title = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 26)

        self.text_color = (255, 255, 255)
        self.panel_color = (40, 40, 40)
        self.btn_color = (80, 80, 80)

        self.distance = 0
        self.cause_of_death = "Unknown"
        self.is_new_high_score = False

        yes_rect = self.layout.rect("btn_yes", pygame.Rect(352, 340, 100, 46))
        self.btn_restart = UIButton(
            yes_rect.x, yes_rect.y, yes_rect.width, yes_rect.height,
            self.layout.get("btn_yes", "text", "Yes"), self.font_medium, self.btn_color, (50, 200, 50),
        )
        no_rect = self.layout.rect("btn_no", pygame.Rect(472, 340, 100, 46))
        self.btn_menu = UIButton(
            no_rect.x, no_rect.y, no_rect.width, no_rect.height,
            self.layout.get("btn_no", "text", "No"), self.font_medium, self.btn_color, (200, 50, 50),
        )

    def set_result(self, distance: float, cause_of_death: str, is_new_high_score: bool = False) -> None:
        self.distance = int(distance)
        self.cause_of_death = cause_of_death
        self.is_new_high_score = is_new_high_score

    def handle_events(self, event, mouse_pos):
        self.btn_restart.check_hover(mouse_pos)
        self.btn_menu.check_hover(mouse_pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_restart.handle_event(event):
                return "RESTART"
            if self.btn_menu.handle_event(event):
                return "MAIN_MENU"

        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((8, 12, 20))

        panel_rect = self.layout.rect("panel", pygame.Rect(332, 220, 360, 330))
        pygame.draw.rect(surface, self.panel_color, panel_rect, border_radius=10)
        pygame.draw.rect(surface, (255, 255, 255), panel_rect, 2, border_radius=10)

        title_text = "New High Score!" if self.is_new_high_score else "You Died"
        title_surf = self.font_title.render(title_text, True, self.text_color)
        title_rect_widget = self.layout.rect("title", pygame.Rect(352, 240, 320, 40))
        surface.blit(title_surf, title_surf.get_rect(center=title_rect_widget.center))

        prompt_widget = self.layout.rect("prompt", pygame.Rect(352, 290, 320, 40))
        prompt_surf = self.font_medium.render("Would you like to Restart?", True, self.text_color)
        surface.blit(prompt_surf, prompt_surf.get_rect(center=prompt_widget.center))

        self.btn_restart.draw(surface)
        self.btn_menu.draw(surface)

        cause_widget = self.layout.rect("cause_of_death", pygame.Rect(352, 410, 320, 30))
        cause_surf = self.font_small.render(f"Cause of Death: {self.cause_of_death}", True, self.text_color)
        surface.blit(cause_surf, cause_surf.get_rect(center=cause_widget.center))

        distance_widget = self.layout.rect("distance_travelled", pygame.Rect(352, 450, 320, 30))
        distance_surf = self.font_small.render(f"Distance Travelled: {self.distance} m", True, self.text_color)
        surface.blit(distance_surf, distance_surf.get_rect(center=distance_widget.center))
