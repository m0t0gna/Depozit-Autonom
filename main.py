"""Interfata Pygame pentru simulatorul de depozit autonom."""
import pygame

from engine.grid import make_warehouse
from engine.robot import Robot

CELL = 30
PANEL_W = 360
STEP_MS = 120
START = (1, 1)
SPEEDS = (500, 250, 120, 60, 30)

BG = (15, 23, 38)
FREE, WALL = (27, 39, 55), (76, 91, 111)
ROBOT, GOAL, PATH, EXPL = (73, 171, 255), (68, 218, 159), (59, 159, 125), (32, 61, 80)
TEXT, MUTED = (231, 239, 249), (149, 168, 190)


def cell_at(mouse_pos):
    """Pixeli -> coordonate de celula."""
    return mouse_pos[0] // CELL, mouse_pos[1] // CELL


class Simulation:
    """Starea interactiva, separata de desenare pentru verificare fara fereastra."""

    def __init__(self):
        self.grid = make_warehouse()
        self.robot = Robot("Robot 1", START)
        self.paused = False
        self.show_explored = True
        self.speed_index = SPEEDS.index(STEP_MS)

    @property
    def step_ms(self):
        return SPEEDS[self.speed_index]

    def reset(self, restore_map=False):
        if restore_map:
            self.grid = make_warehouse()
        # Celula initiala ramane accesibila inclusiv dupa editarea hartii.
        self.grid.blocked.discard(START)
        self.robot = Robot("Robot 1", START)

    def edit(self, cell):
        if not self.grid.in_bounds(cell) or cell in (self.robot.pos, self.robot.goal, START):
            return
        self.grid.toggle(cell)
        # Orice editare poate redeschide accesul sau crea un drum mai scurt.
        if self.robot.goal is not None and self.robot.pos != self.robot.goal:
            self.robot.plan(self.grid)

    def change_speed(self, delta):
        self.speed_index = max(0, min(len(SPEEDS) - 1, self.speed_index + delta))


def wrapped_lines(font, text, width):
    line = ""
    for word in text.split():
        candidate = f"{line} {word}".strip()
        if line and font.size(candidate)[0] > width:
            yield line
            line = word
        else:
            line = candidate
    if line:
        yield line


