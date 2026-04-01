"""
play.py
-------
PlayScreen: draws and handles all input for the Active Gameplay state.

Owns:
  • HUD bar (turn indicator, mouse status chips, Pause + Quit buttons)
  • Gameboard rendering
  • Sprite rendering (mice tokens on top layer)
  • Active player highlight ring
  • All click routing for Mouse moves and Trapper wall placement

Returns the next state string (or special signals) to GameManager.
"""

import pygame

from ui_shared import (
    C_BG, C_PANEL, C_ACCENT, C_ACCENT2,
    C_MOUSE_HUD, C_RED,
    STATE_MENU, STATE_PAUSED,
    TURN_MOUSE, TURN_TRAPPER,
    BOARD_TOP,
    make_font, draw_button,
)

# Special signals returned to GameManager
SIGNAL_MOUSE_WIN   = "SIGNAL_MOUSE_WIN"
SIGNAL_TRAPPER_WIN = "SIGNAL_TRAPPER_WIN"


class PlayScreen:
    """
    Self-contained Active Gameplay screen.

    GameManager passes in the live gameboard, mice list, trapper, and
    turn_manager references so this screen can read and mutate game state.

    Usage
    -----
    screen_obj = PlayScreen(surface, gameboard, mice, trapper, turn_mgr)
    next = screen_obj.handle_event(event)
    screen_obj.draw()
    """

    def __init__(self, surface: pygame.Surface,
                 gameboard, mice: list, trapper, turn_mgr):
        self.surface    = surface
        self.gameboard  = gameboard
        self.mice       = mice
        self.trapper    = trapper
        self.turn_mgr   = turn_mgr
        self.highlighted: set[tuple[int, int]] = set()

        # Sprite group for mouse tokens
        self.sprite_group = pygame.sprite.Group()
        for m in self.mice:
            self.sprite_group.add(m)

        # Fonts
        self.font_med   = make_font(22)
        self.font_small = make_font(16)

        # HUD button rects rebuilt each draw()
        self._btns: dict[str, pygame.Rect] = {}

        self.refresh_highlights()

    # ── Public interface ──────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """
        Returns:
          STATE_PAUSED        – Pause button clicked
          STATE_MENU          – Quit button clicked
          SIGNAL_MOUSE_WIN    – a mouse reached the edge
          SIGNAL_TRAPPER_WIN  – all paths blocked
          None                – no transition
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # HUD buttons take priority
            if "pause" in self._btns and self._btns["pause"].collidepoint(mx, my):
                return STATE_PAUSED
            if "quit" in self._btns and self._btns["quit"].collidepoint(mx, my):
                return STATE_MENU

            # Board click (offset into board-local coordinates)
            bx, by = mx, my - BOARD_TOP
            cell = self.gameboard.cell_at_pixel(bx, by)
            if cell is None:
                return None

            state, idx = self.turn_mgr.current()

            if state == TURN_MOUSE:
                result = self._handle_mouse_click(cell, idx)
                if result:
                    return result

            elif state == TURN_TRAPPER:
                result = self._handle_trapper_click(cell)
                if result:
                    return result

        return None

    def refresh_highlights(self):
        """Recompute which hexes should glow for the current player's turn."""
        self.highlighted = set()
        state, idx = self.turn_mgr.current()
        if state == TURN_MOUSE and idx < len(self.mice):
            m = self.mice[idx]
            self.highlighted = set(
                self.gameboard.get_active_neighbours(m.col, m.row)
            )

    def draw(self):
        """Render the full play screen onto self.surface."""
        w, h = self.surface.get_size()
        self.surface.fill(C_BG)
        self._draw_hud(w)
        self._draw_board(w, h)
        self._draw_sprites()
        self._draw_active_ring()

    # ── Private click handlers ────────────────────────────────────────────────

    def _handle_mouse_click(self, cell, idx: int) -> str | None:
        """
        Process a board click during a Mouse's turn.
        If this mouse has no escape path it is trapped — skip its turn.
        Only trigger Trapper win if ALL mice are trapped or escaped.
        """
        if idx >= len(self.mice):
            return None
        mouse = self.mice[idx]

        # If this mouse is trapped, skip its turn automatically
        if not mouse.has_escape_path():
            mouse.trapped = True
            self.turn_mgr.advance()
            self.refresh_highlights()
            # Now check if all mice are either escaped or trapped
            if all(m.escaped or m.trapped for m in self.mice):
                return SIGNAL_TRAPPER_WIN
            return None

        moved = mouse.try_move(cell.col, cell.row)
        if moved:
            if mouse.escaped:
                return SIGNAL_MOUSE_WIN + f":{idx}"
            self.turn_mgr.advance()
            self.refresh_highlights()
        return None

    def _handle_trapper_click(self, cell) -> str | None:
        """
        Process a board click during the Trapper's turn.
        Win only if ALL non-escaped mice are trapped.
        """
        occupied = [(m.col, m.row) for m in self.mice]
        placed   = self.trapper.try_place_wall(cell.col, cell.row, occupied)
        if placed:
            # Mark any newly trapped mice
            for mouse in self.mice:
                if not mouse.escaped and not mouse.has_escape_path():
                    mouse.trapped = True

            # Win only if every mouse is either escaped or trapped
            active_mice = [m for m in self.mice if not m.escaped]
            if all(m.trapped for m in active_mice):
                return SIGNAL_TRAPPER_WIN

            self.turn_mgr.advance()
            self.refresh_highlights()
        return None

    # ── Private drawing helpers ───────────────────────────────────────────────

    def _draw_hud(self, w: int):
        """Draw the top HUD bar: turn label, mouse chips, Pause/Quit buttons."""
        pygame.draw.rect(self.surface, C_PANEL, (0, 0, w, BOARD_TOP))
        pygame.draw.line(self.surface, C_ACCENT, (0, BOARD_TOP), (w, BOARD_TOP), 1)

        # Turn label (left)
        state, idx = self.turn_mgr.current()
        color     = C_MOUSE_HUD[idx] if state == TURN_MOUSE else C_ACCENT2
        turn_surf = self.font_med.render(self.turn_mgr.turn_label(), True, color)
        self.surface.blit(turn_surf,
                          (16, (BOARD_TOP - turn_surf.get_height()) // 2))

        # Mouse status chips (right side, before buttons)
        chip_x = w - 270
        for i, m in reversed(list(enumerate(self.mice))):
            if m.escaped:
                status = "ESCAPED"
            elif m.trapped:
                status = "TRAPPED"
            else:
                status = f"({m.col},{m.row})"
            chip_txt  = f"M{i+1}: {status}"
            chip_surf = self.font_small.render(chip_txt, True, C_MOUSE_HUD[i])
            chip_x   -= chip_surf.get_width() + 16
            self.surface.blit(chip_surf,
                              (chip_x, (BOARD_TOP - chip_surf.get_height()) // 2))

        # Pause + Quit buttons (far right)
        self._btns.clear()
        btn_cy     = BOARD_TOP // 2
        quit_rect  = draw_button(self.surface, "✕ QUIT",  w - 70,  btn_cy,
                                 C_RED,    C_PANEL, self.font_small)
        pause_rect = draw_button(self.surface, "⏸ PAUSE", w - 170, btn_cy,
                                 C_ACCENT, C_PANEL, self.font_small)
        self._btns["quit"]  = quit_rect
        self._btns["pause"] = pause_rect

    def _draw_board(self, w: int, h: int):
        """Render the hex grid onto the board sub-surface."""
        board_surface = self.surface.subsurface(
            pygame.Rect(0, BOARD_TOP, w, h - BOARD_TOP)
        )
        self.gameboard.draw(board_surface, self.highlighted)

    def _draw_sprites(self):
        """Blit all mouse sprites, offset by the HUD height."""
        for sprite in self.sprite_group:
            sprite.update()
            self.surface.blit(sprite.image,
                              (sprite.rect.x, sprite.rect.y + BOARD_TOP))

    def _draw_active_ring(self):
        """Draw a coloured outline around the currently active mouse token."""
        state, idx = self.turn_mgr.current()
        if state == TURN_MOUSE and idx < len(self.mice):
            m    = self.mice[idx]
            cell = self.gameboard.get_cell(m.col, m.row)
            if cell:
                pts = [(int(x), int(y + BOARD_TOP)) for x, y in cell.vertices]
                pygame.draw.polygon(self.surface, C_MOUSE_HUD[idx], pts, 3)