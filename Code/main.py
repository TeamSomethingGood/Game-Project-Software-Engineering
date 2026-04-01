"""
main.py
-------
Entry point for Mouse Trap.

GameManager is a thin orchestrator — it owns the game loop, the state
machine, and the core game objects (Gameboard, Mice, Trapper, TurnManager).
All screen rendering and input handling is delegated to the screen modules:

    mainmenu.py   MainMenuScreen
    setup.py      SetupScreen
    play.py       PlayScreen
    pause.py      PauseScreen
    gameover.py   GameOverScreen

To add a new screen: create a new <n>.py following the same pattern
(handle_event / draw), then wire it into GameManager below.
"""

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
    """
    Manages the strict alternating turn sequence:
        Mouse 1 -> Trapper -> Mouse 2 -> Trapper -> ... -> back to Mouse 1
    """

    def __init__(self, num_mice: int):
        self.num_mice  = num_mice
        self._sequence = []
        for i in range(num_mice):
            self._sequence.append((TURN_MOUSE, i))
            self._sequence.append((TURN_TRAPPER, None))
        self._index = 0


    def current(self):
        return self._sequence[self._index]

    def advance(self):
        self._index = (self._index + 1) % len(self._sequence)

    def reset(self):
        self._index = 0

    def turn_label(self) -> str:
        state, idx = self.current()
        if state == TURN_MOUSE:
            return f"Mouse {idx + 1}'s Turn  --  Click an adjacent hex to move"
        return "Trapper's Turn  --  Click any active hex to place a wall"


class GameManager:
    """High-level orchestrator. Delegates all UI to screen modules."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.RESIZABLE)
        pygame.display.set_caption("Mouse Trap")
        self.clock = pygame.time.Clock()

        self.state    = STATE_MENU
        self.num_mice = 0

        self.gameboard = None
        self.trapper   = None
        self.mice      = []
        self.turn_mgr  = None

        self.screen_menu     = MainMenuScreen(self.screen)
        self.screen_setup    = SetupScreen(self.screen)
        self.screen_play     = None
        self.screen_pause    = PauseScreen(self.screen)
        self.screen_gameover = GameOverScreen(self.screen)

        self._play_snapshot = None

    def run(self):
        while True:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.VIDEORESIZE:
                    self._on_resize(event.w, event.h)
                self._handle_event(event)
            self._draw()
            pygame.display.flip()

    def _on_resize(self, w, h):
        if self.gameboard:
            self.gameboard.rebuild(w, h - BOARD_TOP)
            for m in self.mice:
                m.update()

    def _handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.state == STATE_PLAY:
                self.state = STATE_PAUSED
                return
            if self.state == STATE_PAUSED:
                self.state = STATE_PLAY
                return

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
            if result == SIGNAL_PLAY_AGAIN:
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

        # Initialize mice at their starting positions, cycling through MOUSE_STARTS if there are more mice than starting positions.
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
        self.screen_gameover.set_message(message)
        self.state = STATE_GAMEOVER

    def _draw(self):
        if self.state == STATE_MENU:
            self.screen_menu.draw()
        elif self.state == STATE_SETUP:
            self.screen_setup.draw()
        elif self.state == STATE_PLAY and self.screen_play:
            self.screen_play.draw()
            self._play_snapshot = self.screen.copy()
        elif self.state == STATE_PAUSED:
            self.screen_pause.draw(self._play_snapshot)
        elif self.state == STATE_GAMEOVER:
            self.screen_gameover.draw()

# Launches the game. 
gm = GameManager()
gm.run()