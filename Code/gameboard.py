# gameboard.py
# ------------
# Gameboard: owns the 32×16 hexagonal grid and acts as the intermediary
# for all player actions (wall placement, movement validation, win detection).


import math
from collections import deque
from button import HexagonButton

COLS = 32
ROWS = 16


def _hex_layout(cols: int, rows: int, screen_w: int, screen_h: int):
# Compute pixel centres for a flat-top offset hex grid that fills
# (screen_w × screen_h) with a small margin.
# Flat-top hex geometry:
#     hex_w = 2 * r
#     hex_h = sqrt(3) * r
#     col spacing = hex_w * 0.75          (horizontal step)
#     row spacing = hex_h                 (vertical step)
#     odd columns are offset by hex_h / 2 downward
    
    # 1. Define Margins: Prevents hexagons from touching the screen edges.
    margin_x = 10
    margin_y = 10
    usable_w = screen_w - 2 * margin_x
    usable_h = screen_h - 2 * margin_y

    # 2. Solve for 'r' (Circumradius):
    # Width constraint: The first hex takes 2r, each subsequent hex adds 1.5r.
    # Total width = 2r + (cols - 1) * 1.5r => r * (1.5 * cols + 0.5)
    r_from_w = usable_w  / (1.5 * cols + 0.5)

    # Height constraint: Total height is (rows * hex_h) + the vertical offset (0.5 * hex_h).
    # hex_h = sqrt(3) * r.
    r_from_h = usable_h  / (math.sqrt(3) * (rows + 0.5))

    # Use the smaller radius to ensure the grid fits entirely within the screen.
    r = min(r_from_w, r_from_h)

    # 3. Define Layout Steps:
    col_step = r * 1.5
    row_step = r * math.sqrt(3)

    # 4. Calculate Centering Offsets:
    # total_w/h calculates the actual pixel footprint of the grid.
    total_w = col_step * (cols - 1) + 2 * r
    total_h = row_step * (rows - 1) + row_step # (includes the offset height)

    # Calculate starting 'origin' (ox, oy) to center the grid in the usable area.
    ox = margin_x + (usable_w - total_w) / 2 + r
    oy = margin_y + (usable_h - total_h) / 2 + row_step / 2

    # 5. Generate Centres:
    # Loop through each grid coordinate (col, row) and calculate the pixel centre (cx, cy).
    # Odd columns are offset vertically by row_step / 2.
    centres = {}
    for c in range(cols):
        for rr in range(rows):
            cx = ox + c * col_step
            cy = oy + rr * row_step + (row_step / 2 if c % 2 == 1 else 0)
            centres[(c, rr)] = (cx, cy)
    return centres, r


