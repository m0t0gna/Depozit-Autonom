"""main.py - interfata pygame + bucla principala a simularii.

Comenzi:
  click stanga  = pune/scoate obstacol
  click dreapta = seteaza tinta (B) pentru robot
  E = arata/ascunde celulele explorate de A*
  R = reset robot in colt
"""
import pygame

from grid import make_warehouse
from robot import Robot

CELL = 30
PANEL_W = 320
STEP_MS = 120           # cat asteapta simularea intre doi pasi ai robotului
START = (1, 1)

BG, FREE, WALL = (245, 245, 245), (255, 255, 255), (70, 70, 80)
ROBOT, GOAL, PATH, EXPL = (30, 110, 230), (40, 170, 70), (120, 200, 140), (220, 232, 250)


def cell_at(mouse_pos):
    """Pixeli -> coordonate de celula."""
    return (mouse_pos[0] // CELL, mouse_pos[1] // CELL)


def draw(screen, font, grid, robot, show_explored):
    screen.fill(BG)
    # 1) celulele
    for y in range(grid.height):
        for x in range(grid.width):
            rect = pygame.Rect(x * CELL, y * CELL, CELL, CELL)
            color = WALL if (x, y) in grid.blocked else FREE
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, (225, 225, 225), rect, 1)
    # 2) ce a explorat A* (util ca sa intelegi cum "cauta")
    if show_explored:
        for (x, y) in robot.explored:
            if (x, y) not in grid.blocked:
                pygame.draw.rect(screen, EXPL, (x * CELL + 1, y * CELL + 1, CELL - 2, CELL - 2))
    # 3) drumul planificat
    for (x, y) in robot.path:
        pygame.draw.rect(screen, PATH, (x * CELL + 8, y * CELL + 8, CELL - 16, CELL - 16))
    # 4) tinta si robotul
    if robot.goal:
        gx, gy = robot.goal
        pygame.draw.rect(screen, GOAL, (gx * CELL + 4, gy * CELL + 4, CELL - 8, CELL - 8))
    rx, ry = robot.pos
    pygame.draw.circle(screen, ROBOT, (rx * CELL + CELL // 2, ry * CELL + CELL // 2), CELL // 2 - 3)

    # 5) panoul de log (in dreapta)
    px = grid.width * CELL
    pygame.draw.rect(screen, (30, 30, 36), (px, 0, PANEL_W, grid.height * CELL))
    lines = [f"{robot.name}  pos={robot.pos}", ""] + list(robot.log)
    for i, text in enumerate(lines):
        screen.blit(font.render(text[:42], True, (230, 230, 230)), (px + 10, 10 + i * 20))


def main():
    pygame.init()
    grid = make_warehouse()
    robot = Robot("Robot 1", START)
    screen = pygame.display.set_mode((grid.width * CELL + PANEL_W, grid.height * CELL))
    pygame.display.set_caption("Simulator depozit - Etapa 1")
    font = pygame.font.SysFont("consolas", 16)
    clock = pygame.time.Clock()

    show_explored = True
    last_step = 0
    running = True
    while running:
        # --- 1. INPUT ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    show_explored = not show_explored
                elif event.key == pygame.K_r:
                    robot = Robot("Robot 1", START)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                cell = cell_at(event.pos)
                if not grid.in_bounds(cell):
                    continue
                if event.button == 1 and cell != robot.pos and cell != robot.goal:
                    grid.toggle(cell)
                    # replanificam doar daca noul obstacol cade pe drumul robotului
                    if cell in robot.path:
                        robot.log.append(f"Obstacol nou pe traseu la {cell}")
                        robot.plan(grid)
                elif event.button == 3 and grid.is_free(cell):
                    robot.set_goal(grid, cell)

        # --- 2. UPDATE (simularea avanseaza la intervale fixe) ---
        now = pygame.time.get_ticks()
        if now - last_step >= STEP_MS:
            robot.step(grid)
            last_step = now

        # --- 3. DRAW ---
        draw(screen, font, grid, robot, show_explored)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
