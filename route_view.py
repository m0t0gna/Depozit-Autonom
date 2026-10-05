"""Traseu de afisare complet; nu modifica rezervarile coordonatorului."""
from functools import lru_cache
from astar import astar
from grid import Grid


@lru_cache(maxsize=128)
def _route(width, height, blocked, start, goal, planned):
    if goal is None or start == goal:
        return (), True
    grid = Grid(width, height)
    grid.blocked = set(blocked)
    route = [start]
    for cell in planned:
        if cell == route[-1]:
            continue  # Asteptarea nu este un segment geometric.
        if not grid.is_free(cell) or abs(cell[0] - route[-1][0]) + abs(cell[1] - route[-1][1]) != 1:
            route = [start]  # Plan invalidat de editarea hartii: refacem previzualizarea.
            break
        route.append(cell)
        if cell == goal:
            break
    if route[-1] != goal:
        tail, _ = astar(grid, route[-1], goal)
        if tail is None:
            return tuple(route), False
        route.extend(tail[1:])
    return tuple(route), True


def display_route(grid, robot):
    return _route(grid.width, grid.height, frozenset(grid.blocked), robot.pos,
                  robot.goal, tuple(robot.path))
