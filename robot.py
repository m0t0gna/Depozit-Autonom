"""robot.py - un robot care are o tinta, un drum planificat si un jurnal de decizii."""
from collections import deque

from astar import astar


class Robot:
    def __init__(self, name, pos):
        self.name = name
        self.pos = pos
        self.goal = None
        self.path = []                  # pasii ramasi (fara pozitia curenta)
        self.explored = []              # ce a explorat A* (doar pentru desen)
        self.log = deque(maxlen=12)     # ultimele mesaje, afisate in panou
        self.steps_taken = 0
        self.plans = 0

    @property
    def status(self):
        if self.goal is None:
            return "Asteapta o tinta"
        if self.pos == self.goal:
            return "Tinta atinsa"
        return "In miscare" if self.path else "Traseu blocat"

    def set_goal(self, grid, goal):
        if not grid.is_free(goal):
            self.log.append("Tinta invalida: alege o celula libera.")
            return
        self.goal = goal
        self.log.append(f"Tinta noua: {goal}")
        self.plan(grid)

    def plan(self, grid):
        """(Re)calculeaza drumul de la pozitia curenta la tinta."""
        if self.goal is None:
            return
        self.plans += 1
        path, self.explored = astar(grid, self.pos, self.goal)
        if path is None:
            self.path = []
            self.log.append("Nu exista drum catre tinta!")
        else:
            self.path = path[1:]        # path[0] e chiar pozitia curenta
            if not self.path:
                self.log.append("Am ajuns la tinta.")
                return
            self.log.append(f"Drum planificat: {len(self.path)} pasi "
                            f"({len(self.explored)} celule explorate)")

    def step(self, grid):
        """Un pas de simulare: muta robotul o celula pe drum."""
        if not self.path:
            return
        nxt = self.path[0]
        if not grid.is_free(nxt):       # plasa de siguranta: harta s-a schimbat
            self.log.append("Drum blocat, replanific...")
            self.plan(grid)
            return
        self.pos = self.path.pop(0)
        self.steps_taken += 1
        if not self.path:
            self.log.append("Am ajuns la tinta.")