class Gameboard:
    # Owns and manages the 32×16 hex grid.
    # Parameters
    # ----------
    # screen_w, screen_h : int   Pixel dimensions of the game area canvas.
    
    def __init__(self, screen_w: int, screen_h: int):
        # 1. State Initialization:
        # These constants (COLS/ROWS) likely define the 32x16 grid size.
        self.cols      = COLS
        self.rows      = ROWS
        self.screen_w  = screen_w
        self.screen_h  = screen_h

        # 2. Grid Storage:
        # A dictionary is used for 'Spatial Hashing'. It maps logical grid 
        # coordinates (tuple) to the actual HexagonButton objects.
        # This makes coordinate-based lookups (like for pathfinding) nearly instantaneous.
        self._cells: dict[tuple[int, int], HexagonButton] = {}

        # 3. Initialization Flow:
        # Build the grid immediately upon instantiation so the board is ready to draw.
        self._build_grid()

    # ── Grid construction ────────────────────────────────────────────────────

    def _build_grid(self):
        # 1. Fetch layout math from our helper function (_hex_layout).
        centres, radius = _hex_layout(self.cols, self.rows,
                                      self.screen_w, self.screen_h)
        
        self.hex_radius = radius
        for (c, r), (cx, cy) in centres.items():
            # 2. Instantiate the button with its physical and logical coordinates
            btn = HexagonButton(c, r, cx, cy, radius)

            # 3. Edge Detection: Identifies if a tile is part of the board perimeter.
            # This is useful for gameplay mechanics (e.g., 'out of bounds' or wall logic)
            btn.is_edge = (c == 0 or c == self.cols - 1 or
                           r == 0 or r == self.rows - 1)
            # 4. Storage: Using a dictionary allows for O(1) coordinate-to-cell lookups.
            self._cells[(c, r)] = btn

    def rebuild(self, screen_w: int, screen_h: int):
        # Re-compute layout after a window resize (preserves active state).
        
        # 1. Capture Current State: Use a dictionary comprehension to store which 
        # cells are currently active before we overwrite the grid.
        states = {pos: cell.active for pos, cell in self._cells.items()}

        # 2. Update Dimensions: Sync the new screen size for the re-layout.
        self.screen_w = screen_w
        self.screen_h = screen_h

        # 3. Re-Generate: This wipes self._cells and replaces them with new 
        # objects at the new pixel coordinates.
        self._build_grid()

        # 4. Restore State: Iterate through the saved states and re-apply 'active' 
        # status to the new objects at the same logical positions.
        for pos, active in states.items():
            if pos in self._cells:
                self._cells[pos].active = active

    # ── Accessors ────────────────────────────────────────────────────────────
    
    # Safe lookup for a cell by its grid coordinates.
    # Returns None if the coordinates are out of bounds.
    def get_cell(self, col: int, row: int) -> HexagonButton | None:
        return self._cells.get((col, row))

    def cell_at_pixel(self, mx: float, my: float) -> HexagonButton | None:
        # Translates a raw mouse click (screen pixels) into a specific HexagonButton.
        # Uses a two-phase 'Nearest Neighbor' search for high accuracy.
        best      = None
        best_dist = float('inf') # Start with 'infinity' to ensure the first check passes

        # Phase 1: Distance Search
        # We iterate through the cells to find the candidate whose center 
        # is physically closest to the mouse cursor.
        for cell in self._cells.values():
            # math.hypot calculates the straight-line distance: sqrt(dx^2 + dy^2)
            d = math.hypot(mx - cell.cx, my - cell.cy)
            if d < best_dist:
                best_dist = d
                best      = cell

        # Phase 2: Precise Boundary Check
        # Even if 'best' is the closest cell, the click might be outside the 
        # actual hexagon (e.g., in a margin). This confirms a true 'hit'.
        if best and best.contains_point(mx, my):
            return best
        return None

    # ── Hex neighbour logic (flat-top offset grid) ───────────────────────────

    def neighbours(self, col: int, row: int) -> list[tuple[int, int]]:
        
        # Calculates the 6 adjacent coordinates for a given hex.
        # In an offset grid, vertical neighbors shift based on column parity (even/odd).
        
        # Even columns (0, 2, 4...) are 'higher' in the stagger.
        if col % 2 == 0:   
            dirs = [(+1, 0), (+1, -1), (0, -1), (-1, -1), (-1, 0), (0, +1)]

        # Odd columns (1, 3, 5...) are shifted down by row_step / 2.
        else:               
            dirs = [(+1, +1), (+1, 0), (0, -1), (-1, 0), (-1, +1), (0, +1)]

        result = []
        for dc, dr in dirs:
            nc, nr = col + dc, row + dr
            # Validation: Only return neighbors that actually exist on our 32x16 board.
            # This automatically handles map boundaries.
            if (nc, nr) in self._cells:
                result.append((nc, nr))
        return result

    # ── Player actions ───────────────────────────────────────────────────────

    def request_wall(self, col: int, row: int,
                     mouse_positions: list[tuple[int, int]]) -> bool:
        # Validates and executes a 'Wall Placement' move by the Trapper.
        # Walls turn a tile 'inactive', blocking movement for all units.
        cell = self.get_cell(col, row)

        # 1. Validation: 
        # Cannot place on non-existent cells, already blocked cells, or the board perimeter.
        if cell is None or not cell.active or cell.is_edge:
            return False
        
        # 2. Occupancy Check: 
        # A wall cannot be built 'on top' of a mouse.
        if (col, row) in mouse_positions:
            return False

        # 3. Execution:
        # Flip the state. The HexagonButton's internal draw logic will handle the color change.
        cell.active = False
        return True

    def request_move(self, mouse, target_col: int, target_row: int) -> bool:
        # Mouse requests to move from its current cell to (target_col, target_row).
        # Only allowed if the target is an active neighbour.
        
        # 1. Adjacency Check: 
        # Uses the hex neighbor math to ensure the move is exactly 1 tile away.
        if (target_col, target_row) not in self.neighbours(mouse.col, mouse.row):
            return False
        
        # 2. Pathfinding Check:
        # Prevents moving into walls or off the board.
        target = self.get_cell(target_col, target_row)
        if target is None or not target.active:
            return False
        return True

    # ── Win detection ────────────────────────────────────────────────────────

    def _has_path_to_edge(self, start_col: int, start_row: int) -> bool:
        # Uses Breadth-First Search (BFS) to determine if a 'Mouse' at a given 
        # coordinate can still reach the perimeter of the board.

        # 1. Sanity Check: Ensure we aren't starting on a wall or off-board.
        start_cell = self.get_cell(start_col, start_row)
        if start_cell is None or not start_cell.active:
            return False
        
        # 2. Immediate Success: If the mouse is already on the edge, they win.
        if start_cell.is_edge:
            return True

        # 3. BFS Setup:
        # 'visited' prevents redundant checks and infinite loops.
        # 'queue' manages the 'frontier' of tiles we are currently exploring.
        visited = {(start_col, start_row)}
        queue   = deque([(start_col, start_row)])

        # 4. BFS Loop: Continues until we exhaust all reachable tiles or find an edge.
        while queue:
            c, r = queue.popleft()

            # 5. Explore Neighbors:
            # Leverage our hex neighbor logic to find all adjacent tiles.
            for nc, nr in self.neighbours(c, r):
                if (nc, nr) in visited:
                    continue
                nb = self.get_cell(nc, nr)

                # 6. Path Validation:
                # We can only move through 'active' tiles (not walls).
                if nb is None or not nb.active:
                    continue

                # 7. Win Condition:
                # If any searchable neighbor is an edge, a path exists.
                if nb.is_edge:
                    return True
                
                # 8. Add to Frontier:
                visited.add((nc, nr))
                queue.append((nc, nr))

        # 9. No Path Found: If the queue empties, the mouse is officially trapped.
        return False

    # ── Rendering ────────────────────────────────────────────────────────────

    def draw(self, surface, highlighted: set[tuple[int, int]] | None = None):
        # Renders the entire grid to the Pygame surface.
        
        # Args:
        #   surface: The Pygame screen/surface to draw on.
        #   highlighted: An optional set of coordinates to visually flag (e.g., move targets).
        
        for (c, r), cell in self._cells.items():
            # State Injection: Update the 'hovered' property based on external context
            # (like valid move targets) before the cell draws itself.
            cell.hovered = highlighted is not None and (c, r) in highlighted
            cell.draw(surface)

    def get_active_neighbours(self, col: int, row: int) -> list[tuple[int, int]]:
        # Return active neighbour coordinates (for movement highlighting).
        # Filter the 6 neighbors to only include those that are 'active' (not walls).
        return [(c, r) for c, r in self.neighbours(col, row)
                if self._cells[(c, r)].active]
