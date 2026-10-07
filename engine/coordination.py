"""Coordonare pe fereastra temporala cu rezolvarea conflictelor.

Cautarea de nivel inalt ramifica restrictii pentru primul conflict (CBS).
Bugetul este limitat; daca nu gaseste o solutie, foloseste coordonatorul
conservator. Nu exista garantie generala de progres cu orizont/buget finite.
"""
from collections import deque
import heapq
import itertools

from engine.astar import astar
from engine.grid import Grid


def distances(grid, goal):
    """Distante exacte fara roboti, folosite drept euristica spatiala."""
    result = {goal: 0}
    queue = deque([goal])
    while queue:
        cell = queue.popleft()
        for nxt in grid.neighbors(cell):
            if nxt not in result:
                result[nxt] = result[cell] + 1
                queue.append(nxt)
    return result


def timed_path(grid, start, goal, horizon, distance, vertices=frozenset(), edges=frozenset()):
    """A* pe (celula, timp), cu asteptare si rezervarea tintei pana la orizont.

Returneaza un traseu de horizon+1 pozitii si costul estimat. Daca tinta este
prea departe, returneaza un prefix spre ea. Restrictiile sunt (celula,t),
respectiv (sursa,destinatie,t_sosire).
"""
    if (start, 0) in vertices:
        return None
    counter = itertools.count()
    heap = [(distance.get(start, 0), next(counter), start, 0)]
    parent = {(start, 0): None}
    while heap:
        _, _, cell, time = heapq.heappop(heap)
        can_hold = cell == goal and all(
            (cell, t) not in vertices and (cell, cell, t) not in edges
            for t in range(time + 1, horizon + 1)
        )
        if can_hold or time == horizon:
            path = []
            state = (cell, time)
            while state is not None:
                path.append(state[0])
                state = parent[state]
            path.reverse()
            path.extend([cell] * (horizon + 1 - len(path)))
            return path, time + distance.get(cell, 0)
        for nxt in (*grid.neighbors(cell), cell):
            nt = time + 1
            state = (nxt, nt)
            if state in parent or (nxt, nt) in vertices or (cell, nxt, nt) in edges:
                continue
            parent[state] = (cell, time)
            heapq.heappush(heap, (nt + distance.get(nxt, 0), next(counter), nxt, nt))
    return None


def first_conflict(paths):
    """Primul conflict de celula sau muchie, in ordine determinista."""
    ids = sorted(paths)
    for t in range(1, len(paths[ids[0]])):
        for index, a in enumerate(ids):
            for b in ids[index + 1:]:
                if paths[a][t] == paths[b][t]:
                    return a, b, t, 'vertex'
                if paths[a][t - 1] == paths[b][t] and paths[b][t - 1] == paths[a][t]:
                    return a, b, t, 'edge'
    return None


def safe_joint_step(grid, before, after):
    if set(before) != set(after) or len(set(after.values())) != len(after):
        return False
    for a, start in before.items():
        end = after[a]
        if not grid.is_free(end) or abs(start[0] - end[0]) + abs(start[1] - end[1]) > 1:
            return False
        for b in before:
            if a != b and end == before[b] and after[b] == start:
                return False
    return True


class ConservativeCoordinator:
    """Comparator: rezervari doar pentru urmatorul tick."""
    name = 'conservative'

    def __init__(self):
        self.replans = 0
        self.fallbacks = 0

    def invalidate(self):
        pass

    def paths(self, grid, robots, tick):
        occupied = {r.pos for r in robots}
        reserved = set()
        plans = {}
        offset = (tick - 1) % len(robots)
        for robot in robots[offset:] + robots[:offset]:
            view = Grid(grid.width, grid.height)
            view.blocked = grid.blocked | (occupied - {robot.pos}) | reserved
            route, _ = astar(view, robot.pos, robot.goal) if robot.goal is not None else (None, [])
            route = route or [robot.pos]
            plans[robot.id] = route
            reserved.add(route[1] if len(route) > 1 else robot.pos)
        return plans


class WindowCoordinator:
    name = 'window'

    def __init__(self, horizon=12, max_nodes=80):
        if horizon < 1 or max_nodes < 1:
            raise ValueError('Orizontul si bugetul trebuie sa fie pozitive.')
        self.horizon = horizon
        self.max_nodes = max_nodes
        self.replans = 0
        self.fallbacks = 0
        self.expanded = 0
        self._signature = None
        self._paths = None
        self._fallback = ConservativeCoordinator()

    def invalidate(self):
        self._signature = None
        self._paths = None

    def paths(self, grid, robots, tick):
        signature = (grid.width, grid.height, frozenset(grid.blocked),
                     tuple((r.id, r.goal) for r in robots))
        if (signature == self._signature and self._paths
                and all(len(self._paths[r.id]) > 2 and self._paths[r.id][1] == r.pos for r in robots)):
            self._paths = {rid: path[1:] for rid, path in self._paths.items()}
            return self._paths
        self.replans += 1
        self._signature = signature
        self._paths = self._solve(grid, robots)
        if self._paths is None:
            self.fallbacks += 1
            self.invalidate()
            return self._fallback.paths(grid, robots, tick)
        return self._paths

    def _solve(self, grid, robots):
        by_id = {r.id: r for r in robots}
        # Robotii fara misiune raman stationari, inclusiv la finalul ferestrei.
        idle = {r.pos for r in robots if r.goal is None}
        view = Grid(grid.width, grid.height)
        view.blocked = grid.blocked | idle
        maps = {}
        goals = {}
        paths, costs = {}, {}
        for robot in robots:
            goal = robot.goal if robot.goal is not None else robot.pos
            distance = distances(view, goal)
            # Un scop deconectat spatial nu justifica o plimbare aleatorie.
            if robot.pos not in distance or goal in view.blocked:
                goal = robot.pos
                distance = distances(grid, goal)
            goals[robot.id], maps[robot.id] = goal, distance
            if robot.goal is None:
                paths[robot.id], costs[robot.id] = [robot.pos] * (self.horizon + 1), 0
            else:
                result = timed_path(view, robot.pos, goal, self.horizon, distance)
                if result is None:
                    return None
                paths[robot.id], costs[robot.id] = result
        counter = itertools.count()
        constraints = {r.id: (frozenset(), frozenset()) for r in robots}
        heap = [(sum(costs.values()), next(counter), paths, costs, constraints)]
        seen = set()
        for _ in range(self.max_nodes):
            if not heap:
                break
            _, _, paths, costs, constraints = heapq.heappop(heap)
            self.expanded += 1
            conflict = first_conflict(paths)
            if conflict is None:
                return paths
            a, b, time, kind = conflict
            for rid in (a, b):
                robot = by_id[rid]
                if robot.goal is None:
                    continue
                vertices, edges = constraints[rid]
                if kind == 'vertex':
                    vertices = vertices | {(paths[rid][time], time)}
                else:
                    edges = edges | {(paths[rid][time - 1], paths[rid][time], time)}
                child_constraints = dict(constraints)
                child_constraints[rid] = (vertices, edges)
                key = tuple((i, *child_constraints[i]) for i in sorted(child_constraints))
                if key in seen:
                    continue
                seen.add(key)
                result = timed_path(view, robot.pos, goals[rid], self.horizon, maps[rid], vertices, edges)
                if result is None:
                    continue
                child_paths, child_costs = dict(paths), dict(costs)
                child_paths[rid], child_costs[rid] = result
                heapq.heappush(heap, (sum(child_costs.values()), next(counter), child_paths, child_costs, child_constraints))
        return None
