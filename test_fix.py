from engine.grid import make_warehouse, Grid
from engine.coordination import WindowCoordinator
import engine.robot as robot_mod
from engine.fleet import FleetRobot
from engine.astar import astar

class FixedConservativeCoordinator:
    name = 'conservative'
    def __init__(self):
        self.replans = 0
        self.fallbacks = 0
    def invalidate(self): pass
    def paths(self, grid, robots, tick):
        occupied = {r.pos for r in robots}
        reserved = set()
        plans = {}
        offset = (tick - 1) % len(robots)
        for robot in robots[offset:] + robots[:offset]:
            view = Grid(grid.width, grid.height)
            blocked_for_astar = grid.blocked | (occupied - {robot.pos}) | reserved
            if robot.goal in blocked_for_astar:
                blocked_for_astar.remove(robot.goal)
            view.blocked = blocked_for_astar
            route, _ = astar(view, robot.pos, robot.goal) if robot.goal is not None else (None, [])
            if route and len(route) > 1:
                actual_blocked = grid.blocked | (occupied - {robot.pos}) | reserved
                if route[1] in actual_blocked:
                    route = [robot.pos]
            else:
                route = [robot.pos]
            plans[robot.id] = route
            if len(route) > 1:
                reserved.add(route[1])
            else:
                reserved.add(robot.pos)
        return plans

class MockRobot:
    def __init__(self, id, pos, goal):
        self.id, self.pos, self.goal = id, pos, goal

grid = make_warehouse()
robots = [
    MockRobot(1, (28, 17), (20, 8)),
    MockRobot(2, (28, 2), (28, 5)),
    MockRobot(3, (26, 9), (20, 8)),
    MockRobot(4, (22, 8), (20, 8)),
    MockRobot(5, (20, 8), (28, 17)),
    MockRobot(6, (28, 5), (20, 8)),
    MockRobot(7, (19, 9), (20, 8)),
    MockRobot(8, (28, 10), (28, 17)),
]

coord = FixedConservativeCoordinator()
paths = coord.paths(grid, robots, 150)
for i, p in paths.items(): print(i, p)
