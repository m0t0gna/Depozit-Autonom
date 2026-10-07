"""Motor determinist de flota, independent de Pygame si de timpul real.

Coordonarea este separata in coordination.py: fereastra spatio-temporala
implicit, cu comparator conservator configurabil.
"""
from collections import deque
from dataclasses import dataclass, field
import random

from engine.astar import astar
from engine.coordination import ConservativeCoordinator, WindowCoordinator, safe_joint_step
from engine.allocators import GreedyAllocator, HungarianAllocator
from engine.grid import Grid, make_warehouse

Cell = tuple[int, int]


@dataclass
class Task:
    id: int
    pickup: Cell
    dropoff: Cell
    created_tick: int
    status: str = 'pending'
    robot_id: int | None = None
    assigned_tick: int | None = None
    picked_tick: int | None = None
    completed_tick: int | None = None


@dataclass
class FleetRobot:
    id: int
    pos: Cell
    home: Cell
    phase: str = 'idle'
    task_id: int | None = None
    goal: Cell | None = None
    path: list[Cell] = field(default_factory=list)
    explored: list[Cell] = field(default_factory=list)
    steps: int = 0
    wait_ticks: int = 0
    deliveries: int = 0
    wait_reason: str = ''
    consecutive_waits: int = 0

    @property
    def available(self):
        return self.task_id is None

    @property
    def carrying(self):
        return self.phase == 'delivering'


