# main.py
# -------
# Entry point for Mouse Trap.
# GameManager is a thin orchestrator — it owns the game loop, the state
# machine, and the core game objects (Gameboard, Mice, Trapper, TurnManager).
# All screen rendering and input handling is delegated to the screen modules:
#     mainmenu.py   MainMenuScreen
#     setup.py      SetupScreen
#     play.py       PlayScreen
#     pause.py      PauseScreen
#     gameover.py   GameOverScreen

# To add a new screen: create a new <n>.py following the same pattern
# (handle_event / draw), then wire it into GameManager below.


import sys
import pygame

from gameboard import Gameboard
from mouse     import Mouse
from trapper   import Trapper

from ui_shared import (
    WINDOW_W, WINDOW_H, FPS,
    STATE_MENU, STATE_SETUP, STATE_PLAY, STATE_PAUSED, STATE_GAMEOVER,
    TURN_MOUSE, TURN_TRAPPER,
    MOUSE_STARTS, BOARD_TOP,
)

from mainmenu import MainMenuScreen
from setup    import SetupScreen,    SIGNAL_START
from play     import PlayScreen,     SIGNAL_MOUSE_WIN, SIGNAL_TRAPPER_WIN
from pause    import PauseScreen, SIGNAL_RESTART
from gameover import GameOverScreen, SIGNAL_PLAY_AGAIN


class TurnManager:
    # Orchestrates the 'Round Robin' turn sequence for the game.
    # Ensures that for every mouse move, the Trapper receives a counter-move.

    
    def __init__(self, num_mice: int):
        self.num_mice  = num_mice
        self._sequence = []

        # Build the turn order: [ (Mouse0), (Trapper), (Mouse1), (Trapper) ... ]
        # This structure allows for a variable number of mice while maintaining 
        # the Trapper's role as the consistent antagonist.
        for i in range(num_mice):
            self._sequence.append((TURN_MOUSE, i))
            self._sequence.append((TURN_TRAPPER, None))
        self._index = 0


    def current(self):
        # Returns the current turn (Role, ID).
        # Role is either TURN_MOUSE or TURN_TRAPPER. ID is the mouse index for mouse turns, and None for trapper turns.
        return self._sequence[self._index]

    def advance(self):
        # Advances to the next turn in the sequence. 
        # Uses modulo arithmetic to loop back to the start indefinitely.
        self._index = (self._index + 1) % len(self._sequence)

    def reset(self):
        # Resets the game flow to Mouse 1's starting turn.
        self._index = 0

    def turn_label(self) -> str:
        # Generates a human-readable string for the UI HUD.
        state, idx = self.current()
        if state == TURN_MOUSE:
            # Shift from 0-based technical index to 1-based player label.
            return f"Mouse {idx + 1}'s Turn  --  Click an adjacent hex to move"
        return "Trapper's Turn  --  Click any active hex to place a wall"


