"""
mouse.py
--------
Mouse: a pygame.sprite.Sprite that represents one Mouse player.
Sends Move requests to the Gameboard and renders on the top layer.
"""

import pygame
from button import HexagonButton

# Colour assigned to each mouse index (up to 4)
MOUSE_COLORS = [
    (126, 200, 227),   # 0 – sky blue
    (255, 200,  80),   # 1 – gold
    (180, 130, 220),   # 2 – lavender
    (100, 220, 160),   # 3 – mint
]

MOUSE_RADIUS = 10   # drawn circle radius in pixels


class Mouse(pygame.sprite.Sprite):
    """
    Represents one Mouse player token on the board.

    Parameters
    ----------
    player_index : int   0-based index among mice (0..3)
    col, row     : int   Starting grid position
    gameboard    : Gameboard   Reference for move validation
    """

    def __init__(self, player_index: int, col: int, row: int, gameboard):
        super().__init__()
        self.player_index = player_index
        self.col          = col
        self.row          = row
        self.gameboard    = gameboard
        self.color        = MOUSE_COLORS[player_index % len(MOUSE_COLORS)]
        self.escaped      = False   # True once the mouse reaches an edge cell
        self.trapped      = False   # True if the trapper has blocked all paths to edge cells

        # Create a small surface for the sprite
        size = MOUSE_RADIUS * 2 + 4
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self._render_image()

        # rect is used by the sprite group for blitting
        self.rect = self.image.get_rect()
        self._sync_rect()

    # ── Rendering ────────────────────────────────────────────────────────────

    def _render_image(self):
        """Draw a filled circle with a dark outline onto self.image."""
        self.image.fill((0, 0, 0, 0))
        cx = cy = self.image.get_width() // 2
        pygame.draw.circle(self.image, (20, 20, 20), (cx, cy), MOUSE_RADIUS + 1)
        pygame.draw.circle(self.image, self.color,   (cx, cy), MOUSE_RADIUS)
        # Small ear bumps to look mouse-like
        ear_r = MOUSE_RADIUS // 3
        pygame.draw.circle(self.image, self.color, (cx - MOUSE_RADIUS + 2, cy - MOUSE_RADIUS + 2), ear_r)
        pygame.draw.circle(self.image, self.color, (cx + MOUSE_RADIUS - 2, cy - MOUSE_RADIUS + 2), ear_r)

    def _sync_rect(self):
        """Keep self.rect centred on the hexagon's pixel position."""
        hex_cell: HexagonButton = self.gameboard.get_cell(self.col, self.row)
        if hex_cell:
            self.rect.center = (int(hex_cell.cx), int(hex_cell.cy))

    # ── Path scanning ─────────────────────────────────────────────────────────

    def has_escape_path(self) -> bool:
        """
        Scan the board before this mouse's turn.
        Returns True if there is still at least one active path to any edge cell.
        Called by PlayScreen at the start of each Mouse turn to check if the
        Trapper has already won.
        """
        return self.gameboard._has_path_to_edge(self.col, self.row)

    # ── Movement ─────────────────────────────────────────────────────────────

    def try_move(self, target_col: int, target_row: int) -> bool:
        """
        Attempt to move to (target_col, target_row).
        The Gameboard validates adjacency and active status.
        Returns True if the move succeeded.
        """
        success = self.gameboard.request_move(self, target_col, target_row)
        if success:
            self.col = target_col
            self.row = target_row
            self._sync_rect()
            # Check escape condition
            cell = self.gameboard.get_cell(self.col, self.row)
            if cell and cell.is_edge:
                self.escaped = True
        return success

    # ── Update (called each frame by sprite group) ───────────────────────────

    def update(self):
        """Re-sync position each frame (handles board rescaling if needed)."""
        self._sync_rect()

    