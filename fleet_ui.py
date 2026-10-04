"""Vizualizare Pygame pentru motorul de flota din fleet.py."""
import pygame

from fleet import Fleet
from commands import TaskCommands
from main import CELL, BG, FREE, WALL, TEXT, MUTED, SPEEDS, wrapped_lines

HEADER = 60
PANEL = 420
COLORS = [(73, 171, 255), (250, 184, 79), (184, 134, 255), (73, 218, 174),
          (255, 122, 157), (112, 214, 240), (219, 221, 104), (227, 163, 111)]
PHASES = {'idle': 'Liber', 'to_pickup': 'Spre preluare', 'delivering': 'Transporta', 'parking': 'Spre baza'}


def cell_at(pos, grid):
    cell = (pos[0] // CELL, (pos[1] - HEADER) // CELL)
    return cell if grid.in_bounds(cell) else None


def draw(screen, font, fleet, selected=1, paused=False, speed=120,
         auto=False, show_paths=True, pickup=None, message=''):
    screen.fill(BG)
    grid = fleet.grid
    px = grid.width * CELL

    def label(text, x, y, color=TEXT):
        screen.blit(font.render(text, True, color), (x, y))

    def center(cell):
        return cell[0] * CELL + CELL // 2, HEADER + cell[1] * CELL + CELL // 2

    label('DEPOZIT AUTONOM / FLOTA', 16, 12, COLORS[0])
    label(f'Tick {fleet.tick}   |   {"PAUZA" if paused else "ACTIV"}   |   {1000 / speed:.1f} pasi/sec', 16, 34, MUTED)
    label(f'Comenzi: {len(fleet.tasks)}   Livrate: {fleet.completed}   In asteptare: {fleet.pending}', 425, 23)
    for y in range(grid.height):
        for x in range(grid.width):
            rect = (x * CELL + 1, HEADER + y * CELL + 1, CELL - 2, CELL - 2)
            pygame.draw.rect(screen, WALL if (x, y) in grid.blocked else FREE, rect, border_radius=3)
    for i, cell in enumerate(fleet.pickups):
        pygame.draw.rect(screen, (116, 86, 34), (cell[0] * CELL + 2, HEADER + cell[1] * CELL + 2, CELL - 4, CELL - 4), border_radius=4)
        label(f'P{i + 1}', cell[0] * CELL + 5, HEADER + cell[1] * CELL + 7, COLORS[1])
    for i, cell in enumerate(fleet.dropoffs):
        pygame.draw.rect(screen, (27, 100, 77), (cell[0] * CELL + 2, HEADER + cell[1] * CELL + 2, CELL - 4, CELL - 4), border_radius=4)
        label(chr(65 + i), cell[0] * CELL + 10, HEADER + cell[1] * CELL + 7, COLORS[3])
    for robot in fleet.robots:
        color = COLORS[robot.id - 1]
        pygame.draw.circle(screen, color, center(robot.home), 11, 1)
        if show_paths and robot.path:
            pygame.draw.lines(screen, color, False, [center(robot.pos)] + [center(c) for c in robot.path], 2)
        if robot.goal is not None:
            pygame.draw.circle(screen, color, center(robot.goal), 12, 2)
    if pickup is not None:
        pygame.draw.circle(screen, TEXT, center(pickup), 14, 2)
    for robot in fleet.robots:
        cx, cy = center(robot.pos)
        color = COLORS[robot.id - 1]
        if robot.id == selected:
            pygame.draw.circle(screen, TEXT, (cx, cy), 14, 2)
        pygame.draw.circle(screen, color, (cx, cy), 10)
        label(str(robot.id), cx - 4, cy - 8, BG)
        if robot.carrying:
            pygame.draw.rect(screen, COLORS[1], (cx + 6, cy - 12, 8, 8))

    x = px + 18
    label('CONTROL FLOTA', x, 16, COLORS[0])
    label(f'{fleet.coordinator.name} | Auto: {"PORNIT" if auto else "OPRIT"}', x, 43, MUTED)
    label('ROBOTI / SARCINA / STARE', x, 80, MUTED)
    for i, robot in enumerate(fleet.robots):
        state = 'Asteapta' if robot.wait_reason else PHASES[robot.phase]
        task = f'#{robot.task_id}' if robot.task_id else '--'
        marker = '>' if robot.id == selected else ' '
        label(f'{marker} R{robot.id}  {task:5} {state:14} {robot.pos}', x, 106 + i * 25, COLORS[i])
    robot = fleet.robots[selected - 1]
    y = 118 + len(fleet.robots) * 25
    label(f'R{selected}: {robot.steps} pasi / {robot.deliveries} livrari', x, y)
    label(f'Asteptari: {robot.wait_ticks} tick-uri', x, y + 22, MUTED)
    if robot.task_id:
        task = fleet.tasks[robot.task_id - 1]
        label(f'#{task.id}: {task.pickup} -> {task.dropoff}', x, y + 44, COLORS[selected - 1])
    elif robot.goal:
        label(f'Revenire la baza {robot.goal}', x, y + 44, MUTED)
    y += 77
    for i, line in enumerate((
        'T: comanda noua  B: lot de 5  A: auto',
        'Dreapta: comanda catre destinatie',
        'Shift+dreapta: alege manual preluarea',
        'Stanga: obstacol / selectare robot',
        'Spatiu: pauza  N: pas  Sus/Jos: viteza',
        'P: trasee  1-8: selecteaza robot',
        'R: reset flota  Shift+R: reset total',
        'Esc: iesire  C: anuleaza preluarea',
    )):
        label(line, x, y + i * 21, MUTED)
    y += 185
    label('DECIZII RECENTE', x, y, COLORS[0])
    capacity = max(0, (screen.get_height() - y - 40) // 19)
    lines = []
    for log_message in reversed(fleet.log):
        message_lines = list(wrapped_lines(font, log_message, PANEL - 36))
        if len(lines) + len(message_lines) > capacity:
            break
        lines = message_lines + lines
    for i, line in enumerate(lines):
        label(line, x, y + 27 + i * 19, MUTED)
    footer = HEADER + grid.height * CELL + 12
    hint = f'Preluare {pickup}: alege destinatia. C: anulare.' if pickup else 'Un click dreapta = comanda | Shift+dreapta = preluare manuala | P1-P6: preluari; A-C: iesiri'
    label(message, 14, footer, COLORS[1])
    label(hint, 14, footer + 23, MUTED)


def run(robot_count=5, seed=42, coordination='window'):
    pygame.init()
    try:
        fleet = Fleet(robot_count=robot_count, seed=seed, coordination=coordination)
        for _ in range(5):
            fleet.random_task()
        screen = pygame.display.set_mode((fleet.grid.width * CELL + PANEL, HEADER + fleet.grid.height * CELL + 68))
        pygame.display.set_caption('Depozit autonom | Flota multi-robot')
        font = pygame.font.SysFont('consolas', 15)
        clock = pygame.time.Clock()
        selected, speed_index = 1, 2
        paused, auto, show_paths = False, False, True
        commands = TaskCommands(fleet)
        last_step = pygame.time.get_ticks()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    key = event.key
                    if key == pygame.K_ESCAPE:
                        running = False
                    elif key == pygame.K_SPACE:
                        paused = not paused
                        last_step = pygame.time.get_ticks()
                    elif key == pygame.K_n and paused:
                        fleet.step()
                        if auto and fleet.tick % 40 == 0 and fleet.pending < 20:
                            fleet.random_task()
                    elif key == pygame.K_t:
                        fleet.random_task()
                    elif key == pygame.K_b:
                        for _ in range(5):
                            fleet.random_task()
                    elif key == pygame.K_a:
                        auto = not auto
                    elif key == pygame.K_p:
                        show_paths = not show_paths
                    elif key == pygame.K_c:
                        commands.cancel()
                    elif key in (pygame.K_UP, pygame.K_DOWN):
                        speed_index = max(0, min(len(SPEEDS) - 1, speed_index + (1 if key == pygame.K_UP else -1)))
                        last_step = pygame.time.get_ticks()
                    elif pygame.K_1 <= key <= pygame.K_8:
                        selected = min(key - pygame.K_1 + 1, len(fleet.robots))
                    elif key == pygame.K_r:
                        grid = None if event.mod & pygame.KMOD_SHIFT else fleet.grid
                        fleet = Fleet(robot_count=robot_count, seed=seed, grid=grid, coordination=coordination)
                        commands = TaskCommands(fleet)
                        last_step = pygame.time.get_ticks()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    cell = cell_at(event.pos, fleet.grid)
                    if cell is None:
                        continue
                    if event.button == 1:
                        clicked = next((r for r in fleet.robots if r.pos == cell), None)
                        if clicked:
                            selected = clicked.id
                        elif cell != commands.pickup:
                            fleet.edit(cell)
                    elif event.button == 3:
                        commands.right_click(cell, custom=bool(pygame.key.get_mods() & pygame.KMOD_SHIFT))
            now = pygame.time.get_ticks()
            if not paused and now - last_step >= SPEEDS[speed_index]:
                fleet.step()
                if auto and fleet.tick % 40 == 0 and fleet.pending < 20:
                    fleet.random_task()
                last_step = now
            draw(screen, font, fleet, selected, paused, SPEEDS[speed_index], auto, show_paths, commands.pickup, commands.message)
            pygame.display.flip()
            clock.tick(60)
    finally:
        pygame.quit()
