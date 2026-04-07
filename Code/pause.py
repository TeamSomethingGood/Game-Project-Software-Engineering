# pause.py
# --------
# PauseScreen: draws the pause overlay on top of the frozen board.
# By drawing over a static surface (board_snapshot) instead of the 
# live game state, we prevent logic leaks and save GPU/CPU resources.
# Does NOT own or re-render the board — it receives a pre-rendered snapshot
# surface to display underneath the dim overlay, keeping it decoupled from
# PlayScreen internals.

import pygame

from ui_shared import (
    C_PANEL, C_ACCENT, C_DIM, C_GREEN, C_RED, C_ACCENT2,
    STATE_PLAY, STATE_MENU,
    make_font, draw_button,
)

SIGNAL_RESTART = "SIGNAL_RESTART"  # go back to setup screen

class PauseScreen:
    # Self-contained Pause overlay screen.
    # Usage
    # -----
    # screen_obj = PauseScreen(pygame_surface)
    # pass the already-rendered board frame as background:
    # next = screen_obj.handle_event(event)
    # screen_obj.draw(board_snapshot)

    def __init__(self, surface: pygame.Surface):
        self.surface = surface

        # Fonts
        self.font_large = make_font(32, bold=True)
        self.font_small = make_font(16)

        # Spatial Awareness: Using a dictionary to map logical actions 
        # to physical screen coordinates (Rects) for collision detection.
        self._btns: dict[str, pygame.Rect] = {}

    # ── Public interface ──────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> str | None:
        # Event Handling:
        # Listens for mouse clicks on the pause menu buttons and returns
        # the corresponding state transition signal to GameManager.
        # Returns:
        #   STATE_PLAY      – Resume clicked (or ESC handled by GameManager)
        #   STATE_MENU      – Main Menu clicked
        #   SIGNAL_RESTART  – Restart clicked (back to setup)
        #   "QUIT_APP"      – Quit Game clicked (GameManager calls sys.exit)
        #   None            – no transition
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # collidepoint is used here to check the mouse position against
            # the rects we generated during the last draw() call.
            if "resume"   in self._btns and self._btns["resume"].collidepoint(event.pos):
                return STATE_PLAY
            if "menu"     in self._btns and self._btns["menu"].collidepoint(event.pos):
                return STATE_MENU
            if "restart"  in self._btns and self._btns["restart"].collidepoint(event.pos):
                return SIGNAL_RESTART
            if "quit_app" in self._btns and self._btns["quit_app"].collidepoint(event.pos):
                return "QUIT_APP"
        return None

    def draw(self, board_snapshot: pygame.Surface | None = None):
        # Render the pause overlay.
        # Parameters
        # ----------
        # board_snapshot : Surface | None
        #     A pre-rendered image of the game board to show dimmed behind the
        #     pause panel.  If None, just fills with black.
        
        w, h = self.surface.get_size()

        # LAYER 1: The 'Frozen' World
        # We blit the pre-rendered snapshot. This is a massive optimization 
        # because we don't need to loop through 100+ hexagons while paused.
        if board_snapshot:
            self.surface.blit(board_snapshot, (0, 0))
        else:
            self.surface.fill((0, 0, 0))

        # LAYER 2: The Dimmer (Alpha Blending)
        # Using SRCALPHA to create a 'tint' effect, giving the user 
        # the psychological cue that the game is inactive.
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.surface.blit(overlay, (0, 0))

        # ── Layout constants ──────────────────────────────────────────────────
        # Building a 2x2 grid dynamically based on the current window size.
        btn_w     = 240
        btn_h     = self.font_large.get_height() + 24
        col_gap   = 20    # horizontal gap between buttons
        row_gap   = 16    # vertical gap between rows
        pad       = 40    # panel edge padding

        grid_w    = btn_w * 2 + col_gap
        grid_h    = btn_h * 2 + row_gap
        panel_w   = grid_w + pad * 2
        panel_h   = grid_h + 120   # room for title + hint above grid
        panel_x   = w // 2 - panel_w // 2
        panel_y   = h // 2 - panel_h // 2

        # LAYER 3: The Control Panel
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(self.surface, C_PANEL, panel_rect, border_radius=12)
        pygame.draw.rect(self.surface, C_ACCENT, panel_rect, 2, border_radius=12)

        # LAYER 4: Text Content (Center-Aligned)
        pause_surf = self.font_large.render("⏸  PAUSED", True, C_ACCENT)
        self.surface.blit(pause_surf,
                          pause_surf.get_rect(center=(w // 2, panel_y + 30)))
        hint = self.font_small.render("Press ESC to resume", True, C_DIM)
        self.surface.blit(hint, hint.get_rect(center=(w // 2, panel_y + 62)))

        # LAYER 5: The Button Grid
        # We calculate coordinates for a 4-button layout.
        grid_top  = panel_y + panel_h - grid_h - pad
        col_left  = panel_x + pad + btn_w // 2
        col_right = col_left + btn_w + col_gap
        row_top   = grid_top + btn_h // 2
        row_bot   = row_top + btn_h + row_gap

        grid_btns = [
            ("restart",  "↺ RESTART", C_ACCENT2, col_left,  row_top),
            ("resume",   "▶ RESUME",  C_GREEN,   col_right, row_top),
            ("menu",     "⌂ MENU",    C_DIM,     col_left,  row_bot),
            ("quit_app", "✕ QUIT",    C_RED,     col_right, row_bot),
        ]

        # Clearing and repopulating the Rect dictionary ensures that even 
        # if the window resizes, the click detection remains 100% accurate.
        self._btns.clear()
        for key, label, color, bx, by in grid_btns:
            self._btns[key] = draw_button(
                self.surface, label, bx, by,
                color, C_PANEL, self.font_large,
                width=btn_w,
            )
