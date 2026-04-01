"""
pause.py
--------
PauseScreen: draws the pause overlay on top of the frozen board.

Does NOT own or re-render the board — it receives a pre-rendered snapshot
surface to display underneath the dim overlay, keeping it decoupled from
PlayScreen internals.
"""

import pygame

from ui_shared import (
    C_PANEL, C_ACCENT, C_DIM, C_GREEN, C_RED, C_ACCENT2,
    STATE_PLAY, STATE_MENU,
    make_font, draw_button,
)

SIGNAL_RESTART = "SIGNAL_RESTART"  # go back to setup screen


class PauseScreen:
    """
    Self-contained Pause overlay screen.

    Usage
    -----
    screen_obj = PauseScreen(pygame_surface)
    # pass the already-rendered board frame as background:
    next = screen_obj.handle_event(event)
    screen_obj.draw(board_snapshot)
    """

    def __init__(self, surface: pygame.Surface):
        self.surface = surface

        # Fonts
        self.font_large = make_font(32, bold=True)
        self.font_small = make_font(16)

        # Button rects rebuilt each draw()
        self._btns: dict[str, pygame.Rect] = {}

    # ── Public interface ──────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """
        Returns:
          STATE_PLAY      – Resume clicked (or ESC handled by GameManager)
          STATE_MENU      – Main Menu clicked
          SIGNAL_RESTART  – Restart clicked (back to setup)
          "QUIT_APP"      – Quit Game clicked (GameManager calls sys.exit)
          None            – no transition
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
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
        """
        Render the pause overlay.

        Parameters
        ----------
        board_snapshot : Surface | None
            A pre-rendered image of the game board to show dimmed behind the
            pause panel.  If None, just fills with black.
        """
        w, h = self.surface.get_size()

        # Show frozen board underneath
        if board_snapshot:
            self.surface.blit(board_snapshot, (0, 0))
        else:
            self.surface.fill((0, 0, 0))

        # Dark overlay
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.surface.blit(overlay, (0, 0))

        # ── Layout constants ──────────────────────────────────────────────────
        # 2x2 grid:  [RESTART]  [RESUME ]
        #            [MENU    ]  [QUIT   ]
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

        # Draw panel
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(self.surface, C_PANEL, panel_rect, border_radius=12)
        pygame.draw.rect(self.surface, C_ACCENT, panel_rect, 2, border_radius=12)

        # Title + hint
        pause_surf = self.font_large.render("⏸  PAUSED", True, C_ACCENT)
        self.surface.blit(pause_surf,
                          pause_surf.get_rect(center=(w // 2, panel_y + 30)))
        hint = self.font_small.render("Press ESC to resume", True, C_DIM)
        self.surface.blit(hint, hint.get_rect(center=(w // 2, panel_y + 62)))

        # Grid positions: top-left, top-right, bottom-left, bottom-right
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

        self._btns.clear()
        for key, label, color, bx, by in grid_btns:
            self._btns[key] = draw_button(
                self.surface, label, bx, by,
                color, C_PANEL, self.font_large,
                width=btn_w,
            )