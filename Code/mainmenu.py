"""
mainmenu.py
-----------
MainMenuScreen: draws and handles input for the Main Menu state.

Owns:
  • Dark grid background
  • Bouncing mouse-face logo (SomethingGood? team branding)
  • Semi-transparent yellow panel with title + Play button

Returns the next state string to GameManager via handle_event() / update().
"""

import pygame

from ui_shared import (
    STATE_SETUP,
    make_georgia, make_courier,
)


class MainMenuScreen:
    """
    Self-contained Main Menu screen.

    Usage
    -----
    screen_obj = MainMenuScreen(pygame_surface)
    # each frame:
    next_state = screen_obj.handle_event(event)   # returns new state or None
    screen_obj.draw()
    """

    # Logo bounding box size
    LOGO_W = 80
    LOGO_H = 80

    def __init__(self, surface: pygame.Surface):
        self.surface = surface

        # Fonts
        self.font_title = make_georgia(64, bold=True)
        self.font_play  = make_georgia(32, bold=True)
        self.font_logo  = make_courier(18, bold=True)

        # Bouncing logo physics
        self._logo_x  = 80.0
        self._logo_y  = 60.0
        self._logo_vx = 2.2
        self._logo_vy = 1.9

        # Button rect — rebuilt every draw()
        self._play_rect: pygame.Rect | None = None

    # ── Public interface ──────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """
        Process one pygame event.
        Returns the next STATE string if a transition should occur, else None.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._play_rect and self._play_rect.collidepoint(event.pos):
                return STATE_SETUP
        return None

    def draw(self):
        """Render the full menu screen onto self.surface."""
        w, h = self.surface.get_size()
        self._update_logo(w, h)
        self._draw_background(w, h)
        self._draw_logo(self._logo_x, self._logo_y)
        self._draw_panel(w, h)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _update_logo(self, w: int, h: int):
        """Advance the bouncing logo one frame."""
        self._logo_x += self._logo_vx
        self._logo_y += self._logo_vy
        if self._logo_x <= 0 or self._logo_x + self.LOGO_W >= w:
            self._logo_vx *= -1
            self._logo_x = max(0.0, min(self._logo_x, float(w - self.LOGO_W)))
        if self._logo_y <= 0 or self._logo_y + self.LOGO_H >= h:
            self._logo_vy *= -1
            self._logo_y = max(0.0, min(self._logo_y, float(h - self.LOGO_H)))

    def _draw_background(self, w: int, h: int):
        """Dark background with subtle grid lines."""
        self.surface.fill((15, 12, 10))
        for gx in range(0, w, 30):
            pygame.draw.line(self.surface, (25, 20, 15), (gx, 0), (gx, h))
        for gy in range(0, h, 30):
            pygame.draw.line(self.surface, (25, 20, 15), (0, gy), (w, gy))

    def _draw_logo(self, x: float, y: float):
        """Cute bouncing mouse face with team name label."""
        LOGO_COLOR   = (255, 220,  60)
        LOGO_OUTLINE = (120,  90,  10)
        cx = int(x + self.LOGO_W / 2)
        cy = int(y + self.LOGO_H / 2)
        r  = 28

        # Body
        pygame.draw.circle(self.surface, LOGO_COLOR,   (cx, cy + 6), r)
        pygame.draw.circle(self.surface, LOGO_OUTLINE, (cx, cy + 6), r, 2)

        # Ears
        for _, ex in [(-1, cx - 22), (1, cx + 22)]:
            pygame.draw.circle(self.surface, LOGO_COLOR,      (ex, cy - 18), 12)
            pygame.draw.circle(self.surface, LOGO_OUTLINE,    (ex, cy - 18), 12, 2)
            pygame.draw.circle(self.surface, (220, 140, 140), (ex, cy - 18),  8)

        # Eyes
        pygame.draw.circle(self.surface, (30, 20, 10),    (cx - 10, cy + 2), 4)
        pygame.draw.circle(self.surface, (30, 20, 10),    (cx + 10, cy + 2), 4)
        pygame.draw.circle(self.surface, (255, 255, 255), (cx -  9, cy + 1), 1)
        pygame.draw.circle(self.surface, (255, 255, 255), (cx + 11, cy + 1), 1)

        # Nose
        pygame.draw.circle(self.surface, (200, 80, 80), (cx, cy + 12), 3)

        # Whiskers
        for side in [-1, 1]:
            for dy in [-3, 0, 3]:
                pygame.draw.line(self.surface, LOGO_OUTLINE,
                                 (cx + side * 4,  cy + 12 + dy),
                                 (cx + side * 26, cy + 10 + dy), 1)

        # Team label
        label = self.font_logo.render("SomethingGood?", True, LOGO_OUTLINE)
        self.surface.blit(label, (cx - label.get_width() // 2, cy + r + 10))

    def _draw_panel(self, w: int, h: int):
        """Semi-transparent yellow panel with title and Play button."""
        PANEL_W = min(420, w - 40)
        PANEL_H = 280
        PANEL_X = (w - PANEL_W) // 2
        PANEL_Y = (h - PANEL_H) // 2

        # Panel fill
        panel_surf = pygame.Surface((PANEL_W, PANEL_H), pygame.SRCALPHA)
        panel_surf.fill((210, 180, 80, 160))
        pygame.draw.rect(panel_surf, (180, 150, 40, 80),
                         (0, 0, PANEL_W, PANEL_H), border_radius=18)
        self.surface.blit(panel_surf, (PANEL_X, PANEL_Y))
        pygame.draw.rect(self.surface, (200, 165, 50),
                         (PANEL_X, PANEL_Y, PANEL_W, PANEL_H), 2, border_radius=18)

        # Title with drop shadow
        shadow = self.font_title.render("Mouse Trap", True, (150, 120, 20))
        title  = self.font_title.render("Mouse Trap", True, ( 20,  15, 10))
        tx = PANEL_X + (PANEL_W - title.get_width()) // 2
        ty = PANEL_Y + 30
        self.surface.blit(shadow, (tx + 3, ty + 3))
        self.surface.blit(title,  (tx,     ty))

        # Play button
        BTN_W, BTN_H = 160, 50
        BTN_X = (w   - BTN_W) // 2
        BTN_Y = PANEL_Y + 195
        btn_rect = pygame.Rect(BTN_X, BTN_Y, BTN_W, BTN_H)

        mx, my  = pygame.mouse.get_pos()
        hovered = btn_rect.collidepoint(mx, my)
        bg_col  = (255, 210,   0) if hovered else (210, 175,  40)
        txt_col = (255, 230,  80) if hovered else ( 20,  15,  10)

        pygame.draw.rect(self.surface, bg_col,        btn_rect, border_radius=10)
        pygame.draw.rect(self.surface, (120, 90, 10), btn_rect, 2, border_radius=10)

        lbl = self.font_play.render("▶  Play", True, txt_col)
        self.surface.blit(lbl, lbl.get_rect(center=btn_rect.center))

        self._play_rect = btn_rect
