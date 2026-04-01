"""
setup.py
--------
SetupScreen: draws and handles input for the Game Setup / customisation state.

Lets the player choose how many mice (1-4) before starting.
Returns the next state or a special "START" signal to GameManager.
"""

import pygame

from ui_shared import (
    C_BG, C_ACCENT, C_ACCENT2, C_TEXT, C_DIM, C_MOUSE_HUD, C_GREEN,
    make_font, draw_button, draw_bg_grid,
)

# Special return value that tells GameManager to start a new game
SIGNAL_START = "SIGNAL_START"


class SetupScreen:
    """
    Self-contained Setup / Game Customisation screen.

    Usage
    -----
    screen_obj = SetupScreen(pygame_surface)
    screen_obj.num_mice = 2          # set/read the chosen mouse count
    next = screen_obj.handle_event(event)   # STATE_MENU | SIGNAL_START | None
    screen_obj.draw()
    """

    def __init__(self, surface: pygame.Surface):
        self.surface  = surface
        self.num_mice = 2   # default selection

        # Fonts
        self.font_large = make_font(32, bold=True)
        self.font_med   = make_font(22)
        self.font_small = make_font(16)

        # Button rects rebuilt each draw()
        self._btns: dict[str, pygame.Rect] = {}

    # ── Public interface ──────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """
        Returns:
          SIGNAL_START  – player clicked Start Game
          None          – no transition needed
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for key, rect in self._btns.items():
                if rect.collidepoint(event.pos):
                    if key.startswith("mice_"):
                        self.num_mice = int(key.split("_")[1])
                    elif key == "start":
                        return SIGNAL_START
        return None

    def draw(self):
        """Render the full setup screen onto self.surface."""
        w, h = self.surface.get_size()
        self.surface.fill(C_BG)
        draw_bg_grid(self.surface, w, h)
        self._btns.clear()

        # Title
        title = self.font_large.render("GAME SETUP", True, C_ACCENT)
        self.surface.blit(title, title.get_rect(center=(w // 2, h // 5)))

        # Mouse count label
        label = self.font_med.render("Number of Mouse Players:", True, C_TEXT)
        self.surface.blit(label, label.get_rect(center=(w // 2, h // 5 + 70)))

        # 1 / 2 / 3 / 4 selector buttons
        for i, n in enumerate([1, 2, 3, 4]):
            bx = w // 2 + (i - 1.5) * 110
            by = h // 5 + 130
            rect = draw_button(
                self.surface, str(n), int(bx), int(by),
                C_ACCENT if n == self.num_mice else C_DIM,
                C_BG, self.font_large, width=80,
            )
            self._btns[f"mice_{n}"] = rect

        # Role descriptions
        descriptions = [
            ("TRAPPER  (1 player)", C_ACCENT2,
             "Click active hexagons to deactivate them as walls."),
            ("MICE  (1-4 players)", C_MOUSE_HUD[0],
             "Move each turn to an adjacent active hexagon. Reach the edge to escape!"),
        ]
        for i, (heading, color, body) in enumerate(descriptions):
            hy = h // 2 + i * 110
            h_surf = self.font_med.render(heading, True, color)
            self.surface.blit(h_surf, h_surf.get_rect(center=(w // 2, hy)))
            b_surf = self.font_small.render(body, True, C_DIM)
            self.surface.blit(b_surf, b_surf.get_rect(center=(w // 2, hy + 30)))

        # Start button
        start_rect = draw_button(
            self.surface, "START GAME", w // 2, h * 4 // 5,
            C_GREEN, C_BG, self.font_large,
        )
        self._btns["start"] = start_rect

        
