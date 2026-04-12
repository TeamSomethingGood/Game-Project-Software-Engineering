# play.py
# -------
# PlayScreen: draws and handles all input for the Active Gameplay state.
# Owns:
#   • HUD bar (turn indicator, mouse status chips, Pause + Quit buttons)
#   • Gameboard rendering
#   • Sprite rendering (mice tokens on top layer)
#   • Active player highlight ring
#   • All click routing for Mouse moves and Trapper wall placement
# Returns the next state string (or special signals) to GameManager.

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
    # The Central Controller for active gameplay.
    # Manages the 'Play Loop' by coordinating between the Gameboard,
    # the Mouse sprites, and the Turn Manager.

    def __init__(self, surface: pygame.Surface,
                 gameboard, mice: list, trapper, turn_mgr):
        self.surface    = surface
        self.gameboard  = gameboard
        self.mice       = mice
        self.trapper    = trapper
        self.turn_mgr   = turn_mgr

        # Spatial Memory: Stores coordinates of hexes that should 'glow'
        # to guide the player's movement.
        self.highlighted: set[tuple[int, int]] = set()

        # Sprite Management: Using a Group allows for batch updates and
        # optimized 'blitting' (copying pixels to the screen).
        self.sprite_group = pygame.sprite.Group()
        for m in self.mice:
            self.sprite_group.add(m)

        # Fonts
        self.font_med   = make_font(22)
        self.font_small = make_font(16)

        # UI Cache: Rebuilt every frame to ensure buttons work after window resizes.
        self._btns: dict[str, pygame.Rect] = {}

        self.refresh_highlights()

    # ── Public interface ──────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> str | None:
        # The Master Event Router.
        # Decides if a click was a UI interaction (Pause/Quit) or a
        # gameplay interaction (Move/Wall).
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # 1. UI LAYER CHECK: HUD buttons take priority over the game world.
            if "pause" in self._btns and self._btns["pause"].collidepoint(mx, my):
                return STATE_PAUSED
            if "quit" in self._btns and self._btns["quit"].collidepoint(mx, my):
                return STATE_MENU

            # 2. COORDINATE TRANSLATION:
            # Converts raw mouse Y to board-local Y by subtracting the HUD height.
            bx, by = mx, my - BOARD_TOP

            # 3. SPATIAL QUERY: Ask the board which hex the user clicked.
            cell = self.gameboard.cell_at_pixel(bx, by)
            if cell is None:
                return None

            # 4. STATE-DRIVEN LOGIC: Route the click based on whose turn it is.
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
        # UX Polish: Calculates legal moves for the active player so
        # the UI can provide visual 'Affordance' (glow effect).
        self.highlighted = set()
        state, idx = self.turn_mgr.current()
        if state == TURN_MOUSE and idx < len(self.mice):
            m = self.mice[idx]
            self.highlighted = set(
                self.gameboard.get_active_neighbours(m.col, m.row)
            )

    def draw(self):
        # The Render Pipeline: Orders calls from back to front.
        w, h = self.surface.get_size()
        self.surface.fill(C_BG)
        self._draw_hud(w)           # Layer 0: Top Status Bar
        self._draw_board(w, h)      # Layer 1: Hex Grid
        self._draw_sprites()        # Layer 2: Mouse Tokens
        self._draw_active_ring()    # Layer 3: Active Player Highlight

    # ── Turn management ───────────────────────────────────────────────────────

    def _skip_trapped_mice(self) -> str | None:
        # After any turn advances, automatically skip forward past any mice
        # that are already trapped — no click required from the player.
        # When a trapped mouse is skipped, its paired Trapper turn is also
        # skipped since there's no point in the Trapper countering a turn
        # that never happened. Loops until a free mouse or a legitimate
        # trapper turn is found.
        # Returns SIGNAL_TRAPPER_WIN if all mice end up trapped.
        for _ in range(len(self.turn_mgr._sequence)):
            state, idx = self.turn_mgr.current()

            if state == TURN_MOUSE:
                mouse = self.mice[idx]

                # Mark trapped if not already.
                if not mouse.trapped and not mouse.has_escape_path():
                    mouse.trapped = True

                if mouse.trapped:
                    # Check win before skipping.
                    if all(m.escaped or m.trapped for m in self.mice):
                        return SIGNAL_TRAPPER_WIN
                    # Skip the mouse turn.
                    self.turn_mgr.advance()
                    # Also skip the paired trapper turn that follows.
                    self.turn_mgr.advance()
                    continue

                # Free mouse found — stop, it gets to play.
                break

            else:
                # It's the trapper's turn and we got here legitimately
                # (a real mouse played before this), so stop skipping.
                break

        self.refresh_highlights()
        return None

    # ── Private click handlers ────────────────────────────────────────────────

    def _handle_mouse_click(self, cell, idx: int) -> str | None:
        # Process a board click during a Mouse's turn.
        if idx >= len(self.mice):
            return None
        mouse = self.mice[idx]

        # Movement Validation: Check if the clicked cell is a legal move.
        moved = mouse.try_move(cell.col, cell.row)
        if moved:
            if mouse.escaped:
                # Signal includes the index so GameManager knows which mouse won.
                return SIGNAL_MOUSE_WIN + f":{idx}"
            self.turn_mgr.advance()
            # Auto-skip any trapped mice before the next turn starts.
            result = self._skip_trapped_mice()
            if result:
                return result
        return None

    def _handle_trapper_click(self, cell) -> str | None:
        # Processes logic for the Trapper's turn (wall placement).
        occupied = [(m.col, m.row) for m in self.mice]
        placed   = self.trapper.try_place_wall(cell.col, cell.row, occupied)
        if placed:
            # Re-check every mouse: did this new wall just trap someone?
            for mouse in self.mice:
                if not mouse.escaped and not mouse.has_escape_path():
                    mouse.trapped = True

            # Global Win Check: if all non-escaped mice are now trapped, Trapper wins.
            active_mice = [m for m in self.mice if not m.escaped]
            if all(m.trapped for m in active_mice):
                return SIGNAL_TRAPPER_WIN

            self.turn_mgr.advance()
            # Auto-skip any trapped mice before the next turn starts.
            result = self._skip_trapped_mice()
            if result:
                return result
        return None

    # ── Private drawing helpers ───────────────────────────────────────────────

    def _draw_hud(self, w: int):
        # Renders the dashboard: Turn info, player status, and UI buttons.
        pygame.draw.rect(self.surface, C_PANEL, (0, 0, w, BOARD_TOP))
        pygame.draw.line(self.surface, C_ACCENT, (0, BOARD_TOP), (w, BOARD_TOP), 1)

        # Turn Indicator: Changes color based on the current active player.
        state, idx = self.turn_mgr.current()
        color     = C_MOUSE_HUD[idx] if state == TURN_MOUSE else C_ACCENT2
        turn_surf = self.font_med.render(self.turn_mgr.turn_label(), True, color)
        self.surface.blit(turn_surf,
                          (16, (BOARD_TOP - turn_surf.get_height()) // 2))

        # Status Chips: Displays the status of each mouse on the board.
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

        # HUD Action Buttons: QUIT and PAUSE.
        self._btns.clear()
        btn_cy     = BOARD_TOP // 2
        pause_rect = draw_button(self.surface, "⏸ PAUSE", w - 170, btn_cy,
                                 C_ACCENT, C_PANEL, self.font_small)
        self._btns["pause"] = pause_rect

    def _draw_board(self, w: int, h: int):
        # Uses a Subsurface to clip board rendering so it doesn't bleed into the HUD.
        board_surface = self.surface.subsurface(
            pygame.Rect(0, BOARD_TOP, w, h - BOARD_TOP)
        )
        self.gameboard.draw(board_surface, self.highlighted)

    def _draw_sprites(self):
        # Batch rendering for all Mouse tokens, offset by the HUD height.
        for sprite in self.sprite_group:
            sprite.update()
            self.surface.blit(sprite.image,
                              (sprite.rect.x, sprite.rect.y + BOARD_TOP))

    def _draw_active_ring(self):
        # Visual Cue: Outlines the active mouse's hexagon to show focus.
        state, idx = self.turn_mgr.current()
        if state == TURN_MOUSE and idx < len(self.mice):
            m    = self.mice[idx]
            cell = self.gameboard.get_cell(m.col, m.row)
            if cell:
                # Map vertices from local board space to screen space.
                pts = [(int(x), int(y + BOARD_TOP)) for x, y in cell.vertices]
                pygame.draw.polygon(self.surface, C_MOUSE_HUD[idx], pts, 3)