class Fleet:
    def __init__(self, robot_count=5, seed=42, *, grid=None, starts=None,
                 pickups=None, dropoffs=None, coordination='window', allocator='greedy'):
        if not 1 <= robot_count <= 8:
            raise ValueError('Flota trebuie sa aiba intre 1 si 8 roboti.')
        self.grid = grid if grid is not None else make_warehouse()
        starts = list(starts) if starts is not None else [(1 + 3 * i, 1) for i in range(robot_count)]
        self.pickups = list(pickups) if pickups is not None else [(4, 2), (12, 2), (20, 2), (4, 8), (12, 8), (20, 8)]
        self.dropoffs = list(dropoffs) if dropoffs is not None else [(28, 5), (28, 11), (28, 17)]
        if not starts or len(starts) > 8 or len(set(starts)) != len(starts):
            raise ValueError('Pozitiile initiale trebuie sa fie distincte (1–8 roboti).')
        if not self.dropoffs:
            raise ValueError('Este necesar cel putin un punct de livrare.')
        if not all(self.grid.is_free(c) for c in starts + self.pickups + self.dropoffs):
            raise ValueError('Pozitiile initiale si statiile trebuie sa fie accesibile.')
        self.robots = [FleetRobot(i + 1, pos, pos) for i, pos in enumerate(starts)]
        self.tasks: list[Task] = []
        self.tick = 0
        if coordination not in ('window', 'conservative'):
            raise ValueError('Coordonator necunoscut.')
        self.coordinator = WindowCoordinator() if coordination == 'window' else ConservativeCoordinator()
        self.allocator = HungarianAllocator() if allocator == 'hungarian' else GreedyAllocator()
        self.rng = random.Random(seed)
        self.log = deque(maxlen=80)
        self.log.append('Flota pregatita. T: comanda noua; A: generare automata.')

    def record(self, message):
        self.log.append(f'[{self.tick:04d}] {message}')

    @property
    def completed(self):
        return sum(t.status == 'completed' for t in self.tasks)

    @property
    def pending(self):
        return sum(t.status == 'pending' for t in self.tasks)

    def add_task(self, pickup, dropoff):
        if pickup == dropoff or not all(self.grid.is_free(c) for c in (pickup, dropoff)):
            raise ValueError('Comanda necesita doua celule libere distincte.')
        task = Task(len(self.tasks) + 1, pickup, dropoff, self.tick)
        self.tasks.append(task)
        self.record(f'Comanda #{task.id}: {pickup} -> {dropoff}.')
        return task

    def random_task(self):
        pairs = [(a, b) for a in self.pickups for b in self.dropoffs if a != b]
        if not pairs:
            raise ValueError('Nu exista perechi distincte de preluare/livrare.')
        return self.add_task(*self.rng.choice(pairs))

    def plan(self, robot, blocked=()):
        if robot.goal is None:
            robot.path = []
            return
        view = Grid(self.grid.width, self.grid.height)
        view.blocked = self.grid.blocked | set(blocked)
        view.blocked.discard(robot.pos)
        path, robot.explored = astar(view, robot.pos, robot.goal)
        robot.path = path[1:] if path else []

    def assign(self):
        self.allocator.assign(self)

    def _execute_assignment(self, robot, task):
        task.status, task.robot_id, task.assigned_tick = 'assigned', robot.id, self.tick
        robot.task_id, robot.phase, robot.goal = task.id, 'to_pickup', task.pickup
        robot.wait_reason = ''
        robot.consecutive_waits = 0
        self.plan(robot)
        self.record(f'Robot {robot.id} preia comanda #{task.id}.')

    def arrive(self, robot):
        if robot.pos != robot.goal:
            return
        if robot.phase == 'to_pickup':
            task = self.tasks[robot.task_id - 1]
            task.status, task.picked_tick = 'carrying', self.tick
            robot.phase, robot.goal = 'delivering', task.dropoff
            self.record(f'Robot {robot.id} a incarcat cutia #{task.id}.')
            self.plan(robot)
        elif robot.phase == 'delivering':
            task = self.tasks[robot.task_id - 1]
            task.status, task.completed_tick = 'completed', self.tick
            robot.deliveries += 1
            robot.task_id = None
            robot.phase, robot.goal = 'parking', robot.home
            self.record(f'Robot {robot.id} a livrat comanda #{task.id}.')
            self.plan(robot)
        elif robot.phase == 'parking':
            robot.phase, robot.goal, robot.path = 'idle', None, []
        robot.wait_reason = ''

    def step(self):
        self.tick += 1
        self.assign()
        # Schimbarile de faza se aplica inaintea planificarii comune.
        for robot in self.robots:
            self.arrive(robot)
        plans = self.coordinator.paths(self.grid, self.robots, self.tick)
        before = {r.id: r.pos for r in self.robots}
        after = {rid: path[1] if len(path) > 1 else path[0] for rid, path in plans.items()}
        # Ultima bariera de siguranta, independenta de algoritmul ales.
        if not safe_joint_step(self.grid, before, after):
            self.coordinator.invalidate()
            self.record('Plan comun invalid: flota oprita pentru siguranta.')
            after = before
            plans = {rid: [cell] for rid, cell in before.items()}
        for robot in self.robots:
            robot.path = list(plans[robot.id][2:])
            if after[robot.id] != robot.pos:
                robot.pos = after[robot.id]
                robot.steps += 1
                robot.consecutive_waits = 0
                robot.wait_reason = ''
            elif robot.goal is not None and robot.pos != robot.goal:
                robot.wait_ticks += 1
                robot.consecutive_waits += 1
                reason = 'rezervare de trafic sau traseu indisponibil'
                if reason != robot.wait_reason:
                    self.record(f'Robot {robot.id} asteapta: {reason}.')
                robot.wait_reason = reason
                if robot.consecutive_waits == 30:
                    self.record(f'Robot {robot.id}: 30 tick-uri fara progres; verifica accesul.')
            self.arrive(robot)

    def edit(self, cell):
        protected = set(self.pickups + self.dropoffs)
        protected.update(r.home for r in self.robots)
        protected.update(r.pos for r in self.robots)
        for task in self.tasks:
            if task.status != 'completed':
                protected.update((task.pickup, task.dropoff))
        if not self.grid.in_bounds(cell) or cell in protected:
            self.record('Editare refuzata: robot, statie sau punct de comanda.')
            return False
        self.grid.toggle(cell)
        self.coordinator.invalidate()
        self.record(f'Harta modificata la {cell}; replanificare flota.')
        for robot in self.robots:
            self.plan(robot)
        return True
