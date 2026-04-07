# mouse.py
# --------
# Mouse: a pygame.sprite.Sprite that represents one Mouse player.
# Sends Move requests to the Gameboard and renders on the top layer.

import pygame
from button import HexagonButton

# Colour assigned to each mouse index (up to 4)
MOUSE_COLORS = [
    (126, 200, 227),   # 0 – sky blue
    (255, 200,  80),   # 1 – gold
    (180, 130, 220),   # 2 – lavender
    (100, 220, 160),   # 3 – mint
]

MOUSE_RADIUS = 10   # The logical 'hitbox' and size for the token

class Mouse(pygame.sprite.Sprite):
    # Inheriting from pygame.sprite.Sprite allows the Mouse to be 
    # managed by Sprite Groups for efficient, layered rendering.
    # Represents one Mouse player token on the board.
    # Parameters
    # ----------
    # player_index : int   0-based index among mice (0..3)
    # col, row     : int   Starting grid position
    # gameboard    : Gameboard   Reference for move validation and pathfinding

    def __init__(self, player_index: int, col: int, row: int, gameboard):
        # Initialize the parent Sprite class
        super().__init__()

        self.player_index = player_index
        self.col          = col
        self.row          = row
        self.gameboard    = gameboard   # Dependency Injection: Reference to the shared board

        # Color logic: Uses modulo so the game won't crash if > 4 mice are added
        self.color        = MOUSE_COLORS[player_index % len(MOUSE_COLORS)]

        # State Flags: Controlled by Gameboard/TurnManager logic
        self.escaped      = False   # True once the mouse reaches an edge cell
        self.trapped      = False   # True if the trapper has blocked all paths to edge cells

        # 1. Surface Pre-rendering: 
        # Creating a transparent 'canvas' for the sprite. +4 pixels allows 
        size = MOUSE_RADIUS * 2 + 4
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self._render_image()

        # 2. Rect Management: 
        # The 'rect' is used by Pygame's draw() methods to position the image.
        self.rect = self.image.get_rect()
        self._sync_rect()

    # ── Rendering ────────────────────────────────────────────────────────────

    def _render_image(self):
        # Procedural Sprite Generation: 
        # Draws the mouse once during initialization to save CPU cycles.

        # Clear the surface with 100% transparency
        self.image.fill((0, 0, 0, 0))

        # Find local center within the sprite surface
        cx = cy = self.image.get_width() // 2

        # Layer 1: Dark Outline (simulates depth/shadow)
        pygame.draw.circle(self.image, (20, 20, 20), (cx, cy), MOUSE_RADIUS + 1)

        # Layer 2: Main Body
        pygame.draw.circle(self.image, self.color,   (cx, cy), MOUSE_RADIUS)

        # Layer 3: Ear Bumps (The 'Mickey' silhouette)
        ear_r = MOUSE_RADIUS // 3

        # Left Ear
        pygame.draw.circle(self.image, self.color, (cx - MOUSE_RADIUS + 2, cy - MOUSE_RADIUS + 2), ear_r)
        # Right Ear
        pygame.draw.circle(self.image, self.color, (cx + MOUSE_RADIUS - 2, cy - MOUSE_RADIUS + 2), ear_r)

    def _sync_rect(self):
        # Keep self.rect centered on the hexagon's pixel position.
        hex_cell = self.gameboard.get_cell(self.col, self.row)
        if hex_cell:
            self.rect.center = (int(hex_cell.cx), int(hex_cell.cy))

    # ── Path scanning ─────────────────────────────────────────────────────────

    def has_escape_path(self) -> bool:
        # Pre-Turn Validation: 
        # Performs a reachability analysis to determine if the Mouse is 'Checkmated'.
        # Returns:
        #     True: If the Mouse can physically reach any exit on the board perimeter.
        #     False: If the Trapper has successfully walled off all possible escape routes.
        # Note:
        #     This is called at the start of the Mouse's turn. If it returns False, 
        #     the game should immediately transition to the 'Trapper Wins' state 
        #     without allowing the Mouse to move.
        return self.gameboard._has_path_to_edge(self.col, self.row)

    # ── Movement ─────────────────────────────────────────────────────────────

    def try_move(self, target_col: int, target_row: int) -> bool:
        # Movement Operation: 
        # Checks with the board, updates coordinates, and checks the win-condition.
        
        # Request permission from the Gameboard to move to the target cell. 
        # The Gameboard will validate:
        success = self.gameboard.request_move(self, target_col, target_row)

        if success:
            # Sync logical position with the target cell
            self.col = target_col
            self.row = target_row

            # Update physical rect for the next draw call
            self._sync_rect()

            # Check for Win-Condition: Did we land on the perimeter?
            cell = self.gameboard.get_cell(self.col, self.row)
            if cell and cell.is_edge:
                self.escaped = True
        return success

    # ── Update (called each frame by sprite group) ───────────────────────────

    def update(self):
        # Responsive UI Hook: 
        # By calling _sync_rect every frame, the mouse will stay perfectly 
        # aligned with its hexagon even if the user resizes the window.
        self._sync_rect()

    