def draw(screen, font, grid, robot, show_explored, paused=False, step_ms=STEP_MS):
    screen.fill(BG)
    explored = set(robot.explored) if show_explored else set()
    for y in range(grid.height):
        for x in range(grid.width):
            cell = (x, y)
            color = WALL if cell in grid.blocked else EXPL if cell in explored else FREE
            rect = pygame.Rect(x * CELL + 1, y * CELL + 1, CELL - 2, CELL - 2)
            pygame.draw.rect(screen, color, rect, border_radius=3)
            if cell in grid.blocked:
                pygame.draw.line(screen, (98, 113, 133), rect.topleft, rect.topright)

    def center(cell):
        return cell[0] * CELL + CELL // 2, cell[1] * CELL + CELL // 2

    pygame.draw.circle(screen, MUTED, center(START), 10, 1)
    if robot.path:
        pygame.draw.lines(screen, PATH, False, [center(robot.pos)] + [center(c) for c in robot.path], 3)
        for cell in robot.path:
            pygame.draw.circle(screen, GOAL, center(cell), 3)
    if robot.goal is not None:
        pygame.draw.circle(screen, GOAL, center(robot.goal), 11, 2)
        pygame.draw.circle(screen, GOAL, center(robot.goal), 4)
    pygame.draw.circle(screen, (20, 75, 119), center(robot.pos), 14)
    pygame.draw.circle(screen, ROBOT, center(robot.pos), 10)
    pygame.draw.circle(screen, TEXT, center(robot.pos), 3)

    px = grid.width * CELL
    pygame.draw.rect(screen, BG, (px, 0, PANEL_W, screen.get_height()))

    def label(text, y, color=TEXT, x=20):
        screen.blit(font.render(text, True, color), (px + x, y))

    label("DEPOZIT AUTONOM", 20, ROBOT)
    label("Planificare A* / 4 directii", 44, MUTED)
    pygame.draw.line(screen, WALL, (px + 20, 78), (px + PANEL_W - 20, 78))
    state = "PAUZA | " + robot.status if paused else robot.status
    label(state, 94, GOAL if robot.path or robot.pos == robot.goal else TEXT)
    label(f"Pozitie: {robot.pos}   Tinta: {robot.goal or '-'}", 123)
    label(f"Pasi ramasi: {len(robot.path)}", 149)
    label(f"Pasi parcursi: {robot.steps_taken}", 175)
    label(f"Explorate: {len(robot.explored)}   Planuri: {robot.plans}", 201)
    label(f"Viteza: {1000 / step_ms:.1f} pasi/sec", 227, ROBOT)

    label("COMENZI", 266, MUTED)
    for i, line in enumerate((
        "Click stanga   Adauga/scoate raft",
        "Click dreapta  Alege tinta",
        "Spatiu         Pauza / continua",
        "N              Un pas in pauza",
        "Sus / Jos      Mai rapid / lent",
        "E              Explorare A*",
        "R / Shift+R    Reset robot / tot",
        "Esc            Inchide",
    )):
        label(line, 292 + i * 21)

    label("JURNAL RECENT", 477, MUTED)
    lines = [line for entry in robot.log for line in wrapped_lines(font, entry, PANEL_W - 40)]
    capacity = max(0, (screen.get_height() - 510) // 20)
    for i, line in enumerate(lines[-capacity:] if capacity else []):
        label(line, 505 + i * 20, MUTED)


def main():
    pygame.init()
    try:
        sim = Simulation()
        screen = pygame.display.set_mode((sim.grid.width * CELL + PANEL_W, sim.grid.height * CELL))
        pygame.display.set_caption("Depozit autonom | Simulator A*")
        font = pygame.font.SysFont("consolas", 15)
        clock = pygame.time.Clock()
        last_step = pygame.time.get_ticks()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_e:
                        sim.show_explored = not sim.show_explored
                    elif event.key == pygame.K_SPACE:
                        sim.paused = not sim.paused
                        last_step = pygame.time.get_ticks()
                    elif event.key == pygame.K_n and sim.paused:
                        sim.robot.step(sim.grid)
                    elif event.key == pygame.K_r:
                        sim.reset(bool(event.mod & pygame.KMOD_SHIFT))
                        last_step = pygame.time.get_ticks()
                    elif event.key in (pygame.K_UP, pygame.K_DOWN):
                        sim.change_speed(1 if event.key == pygame.K_UP else -1)
                        last_step = pygame.time.get_ticks()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    cell = cell_at(event.pos)
                    if not sim.grid.in_bounds(cell):
                        continue
                    if event.button == 1:
                        sim.edit(cell)
                    elif event.button == 3:
                        sim.robot.set_goal(sim.grid, cell)
                        last_step = pygame.time.get_ticks()

            now = pygame.time.get_ticks()
            if not sim.paused and now - last_step >= sim.step_ms:
                sim.robot.step(sim.grid)
                last_step = now
            draw(screen, font, sim.grid, sim.robot, sim.show_explored, sim.paused, sim.step_ms)
            pygame.display.flip()
            clock.tick(60)
    finally:
        pygame.quit()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Simulator de depozit autonom")
    parser.add_argument("--single", action="store_true", help="Demo original cu un robot")
    parser.add_argument("--robots", type=int, choices=range(3, 9), default=5, help="Numar de roboti (3–8)")
    parser.add_argument("--seed", type=int, default=42, help="Seed pentru comenzi reproductibile")
    parser.add_argument("--coordination", choices=("window", "conservative"), default="window", help="Algoritmul de coordonare a flotei")
    args = parser.parse_args()
    if args.single:
        main()
    else:
        from ui.fleet_ui import run

        run(robot_count=args.robots, seed=args.seed, coordination=args.coordination)
