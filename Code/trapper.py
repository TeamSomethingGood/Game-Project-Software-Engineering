"""
trapper.py
----------
Trapper: a logic class that calculates strategic "wall" placement.
Sends wall requests to the Gameboard based on user input coordinates.
"""


class Trapper:
    """
    Represents the Trapper player.

    The Trapper's goal is to deactivate (wall off) hexagonal grid cells
    to block all paths between Mouse players and the board's outer edges.

    Parameters
    ----------
    gameboard : Gameboard
        Reference to the shared game board.
    """

    def __init__(self, gameboard):
        self.gameboard   = gameboard
        self.walls_placed = 0   # running count of walls placed this game
        self.label        = "Trapper"

    # ── Core action ───────────────────────────────────────────────────────────

    def try_place_wall(self, col: int, row: int,
                       mouse_positions: list[tuple[int, int]]) -> bool:
        """
        Attempt to place a wall at (col, row).

        Delegates all validation to the Gameboard, which checks:
          • Cell exists and is currently active
          • Cell is not an edge tile
          • Cell is not occupied by a Mouse
          • Placing the wall does not immediately trap ALL mice
            (BFS path-to-edge check)

        Returns True if the wall was successfully placed.
        """
        success = self.gameboard.request_wall(col, row, mouse_positions)
        if success:
            self.walls_placed += 1
        return success

