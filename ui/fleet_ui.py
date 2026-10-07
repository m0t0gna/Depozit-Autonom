"""Comenzi Pygame pentru depozit; motorul si randarea raman independente."""
import pygame

from engine.fleet import Fleet
from engine.commands import TaskCommands
from engine.grid import Grid
from engine.astar import astar
from ui.retro_view import (CELL, HEADER, MAP_X, PANEL, SPEEDS, Animation, draw,
                        cell_at, window_size, roster_rects, button_rects, help_close_rect)


class DepotUI:
    def __init__(self, fleet, seed=42, now=0):
        self.fleet = fleet
        self.seed = seed
        self.selected = 1
        self.speed_index = 2
        self.paused = False
        self.auto = False
        self.show_paths = False
        self.tool = 'wall'
        self.show_help = False
        self.commands = TaskCommands(fleet)
        self.commands.message = 'Harta goala: W pentru pereti, T pentru cutii. Click pe harta pentru a le pune.'
        self.animation = Animation()
        self.animation.capture(fleet, SPEEDS[self.speed_index], now)
        self.last_step = now

    def select_robot(self, robot_id):
        self.selected = robot_id
        self.show_paths = True

    def advance(self, now):
        self.fleet.step()
        self.animation.capture(self.fleet, SPEEDS[self.speed_index] * .8, now)
        self.last_step = now

    def action(self, action, now):
        if action == 'pause':
            self.paused = not self.paused
            self.last_step = now
        elif action in ('task', 'wall'):
            self.tool = 'box' if action == 'task' else 'wall'
            self.commands.message = ('Click pe o celula libera pentru a pune o cutie. Robotul o duce la iesire.'
                                     if self.tool == 'box' else 'Click pentru a pune sau scoate un perete.')
        elif action == 'step' and self.paused:
            self.advance(now)
        elif action == 'help':
            self.show_help = not self.show_help
            self.last_step = now

    def key(self, event, now):
        key = event.key
        if self.show_help:
            if key in (pygame.K_h, pygame.K_ESCAPE):
                self.action('help', now)
            return True
        if key == pygame.K_ESCAPE:
            return False
        actions = {pygame.K_SPACE: 'pause', pygame.K_t: 'task', pygame.K_w: 'wall', pygame.K_n: 'step', pygame.K_h: 'help'}
        if key in actions:
            self.action(actions[key], now)
        elif key == pygame.K_c:
            self.commands.cancel()
        elif key in (pygame.K_UP, pygame.K_DOWN):
            self.speed_index = max(0, min(len(SPEEDS) - 1, self.speed_index + (1 if key == pygame.K_UP else -1)))
            self.last_step = now
        elif pygame.K_1 <= key <= pygame.K_8:
            self.select_robot(min(key - pygame.K_1 + 1, len(self.fleet.robots)))
        elif key == pygame.K_r:
            grid = Grid(self.fleet.grid.width, self.fleet.grid.height) if event.mod & pygame.KMOD_SHIFT else self.fleet.grid
            self.fleet = Fleet(robot_count=len(self.fleet.robots), seed=self.seed, grid=grid, pickups=list(self.fleet.pickups), dropoffs=list(self.fleet.dropoffs),
                               coordination=self.fleet.coordinator.name)
            self.commands = TaskCommands(self.fleet)
            self.commands.message = 'Tura noua. W: pereti. T: cutii. Shift+R: goleste harta.'
            self.animation = Animation()
            self.animation.capture(self.fleet, SPEEDS[self.speed_index], now)
            self.last_step = now
        return True

    def click(self, pos, button, mods, now):
        if self.show_help:
            if button == 1 and help_close_rect(self.fleet.grid).collidepoint(pos):
                self.action('help', now)
            return
        if button == 1:
            for action, rect in button_rects(self.fleet.grid).items():
                if rect.collidepoint(pos):
                    self.action(action, now)
                    return
            for robot_id, rect in roster_rects(self.fleet).items():
                if rect.collidepoint(pos):
                    self.select_robot(robot_id)
                    return
            # Selectia urmareste sprite-ul vizibil, inclusiv intre celulele logice.
            for robot in reversed(self.fleet.robots):
                point, _, _ = self.animation.position(robot, now)
                rect = pygame.Rect(round(MAP_X + point[0] * CELL), round(HEADER + point[1] * CELL), CELL, CELL)
                if rect.collidepoint(pos):
                    self.select_robot(robot.id)
                    return
        cell = cell_at(pos, self.fleet.grid)
        if cell is None:
            return
        if button == 1 and cell != self.commands.pickup:
            if self.tool == 'box':
                self.place_box(cell)
                return
            if self.fleet.edit(cell):
                self.commands.message = f'Raft {"adaugat" if cell in self.fleet.grid.blocked else "eliminat"} la {cell}.'
            else:
                self.commands.message = 'Loc protejat: robot, baza, statie sau capat de comanda.'
        elif button == 3:
            if mods & pygame.KMOD_SHIFT or self.commands.pickup is not None:
                self.commands.right_click(cell, custom=bool(mods & pygame.KMOD_SHIFT))
            else:
                self.place_box(cell)

    def place_box(self, cell):
        protected = {r.pos for r in self.fleet.robots} | {r.home for r in self.fleet.robots} | set(self.fleet.dropoffs)
        protected.update(t.pickup for t in self.fleet.tasks if t.status in ('pending', 'assigned'))
        if not self.fleet.grid.is_free(cell) or cell in protected:
            self.commands.message = 'Alege o celula libera, fara robot, cutie sau iesire.'
            return
        candidates = []
        for goal in self.fleet.dropoffs:
            path, _ = astar(self.fleet.grid, cell, goal)
            if path:
                candidates.append((len(path), goal))
        if not candidates:
            self.commands.message = 'Cutia nu are acces la o iesire. Scoate un perete si incearca din nou.'
            return
        _, goal = min(candidates)
        task = self.fleet.add_task(cell, goal)
        self.commands.message = f'Cutie #{task.id} pusa la {cell}. Un robot o va duce la iesire.'

    def update(self, now):
        if not self.paused and not self.show_help and now - self.last_step >= SPEEDS[self.speed_index]:
            self.advance(now)


def run(robot_count=5, seed=42, coordination='window'):
    pygame.init()
    try:
        fleet = Fleet(robot_count=robot_count, seed=seed, coordination=coordination, grid=Grid(30, 20), pickups=[])
        screen = pygame.display.set_mode(window_size(fleet.grid))
        pygame.display.set_caption('Micul Depozit | Atelier de robotei')
        from ui.pixel_art import robot_sprite
        pygame.display.set_icon(robot_sprite(0))
        font = pygame.font.SysFont('consolas', 15)
        clock = pygame.time.Clock()
        ui = DepotUI(fleet, seed, pygame.time.get_ticks())
        running = True
        while running:
            now = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    running = ui.key(event, now)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    ui.click(event.pos, event.button, pygame.key.get_mods(), now)
            if not running:
                break
            ui.update(now)
            draw(screen, font, ui.fleet, ui.selected, ui.paused, SPEEDS[ui.speed_index],
                 ui.auto, ui.show_paths, ui.commands.pickup, ui.commands.message,
                 now=now, animation=ui.animation,
                 hover=cell_at(pygame.mouse.get_pos(), ui.fleet.grid), show_help=ui.show_help, tool=ui.tool)
            pygame.display.flip()
            clock.tick(60)
    finally:
        pygame.quit()
