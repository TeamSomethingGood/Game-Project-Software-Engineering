import pygame
import math

pygame.init()

# --- Grid settings ---
GRID_WIDTH = 32
GRID_HEIGHT = 16
HEX_RADIUS = 20  # size of each hex

# --- Derived hex geometry ---
HEX_WIDTH = math.sqrt(3) * HEX_RADIUS
HEX_HEIGHT = 2 * HEX_RADIUS
VERTICAL_SPACING = HEX_HEIGHT * 0.75  # vertical distance between rows

# --- Screen size ---
SCREEN_WIDTH = int(GRID_WIDTH * HEX_WIDTH + HEX_WIDTH)
SCREEN_HEIGHT = int(GRID_HEIGHT * VERTICAL_SPACING + HEX_HEIGHT)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

clock = pygame.time.Clock()


def hex_points(cx, cy, r):
    """Return the 6 corner points of a pointy‑topped hexagon."""
    points = []
    for i in range(6):
        angle_deg = 60 * i - 30
        angle_rad = math.radians(angle_deg)
        x = cx + r * math.cos(angle_rad)
        y = cy + r * math.sin(angle_rad)
        points.append((x, y))
    return points


def draw_hex_grid():
    for row in range(GRID_HEIGHT):
        for col in range(GRID_WIDTH):

            # Offset every other row (pointy‑topped hex layout)
            x = col * HEX_WIDTH + (HEX_WIDTH / 2 if row % 2 else 0)
            y = row * VERTICAL_SPACING

            pygame.draw.polygon(
                screen,
                (255, 255, 255),  # white outline
                hex_points(x, y, HEX_RADIUS),
                width=1
            )


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((0, 0, 0))  # black background
    draw_hex_grid()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