class GameManager:
    # High-level orchestrator. Delegates all UI to screen modules.
    # Manages global state, window lifecycle, and high-level transitions.

    def __init__(self):
        # Initialize Pygame engine components
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.RESIZABLE)
        pygame.display.set_caption("Mouse Trap")
        self.clock = pygame.time.Clock()

        # State Management: Dictates which 'Scene' is currently active
        self.state    = STATE_MENU
        self.num_mice = 0

        # Game Logic Objects (Models): Initialized as None until a game starts
        self.gameboard = None
        self.trapper   = None
        self.mice      = []
        self.turn_mgr  = None

        # View Objects (Screens): Pre-instantiated to preserve UI state/memory
        self.screen_menu     = MainMenuScreen(self.screen)
        self.screen_setup    = SetupScreen(self.screen)
        self.screen_play     = None
        self.screen_pause    = PauseScreen(self.screen)
        self.screen_gameover = GameOverScreen(self.screen)

        # Snapshot for Pause System: Stores the last 'Play' frame to blur/dim behind the menu
        self._play_snapshot = None

    def run(self):
        # Standard Game Loop: Ensures consistent frame timing and event polling.
        while True:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                # Dynamic Layout Support: Responds to user resizing the window
                if event.type == pygame.VIDEORESIZE:
                    self._on_resize(event.w, event.h)
                self._handle_event(event)

            # Draw and Buffer Swap
            self._draw()
            pygame.display.flip()

    def _on_resize(self, w, h):
        # Propagates window size changes to the internal grid logic.
        if self.gameboard:
            # Re-calculates hex centers and sizes to fit the new aspect ratio
            self.gameboard.rebuild(w, h - BOARD_TOP)
            for m in self.mice:
                m.update() # Snaps mice to their new physical pixel positions

    def _handle_event(self, event):
        # The Master Switchboard: Routes input events based on current game state.

        # Global hotkey for pausing and resuming the game, regardless of current screen.
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.state == STATE_PLAY:
                self.state = STATE_PAUSED
                return
            if self.state == STATE_PAUSED:
                self.state = STATE_PLAY
                return

        # State-Specific Event Delegation
        if self.state == STATE_MENU:
            result = self.screen_menu.handle_event(event)
            if result:
                self.state = result

        elif self.state == STATE_SETUP:
            result = self.screen_setup.handle_event(event)
            if result == SIGNAL_START:
                self._start_game()
            elif result:
                self.state = result

        elif self.state == STATE_PLAY and self.screen_play:
            result = self.screen_play.handle_event(event)

            # String parsing for dynamic win messages
            if result == STATE_PAUSED:
                self.state = STATE_PAUSED
            elif result == STATE_MENU:
                self.state = STATE_MENU
            elif result and result.startswith(SIGNAL_MOUSE_WIN):
                idx = int(result.split(":")[1])
                self._end_game(f"Mouse {idx + 1} escaped! Mice Win!")
            elif result == SIGNAL_TRAPPER_WIN:
                walls = self.trapper.walls_placed if self.trapper else "?"
                self._end_game(f"All paths blocked! Trapper Wins!  (Walls: {walls})")

        elif self.state == STATE_PAUSED:
            result = self.screen_pause.handle_event(event)
            # Standard transition logic for Pause Menu options: Resume, Main Menu, Restart, Quit.
            if result == STATE_PLAY:
                self.state = STATE_PLAY
            elif result == STATE_MENU:
                self.state = STATE_MENU
            elif result == SIGNAL_RESTART:
                self.state = STATE_SETUP
            elif result == "QUIT_APP":
                pygame.quit()
                sys.exit()
        
        # Game over screen returns either SIGNAL_PLAY_AGAIN, STATE_MENU, or Quit.
        # SIGNAL_PLAY_AGAIN needs special handling to restart the game
        elif self.state == STATE_GAMEOVER:
            result = self.screen_gameover.handle_event(event)
            if result == SIGNAL_PLAY_AGAIN: # Re-runs setup logic for a fresh session
                self._start_game()
            elif result:
                self.state = result

    # Initializes all core game objects and transitions to the play state.
    def _start_game(self):
        # On game start, we need to initialize all core game objects in the correct order:
        w, h = self.screen.get_size()
        bw, bh = w, h - BOARD_TOP

        # Number of mice is determined by the setup screen, which must be initialized before the gameboard and mice.
        self.num_mice  = self.screen_setup.num_mice
        self.gameboard = Gameboard(bw, bh)
        self.trapper   = Trapper(self.gameboard)

        # Mouse Spawning: Uses modulo to wrap around if num_mice > available start nodes
        self.mice.clear()
        for i in range(self.num_mice):
            c, r = MOUSE_STARTS[i % len(MOUSE_STARTS)]
            self.mice.append(Mouse(i, c, r, self.gameboard))

        # Turn manager only needs the number of mice to build the turn sequence.
        self.turn_mgr    = TurnManager(self.num_mice)   

        # Pass all core game objects to the PlayScreen, which will handle the main game logic and rendering.
        self.screen_play = PlayScreen(
            self.screen, self.gameboard,
            self.mice, self.trapper, self.turn_mgr,
        )

        # Clear the play snapshot, since fresh games doesn't have a snapshot yet.
        self._play_snapshot = None  

        # Transition to the play state.
        self.state = STATE_PLAY

    def _end_game(self, message: str):
        # Prepares the GameOver screen with a specific results message.
        self.screen_gameover.set_message(message)
        self.state = STATE_GAMEOVER

    def _draw(self):
        # Scene Dispatcher: Delegates rendering to the currently active Screen object.
        if self.state == STATE_MENU:
            self.screen_menu.draw()
        elif self.state == STATE_SETUP:
            self.screen_setup.draw()
        elif self.state == STATE_PLAY and self.screen_play:
            self.screen_play.draw()
            # Capture current frame for the pause screen background
            self._play_snapshot = self.screen.copy()
        elif self.state == STATE_PAUSED:
            # Pass the snapshot so the pause menu can draw on top of a frozen game state
            self.screen_pause.draw(self._play_snapshot)
        elif self.state == STATE_GAMEOVER:
            self.screen_gameover.draw()

# Launches the game. 
gm = GameManager()
gm.run()
