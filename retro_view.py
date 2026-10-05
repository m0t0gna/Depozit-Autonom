"""Randare retro a flotei; geometrie comuna pentru desenare si interactiuni."""
import pygame
from route_view import display_route
from turn_effects import TurnDust
from atelier_decor import workshop_floor, desk_plant
from pixel_art import (INK, PAPER, CREAM, MUTED, LINE, TEAL, TERRA, COLORS, NAMES,
                       robot_sprite, tile_sprite, pixel_text, crate_sprite)

CELL, HEADER, MAP_X, PANEL = 30, 88, 20, 380
SPEEDS = (500, 250, 120, 60, 30)
PHASES = {'idle': 'La baza', 'to_pickup': 'Preia colet', 'delivering': 'Livreaza', 'parking': 'Spre baza'}


def window_size(grid):
    return grid.width * CELL + MAP_X * 2 + PANEL, max(810, HEADER + grid.height * CELL + 122)


def cell_at(pos, grid):
    cell = ((pos[0] - MAP_X) // CELL, (pos[1] - HEADER) // CELL)
    return cell if grid.in_bounds(cell) else None


def roster_rects(fleet):
    x = MAP_X + fleet.grid.width * CELL + 24
    count = len(fleet.robots)
    width = (340 - (count - 1) * 6) // count
    return {r.id: pygame.Rect(x + (r.id - 1) * (width + 6), 132, width, 62)
            for r in fleet.robots}



def button_rects(grid):
    names = ('pause', 'wall', 'task', 'step', 'help')
    width = (grid.width * CELL - 32) // 5
    y = HEADER + grid.height * CELL + 20
    return {name: pygame.Rect(MAP_X + i * (width + 8), y, width, 34) for i, name in enumerate(names)}


def help_rect(grid):
    width, height = window_size(grid)
    return pygame.Rect((width - 660) // 2, (height - 520) // 2, 660, 520)


def help_close_rect(grid):
    rect = help_rect(grid)
    return pygame.Rect(rect.right - 46, rect.top + 14, 30, 28)


def wrapped_lines(font, text, width):
    line = ''
    for word in text.split():
        candidate = f'{line} {word}'.strip()
        if line and font.size(candidate)[0] > width:
            yield line
            line = word
        else:
            line = candidate
    if line:
        yield line


class Animation:
    """Orientare/interpolare vizuala. Pozitiile logice raman intregi."""
    def __init__(self):
        self.frames = {}
        self.dust = TurnDust()

    def capture(self, fleet, duration, now):
        self.dust.expire(now)
        for robot in fleet.robots:
            old = self.frames.get(robot.id)
            start = old['end'] if old else robot.pos
            dx, dy = robot.pos[0] - start[0], robot.pos[1] - start[1]
            direction = (dx, dy)
            previous = old.get('direction') if old else None
            if abs(dx) + abs(dy) == 1:
                if previous is not None and previous != direction:
                    self.dust.emit(start, previous, direction, now)
            elif dx == dy == 0:
                direction = previous
            else:
                direction = None  # Teleport/reset: nu este un viraj.
            facing = ('right' if dx > 0 else 'left') if dx else ('down' if dy > 0 else 'up') if dy else (old['facing'] if old else 'down')
            self.frames[robot.id] = dict(start=start, end=robot.pos, time=now,
                                        duration=duration, facing=facing, direction=direction)

    def position(self, robot, now):
        frame = self.frames.get(robot.id)
        if frame is None or frame['end'] != robot.pos:
            return robot.pos, 'down', False
        amount = min(1.0, max(0.0, (now - frame['time']) / max(1, frame['duration'])))
        a, b = frame['start'], frame['end']
        return (a[0] + (b[0] - a[0]) * amount, a[1] + (b[1] - a[1]) * amount), frame['facing'], a != b and amount < 1


def panel(screen, rect, fill=CREAM):
    pygame.draw.rect(screen, LINE, rect.move(3, 4))
    pygame.draw.rect(screen, INK, rect)
    pygame.draw.rect(screen, fill, rect.inflate(-4, -4))


def draw(screen, font, fleet, selected=1, paused=False, speed=120,
         auto=False, show_paths=False, pickup=None, message='', *, now=0,
         animation=None, hover=None, show_help=False, tool='wall'):
    screen.fill(PAPER)
    grid = fleet.grid
    right = MAP_X + grid.width * CELL
    selected_robot = fleet.robots[selected - 1]

    def label(text, x, y, color=INK):
        screen.blit(font.render(text, False, color), (x, y))

    def heading(text, x, y, color=INK, scale=2):
        screen.blit(pixel_text(text, scale, color), (x, y))

    def center(cell):
        return MAP_X + cell[0] * CELL + 15, HEADER + cell[1] * CELL + 15

    # Antet de atelier, hartie si cerneala; fara fonturi externe.
    screen.blit(robot_sprite(0, 3), (20, 15))
    heading('MICUL DEPOZIT', 80, 18, TEAL, 3)
    label('Colectiv de robotei / serviciul de colete', 82, 49, MUTED)
    for x, value, caption in ((508, f'{fleet.completed:02d}', 'LIVRATE'),
                              (652, f'{fleet.pending:02d}', 'IN ASTEPTARE'),
                              (820, f'{len(fleet.robots):02d}', 'ROBOTEI')):
        heading(value, x, 18, TEAL, 3)
        label(caption, x, 48, MUTED)
    label('TURA DE LUCRU', right + 24, 18, MUTED)
    heading('PAUZA' if paused or show_help else 'IN MISCARE' if any(r.goal for r in fleet.robots) else 'PREGATIT', right + 24, 41, TERRA if paused else TEAL)
    pygame.draw.line(screen, LINE, (20, 72), (screen.get_width() - 20, 72), 2)

    # Podea discreta si rafturi din lemn; fiecare celula reflecta harta reala.
    map_rect = pygame.Rect(MAP_X - 4, HEADER - 4, grid.width * CELL + 8, grid.height * CELL + 8)
    panel(screen, map_rect, LINE)
    floor = workshop_floor(grid.width, grid.height, tuple(r.home for r in fleet.robots), tuple(fleet.dropoffs))
    screen.blit(floor, (MAP_X, HEADER))
    for x, y in grid.blocked:
        screen.blit(tile_sprite('wall'), (MAP_X + x * CELL, HEADER + y * CELL))
    for robot in fleet.robots:
        x, y = robot.home
        screen.blit(tile_sprite('home'), (MAP_X + x * CELL, HEADER + y * CELL))
    for kind, cells in (('pickup', fleet.pickups), ('dropoff', fleet.dropoffs)):
        for i, (x, y) in enumerate(cells):
            screen.blit(tile_sprite(kind), (MAP_X + x * CELL, HEADER + y * CELL))
            tag = f'P{i + 1}' if kind == 'pickup' else chr(65 + i)
            badge = pixel_text(tag, 1, CREAM)
            pygame.draw.rect(screen, INK, (MAP_X + x * CELL, HEADER + y * CELL, badge.get_width() + 4, 9))
            screen.blit(badge, (MAP_X + x * CELL + 2, HEADER + y * CELL + 1))
    # Cutii reale de transport, vizibile pana la preluarea de catre robot.
    for task in fleet.tasks:
        if task.status in ('pending', 'assigned'):
            x, y = task.pickup
            screen.blit(crate_sprite(), (MAP_X + x * CELL, HEADER + y * CELL))
    # Pastram ordinea traseului, inclusiv ocolirile; completam orizontul scurt.
    route, reachable = display_route(grid, selected_robot) if show_paths else ((), True)
    if route and len(route) > 1:
        pos = animation.position(selected_robot, now)[0] if animation else selected_robot.pos
        points = [center(pos)] + [center(c) for c in route]
        pygame.draw.lines(screen, CREAM, False, points, 8)
        pygame.draw.lines(screen, TEAL, False, points, 4)
        if reachable:
            gx, gy = center(route[-1])
            pygame.draw.rect(screen, TEAL, (gx - 9, gy - 9, 18, 18), 2)
            pygame.draw.rect(screen, CREAM, (gx - 4, gy - 4, 8, 8))
    if hover is not None and grid.in_bounds(hover):
        hx, hy = center(hover)
        pygame.draw.rect(screen, TEAL if grid.is_free(hover) else TERRA, (hx - 14, hy - 14, 28, 28), 2)
    if pickup is not None:
        hx, hy = center(pickup)
        pygame.draw.rect(screen, TERRA, (hx - 14, hy - 14, 28, 28), 3)
    if animation is not None:
        previous_clip = screen.get_clip()
        screen.set_clip(pygame.Rect(MAP_X, HEADER, grid.width * CELL, grid.height * CELL).clip(previous_clip))
        animation.dust.draw(screen, now, (MAP_X, HEADER), CELL)
        screen.set_clip(previous_clip)
    for robot in fleet.robots:
        pos, facing, moving = animation.position(robot, now) if animation else (robot.pos, 'down', False)
        cx, cy = center(pos)
        # Sprite-ul ramane aliniat pe pixeli intregi in timpul miscarii.
        px, py = round(cx - 15), round(cy - 15)
        blink = (now // 130 + robot.id * 9) % 37 == 0
        stride = now // 90 % 2 if moving else 0
        screen.blit(robot_sprite(robot.id - 1, facing=facing, blink=blink, stride=stride, carrying=robot.carrying), (px, py))
        if robot.id == selected:
            for dx, dy, w, h in ((-16, -16, 7, 2), (-16, -16, 2, 7), (9, 14, 7, 2), (14, 9, 2, 7)):
                pygame.draw.rect(screen, TEAL, (round(cx + dx), round(cy + dy), w, h))

    # Fisele echipei pot fi selectate inclusiv cand exista opt roboti.
    sx = right + 24
    heading('ECHIPA DE TURA', sx, 94, TEAL)
    label('Selecteaza iconita pentru traseu', sx, 114, MUTED)
    for robot in fleet.robots:
        rect = roster_rects(fleet)[robot.id]
        active = robot.id == selected and show_paths
        panel(screen, rect, (204, 224, 193) if active else CREAM)
        screen.blit(robot_sprite(robot.id - 1, carrying=robot.carrying), (rect.centerx - 15, rect.y + 5))
        name = pixel_text(NAMES[robot.id - 1], 1, TEAL if active else INK)
        screen.blit(name, (rect.centerx - name.get_width() // 2, rect.y + 44))
    label('Click pe un robot: vezi traseul sau.', sx, 205, MUTED)
    y = 243
    heading(f'{NAMES[selected - 1]} / FISA DE LUCRU', sx, y, TEAL)
    screen.blit(robot_sprite(selected - 1, 4, carrying=selected_robot.carrying), (sx, y + 26))
    label(f'{selected_robot.deliveries} colete livrate', sx + 74, y + 26)
    label(f'{selected_robot.steps} pasi parcursi', sx + 74, y + 48, MUTED)
    label(f'{selected_robot.wait_ticks} asteptari', sx + 74, y + 70, MUTED)
    if selected_robot.task_id:
        task = fleet.tasks[selected_robot.task_id - 1]
        label(f'Colet #{task.id}: {task.pickup} > {task.dropoff}', sx, y + 99)
    else:
        label('Gata pentru urmatorul colet.', sx, y + 99, MUTED)
    if show_paths:
        note = 'La baza: niciun traseu activ.' if selected_robot.goal is None else 'Tinta inaccesibila: verifica peretii.' if not reachable else 'Ruta orientativa; traficul o poate ajusta.'
        label(note, sx, y + 120, MUTED)
    y += 153
    heading('BONURI DE TRANSPORT', sx, y, TERRA)
    visible_tasks = [t for t in fleet.tasks if t.status != 'completed'][:3]
    if not visible_tasks:
        pygame.draw.rect(screen, (233, 221, 194), (sx, y + 25, 338, 62))
        label('Nicio cutie in asteptare.', sx + 12, y + 35, INK)
        label('Alege CUTII, apoi un loc pe harta.', sx + 12, y + 58, MUTED)
    for i, task in enumerate(visible_tasks):
        yy = y + 24 + i * 23
        pygame.draw.rect(screen, LINE, (sx, yy + 3, 9, 9), 1)
        label(f'#{task.id:03d}  {task.pickup} > {task.dropoff}', sx + 18, yy)
        # Patratul plin marcheaza comenzile inca nealocate.
        if task.status == 'pending':
            pygame.draw.rect(screen, TERRA, (sx + 2, yy + 5, 5, 5))
    y += 108
    heading('CONSTRUIESTE DEPOZITUL', sx, y, TEAL)
    screen.blit(desk_plant(), (sx + 304, y - 19))
    for i, line in enumerate(('W: alege pereti. Click: pune/scoate.',
                              'T: alege cutii. Click: pune o cutie.',
                              'Click pe robot: selecteaza.',
                              'Shift+R: goleste harta.',
                              'H: toate comenzile.')):
        label(line, sx, y + 25 + i * 22, MUTED)

    texts = {'pause': 'CONTINUA' if paused else 'PAUZA', 'task': 'CUTII [T]',
             'wall': 'PERETI [W]',
             'step': 'UN PAS [N]', 'help': 'AJUTOR [H]'}
    for action, rect in button_rects(grid).items():
        active = (action == 'pause' and paused) or (action == 'wall' and tool == 'wall') or (action == 'task' and tool == 'box')
        panel(screen, rect, (218, 230, 205) if active else CREAM)
        text = texts[action]
        label(text, rect.centerx - font.size(text)[0] // 2, rect.y + 9,
              MUTED if action == 'step' and not paused else INK)
    footer = HEADER + grid.height * CELL + 66
    feedback = message or 'Harta goala. Alege PERETI sau CUTII si apasa pe harta.'
    for i, line in enumerate(wrapped_lines(font, feedback, grid.width * CELL)):
        if i == 2:
            break
        label(line, MAP_X, footer + i * 17, TEAL)
    label(f'Tick {fleet.tick:05d}   {1000 / speed:.1f} pasi/sec   |   Sus/Jos: viteza   |   Shift+dreapta: preluare manuala', MAP_X, footer + 38, MUTED)
    if show_help:
        veil = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        veil.fill((55, 48, 43, 125))
        screen.blit(veil, (0, 0))
        rect = help_rect(grid)
        panel(screen, rect)
        heading('BUN VENIT IN ATELIER', rect.x + 28, rect.y + 28, TEAL)
        label('Simularea asteapta cat timp citesti.', rect.x + 28, rect.y + 57, MUTED)
        rows = (
            ('CLICK DREAPTA', 'Pune o cutie cu livrare automata.'),
            ('SHIFT + DREAPTA', 'Alege preluarea, apoi click pe destinatie.'),
            ('CLICK STANGA', 'Foloseste unealta sau selecteaza robotul.'),
            ('SPATIU / N', 'Pauza / un pas cand este pe pauza.'),
            ('W / T', 'Alege unealta pereti / cutii.'),
            ('ICONITE / 1-8', 'Selecteaza robotul si vezi traseul lui.'),
            ('SUS / JOS', 'Regleaza viteza de lucru.'),
            ('R / SHIFT + R', 'Reset flota / reset inclusiv harta.'),
            ('C / H / ESC', 'Anuleaza preluarea / ajutor / inchide.'),
        )
        for i, (key, detail) in enumerate(rows):
            yy = rect.y + 103 + i * 36
            label(key, rect.x + 28, yy, TEAL)
            label(detail, rect.x + 202, yy)
        label('A-C: iesiri   Pad verde: baza robotului', rect.x + 28, rect.bottom - 52, MUTED)
        close = help_close_rect(grid)
        panel(screen, close)
        label('X', close.x + 10, close.y + 6)
