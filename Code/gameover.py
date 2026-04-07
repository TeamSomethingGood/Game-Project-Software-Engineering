# gameover.py
# -----------
# GameOverScreen: draws and handles input for the Game Over state.
# Displays the winner message and offers Play Again / Main Menu options.

import sys
import pygame

from ui_shared import (
    C_BG, C_ACCENT, C_TEXT, C_DIM, C_GREEN, C_RED, 
    STATE_MENU,
    make_font, draw_button, draw_bg_grid,
)

# Signal to GameManager to restart with same settings
SIGNAL_PLAY_AGAIN = "SIGNAL_PLAY_AGAIN"


class GameOverScreen:
    # Self-contained Game Over screen.
    # Usage
    # -----
    # screen_obj = GameOverScreen(pygame_surface)
    # screen_obj.set_message("Mouse 1 escaped! Mice Win!")
    # next = screen_obj.handle_event(event)   # STATE_MENU | SIGNAL_PLAY_AGAIN
    # screen_obj.draw()
    
    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self.message = ""

        # Fonts
        self.font_title = make_font(64, bold=True)
        self.font_large = make_font(32, bold=True)

        # Button rects rebuilt each draw()
        self._btns: dict[str, pygame.Rect] = {}

    # ── Public interface ──────────────────────────────────────────────────────

    def set_message(self, msg: str):
        # Set the winner/outcome message shown on this screen.
        self.message = msg

    def handle_event(self, event: pygame.event.Event) -> str | None:
        # Processes clicks on the Game Over buttons and returns the corresponding
        # state transition signal to GameManager.
        # Returns:
        #   SIGNAL_PLAY_AGAIN  – Play Again clicked
        #   STATE_MENU         – Main Menu clicked
        #   None               – no transition
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # collidepoint is used here to check the mouse position against
            # the rects we generated during the last draw() call.
            if "again" in self._btns and self._btns["again"].collidepoint(event.pos):
                return SIGNAL_PLAY_AGAIN
            if "menu"  in self._btns and self._btns["menu"].collidepoint(event.pos):
                return STATE_MENU
            if "quit"  in self._btns and self._btns["quit"].collidepoint(event.pos):
                pygame.quit()
                sys.exit()
        return None

    def draw(self):
        # Render the full game over screen onto self.surface.
        w, h = self.surface.get_size()
        self.surface.fill(C_BG)
        draw_bg_grid(self.surface, w, h)

        # Dim overlay for atmosphere
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.surface.blit(overlay, (0, 0))

        # "GAME OVER" title
        title_surf = self.font_title.render("GAME OVER", True, C_ACCENT)
        self.surface.blit(title_surf,
                          title_surf.get_rect(center=(w // 2, h // 3)))

        # Winner message
        msg_surf = self.font_large.render(self.message, True, C_TEXT)
        self.surface.blit(msg_surf,
                          msg_surf.get_rect(center=(w // 2, h // 2)))

        # 3 horizontal buttons
        self._btns.clear()
        btn_labels = [
            ("menu",  "⌂ MENU",       C_DIM),
            ("again", "▶ PLAY AGAIN", C_GREEN),
            ("quit",  "✕ QUIT",       C_RED),
        ]

        # 1. Determine Layout Constraints:
        # 'row_y' places the button row at 62.5% of the screen height (lower third).
        num_btns = len(btn_labels)
        row_y    = h * 5 // 8
        gap     = 250          # Horizontal distance between button centers.

        # 2. Calculate the 'Anchor' point:
        # We find the center of the screen (w // 2) and offset it to the left 
        # by half the total width occupied by the button gaps.
        start_x = w // 2 - gap * (num_btns - 1) // 2

        # 3. Component Generation:
        # Iterate through labels to draw buttons and cache their Rects.
        # Storing the Rects in self._btns enables O(1) collision detection in handle_event().
        for i, (key, label, color) in enumerate(btn_labels):
            # bx calculates the specific x-coordinate for the i-th button center.
            bx = start_x + gap * i

            self._btns[key] = draw_button(
                self.surface, label, bx, row_y,
                color, C_BG, self.font_large,
            )
