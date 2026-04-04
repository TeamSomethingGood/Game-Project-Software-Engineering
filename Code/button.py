# button.py
# ---------
# HexagonButton: custom UI element for the Mouse Trap game board.
# Draws a flat-top hexagon using trig and detects clicks via radial distance.


import math
import pygame

# ── Colour palette ──────────────────────────────────────────────────────────
COLOR_ACTIVE        = (30,  70,  30)   # green-tinted active cell
COLOR_INACTIVE      = (80,  15,  15)   # red-tinted dead/wall cell
COLOR_HOVER         = (50, 100,  50)   # lighter green on hover
COLOR_EDGE          = (20,  50,  80)   # blue-tinted border cells (escape tiles)
COLOR_STROKE_ACTIVE = (60, 120,  60)
COLOR_STROKE_DEAD   = (120,  30,  30)
COLOR_STROKE_EDGE   = (40,  90, 140)


class HexagonButton:
#   A single hexagonal cell on the game board.
#   Parameters
#   ----------
#   col, row : int
#   Grid coordinates (0-based).
#   cx, cy : float
#   Pixel centre of the hexagon.
#   radius : float
#   Circumradius (centre → vertex)

    def __init__(self, col: int, row: int, cx: float, cy: float, radius: float):
        self.col    = col
        self.row    = row
        self.cx     = cx
        self.cy     = cy
        self.radius = radius

        # State flags
        self.active  = True   # False = "wall" / deactivated by Trapper
        self.is_edge = False  # True for outermost ring cells
        self.hovered = False

        # Pre-compute the six vertices (flat-top orientation)
        self.vertices = self._compute_vertices()

    # ── Geometry ────────────────────────────────────────────────────────────

    def _compute_vertices(self) -> list[tuple[float, float]]:
        # Return the six corner points of a flat-top hexagon.
        pts = []
        for i in range(6):
            angle_deg = 60 * i          # flat-top: 0°, 60°, 120° 
            angle_rad = math.radians(angle_deg)
            x = self.cx + self.radius * math.cos(angle_rad)
            y = self.cy + self.radius * math.sin(angle_rad)
            pts.append((x, y))
        return pts

    # ── Click detection (radial distance) ───────────────────────────────────

    def contains_point(self, mx: float, my: float) -> bool:     
        # True if the pixel (mx, my) is within the hexagon.
        # Uses circumradius as the threshold — fast and accurate enough for
        # hex grids where hexes tile without large gaps.
        
        dx = mx - self.cx
        dy = my - self.cy
        return math.hypot(dx, dy) <= self.radius * 0.95

    # ── State helpers ────────────────────────────────────────────────────────

    def deactivate(self):
        # Mark this cell as a wall (Trapper action).
        self.active = False

    # ── Rendering ────────────────────────────────────────────────────────────

    # Fill colour depends on state, with hover effect for active cells.
    def _fill_color(self) -> tuple[int, int, int]:
        if not self.active:
            return COLOR_INACTIVE
        if self.is_edge:
            return COLOR_EDGE
        if self.hovered:
            return COLOR_HOVER
        return COLOR_ACTIVE

    # Outline colour depends on state for better visibility against the fill colour.
    def _stroke_color(self) -> tuple[int, int, int]:
        if not self.active:
            return COLOR_STROKE_DEAD
        if self.is_edge:
            return COLOR_STROKE_EDGE
        return COLOR_STROKE_ACTIVE
    
    # Draw the filled hexagon with an outline.
    def draw(self, surface: pygame.Surface):
        pts = [(int(x), int(y)) for x, y in self.vertices]
        pygame.draw.polygon(surface, self._fill_color(), pts)
        pygame.draw.polygon(surface, self._stroke_color(), pts, 1)
