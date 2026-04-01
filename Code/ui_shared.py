"""
ui_shared.py
------------
Shared constants, colours, font helpers, and reusable drawing utilities
used by every screen module (mainmenu, setup, play, pause, gameover).

Import from here instead of duplicating across screen files.
"""

import math
import pygame

# ── Window / layout ──────────────────────────────────────────────────────────
WINDOW_W  = 1280
WINDOW_H  = 720
BOARD_TOP = 110       # pixels reserved for HUD above the board
FPS       = 60

# ── Colours ───────────────────────────────────────────────────────────────────
C_BG        = ( 13,  13,  13)
C_PANEL     = ( 20,  20,  20)
C_ACCENT    = (245, 197,  24)   # yellow
C_ACCENT2   = (224,  92,  42)   # orange
C_TEXT      = (232, 232, 224)
C_DIM       = (100, 100,  90)
C_MOUSE_HUD = [(126, 200, 227), (255, 200, 80), (180, 130, 220), (100, 220, 160)]
C_GREEN     = ( 60, 180,  60)
C_RED       = (200,  50,  50)

# ── GameManager states ────────────────────────────────────────────────────────
STATE_MENU     = "MENU"
STATE_SETUP    = "SETUP"
STATE_PLAY     = "PLAY"
STATE_PAUSED   = "PAUSED"
STATE_GAMEOVER = "GAMEOVER"

# ── TurnManager states ────────────────────────────────────────────────────────
TURN_MOUSE   = "MOUSE_TURN"
TURN_TRAPPER = "TRAPPER_TURN"

# ── Mouse starting positions (col, row) ──────────────────────────────────────
MOUSE_STARTS = [(15, 4), (16, 11), (14, 7), (17, 8)]


# ── Font helpers ──────────────────────────────────────────────────────────────

def make_font(size: int, bold: bool = False) -> pygame.font.Font:
    try:
        return pygame.font.SysFont("couriernew", size, bold=bold)
    except Exception:
        return pygame.font.Font(None, size)


def make_georgia(size: int, bold: bool = False) -> pygame.font.Font:
    try:
        return pygame.font.SysFont("Georgia", size, bold=bold)
    except Exception:
        return make_font(size, bold)


def make_courier(size: int, bold: bool = False) -> pygame.font.Font:
    try:
        return pygame.font.SysFont("Courier", size, bold=bold)
    except Exception:
        return make_font(size, bold)


# ── Shared drawing utilities ──────────────────────────────────────────────────

def draw_button(screen: pygame.Surface, text: str, cx: int, cy: int,
                fg: tuple, bg: tuple, font: pygame.font.Font,
                width: int = 0) -> pygame.Rect:
    """
    Draw a styled text button centred at (cx, cy) onto screen.
    Returns the button's Rect for hit-testing.
    """
    surf  = font.render(text, True, fg)
    pad_x, pad_y = 28, 12
    bw = max(surf.get_width() + pad_x * 2, width)
    bh = surf.get_height() + pad_y * 2
    rect = pygame.Rect(cx - bw // 2, cy - bh // 2, bw, bh)

    pygame.draw.rect(screen, bg, rect, border_radius=6)
    pygame.draw.rect(screen, fg, rect, 2, border_radius=6)

    mx, my = pygame.mouse.get_pos()
    if rect.collidepoint(mx, my):
        bright = pygame.Surface((bw, bh), pygame.SRCALPHA)
        bright.fill((255, 255, 255, 18))
        screen.blit(bright, rect.topleft)

    screen.blit(surf, surf.get_rect(center=rect.center))
    return rect


def draw_bg_grid(screen: pygame.Surface, w: int, h: int):
    """Faint decorative hex grid used on menu/setup/gameover backgrounds."""
    r        = 24
    col_step = r * 1.5
    row_step = r * math.sqrt(3)
    for c in range(int(w // col_step) + 2):
        for rr in range(int(h // row_step) + 2):
            cx = c * col_step
            cy = rr * row_step + (row_step / 2 if c % 2 == 1 else 0)
            pts = []
            for i in range(6):
                a = math.radians(60 * i)
                pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
            pts = [(int(x), int(y)) for x, y in pts]
            pygame.draw.polygon(screen, (30, 45, 30), pts, 1)
