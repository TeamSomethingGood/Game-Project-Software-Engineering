"""
gameboard.py
------------
Gameboard: owns the 32×16 hexagonal grid and acts as the intermediary
for all player actions (wall placement, movement validation, win detection).
"""

import math
from collections import deque
from button import HexagonButton

COLS = 32
ROWS = 16


def _hex_layout(cols: int, rows: int, screen_w: int, screen_h: int):
    """
    Compute pixel centres for a flat-top offset hex grid that fills
    (screen_w × screen_h) with a small margin.

    Flat-top hex geometry:
        hex_w = 2 * r
        hex_h = sqrt(3) * r
        col spacing = hex_w * 0.75          (horizontal step)
        row spacing = hex_h                 (vertical step)
        odd columns are offset by hex_h / 2 downward
    """
    margin_x = 10
    margin_y = 10
    usable_w = screen_w - 2 * margin_x
    usable_h = screen_h - 2 * margin_y

    # Solve for r:
    #   col_step = 2r * 0.75  → total width  = margin + (cols-1)*col_step + 2r
    #   row_step = sqrt(3)*r  → total height = margin + (rows-1)*row_step + sqrt(3)*r
    r_from_w = usable_w  / (1.5 * cols + 0.5)
    r_from_h = usable_h  / (math.sqrt(3) * (rows + 0.5))
    r = min(r_from_w, r_from_h)

    col_step = r * 1.5
    row_step = r * math.sqrt(3)

    # Re-centre after choosing r
    total_w = col_step * (cols - 1) + 2 * r
    total_h = row_step * (rows - 1) + row_step
    ox = margin_x + (usable_w - total_w) / 2 + r
    oy = margin_y + (usable_h - total_h) / 2 + row_step / 2

    centres = {}
    for c in range(cols):
        for rr in range(rows):
            cx = ox + c * col_step
            cy = oy + rr * row_step + (row_step / 2 if c % 2 == 1 else 0)
            centres[(c, rr)] = (cx, cy)
    return centres, r


class Gameboard:
    """
    Owns and manages the 32×16 hex grid.

    Parameters
    ----------
    screen_w, screen_h : int   Pixel dimensions of the game area canvas.
    """

    def __init__(self, screen_w: int, screen_h: int):
        self.cols      = COLS
        self.rows      = ROWS
        self.screen_w  = screen_w
        self.screen_h  = screen_h
        self._cells: dict[tuple[int, int], HexagonButton] = {}
        self._build_grid()

    # ── Grid construction ────────────────────────────────────────────────────

    def _build_grid(self):
        centres, radius = _hex_layout(self.cols, self.rows,
                                      self.screen_w, self.screen_h)
        self.hex_radius = radius
        for (c, r), (cx, cy) in centres.items():
            btn = HexagonButton(c, r, cx, cy, radius)
            btn.is_edge = (c == 0 or c == self.cols - 1 or
                           r == 0 or r == self.rows - 1)
            self._cells[(c, r)] = btn

    def rebuild(self, screen_w: int, screen_h: int):
        """Re-compute layout after a window resize (preserves active state)."""
        states = {pos: cell.active for pos, cell in self._cells.items()}
        self.screen_w = screen_w
        self.screen_h = screen_h
        self._build_grid()
        for pos, active in states.items():
            if pos in self._cells:
                self._cells[pos].active = active

    # ── Accessors ────────────────────────────────────────────────────────────

    def get_cell(self, col: int, row: int) -> HexagonButton | None:
        return self._cells.get((col, row))

    def cell_at_pixel(self, mx: float, my: float) -> HexagonButton | None:
        """Return the HexagonButton whose radial region contains (mx, my)."""
        best      = None
        best_dist = float('inf')
        # Only check cells near the click to stay fast
        for cell in self._cells.values():
            d = math.hypot(mx - cell.cx, my - cell.cy)
            if d < best_dist:
                best_dist = d
                best      = cell
        # Confirm it truly contains the point
        if best and best.contains_point(mx, my):
            return best
        return None

    # ── Hex neighbour logic (flat-top offset grid) ───────────────────────────

    def neighbours(self, col: int, row: int) -> list[tuple[int, int]]:
        """
        Return valid grid coordinates of the 6 flat-top hex neighbours.
        Uses the standard offset-grid neighbour formula.
        """
        if col % 2 == 0:   # even column
            dirs = [(+1, 0), (+1, -1), (0, -1), (-1, -1), (-1, 0), (0, +1)]
        else:               # odd column
            dirs = [(+1, +1), (+1, 0), (0, -1), (-1, 0), (-1, +1), (0, +1)]
        result = []
        for dc, dr in dirs:
            nc, nr = col + dc, row + dr
            if (nc, nr) in self._cells:
                result.append((nc, nr))
        return result

    # ── Player actions ───────────────────────────────────────────────────────

    def request_wall(self, col: int, row: int,
                     mouse_positions: list[tuple[int, int]]) -> bool:
        """
        Trapper places a wall on (col, row).
        Refuses if:
          • cell is already inactive
          • cell is occupied by a Mouse
          • cell is an edge cell
        The Trapper IS allowed to place a wall that fully blocks all mice —
        that is the winning move. Win detection is handled by the caller.
        Returns True on success.
        """
        cell = self.get_cell(col, row)
        if cell is None or not cell.active or cell.is_edge:
            return False
        if (col, row) in mouse_positions:
            return False

        cell.active = False
        return True

    def request_move(self, mouse, target_col: int, target_row: int) -> bool:
        """
        Mouse requests to move from its current cell to (target_col, target_row).
        Only allowed if the target is an active neighbour.
        """
        if (target_col, target_row) not in self.neighbours(mouse.col, mouse.row):
            return False
        target = self.get_cell(target_col, target_row)
        if target is None or not target.active:
            return False
        return True

    # ── Win detection ────────────────────────────────────────────────────────

    def _has_path_to_edge(self, start_col: int, start_row: int) -> bool:
        """BFS from (start_col, start_row) to any active edge cell."""
        start_cell = self.get_cell(start_col, start_row)
        if start_cell is None or not start_cell.active:
            return False
        if start_cell.is_edge:
            return True

        visited = {(start_col, start_row)}
        queue   = deque([(start_col, start_row)])
        while queue:
            c, r = queue.popleft()
            for nc, nr in self.neighbours(c, r):
                if (nc, nr) in visited:
                    continue
                nb = self.get_cell(nc, nr)
                if nb is None or not nb.active:
                    continue
                if nb.is_edge:
                    return True
                visited.add((nc, nr))
                queue.append((nc, nr))
        return False

    # ── Rendering ────────────────────────────────────────────────────────────

    def draw(self, surface, highlighted: set[tuple[int, int]] | None = None):
        """
        Draw the full grid.
        highlighted: set of (col, row) to mark as hover (adjacent move targets).
        """
        for (c, r), cell in self._cells.items():
            cell.hovered = highlighted is not None and (c, r) in highlighted
            cell.draw(surface)

    def get_active_neighbours(self, col: int, row: int) -> list[tuple[int, int]]:
        """Return active neighbour coordinates (for movement highlighting)."""
        return [(c, r) for c, r in self.neighbours(col, row)
                if self._cells[(c, r)].active]
