"""Regresii pentru planificare si interactiunile simulatorului."""
from collections import deque
import random

import pytest

from astar import astar
from grid import Grid, make_warehouse
from main import Simulation, SPEEDS, START
from robot import Robot


@pytest.mark.parametrize('start,goal', [((-1, 0), (2, 2)), ((0, 0), (3, 0)), ((1, 1), (2, 2)), ((1, 1), (1, 1)), ((0, 0), (1, 1))])
def test_invalid_endpoints(start, goal):
    grid = Grid(3, 3)
    grid.blocked.add((1, 1))
    assert astar(grid, start, goal) == (None, [])


def test_optimal_paths_match_breadth_first_search():
    rng = random.Random(42)
    for _ in range(40):
        grid = Grid(8, 8)
        grid.blocked = {(x, y) for x in range(8) for y in range(8) if rng.random() < .3} - {(0, 0), (7, 7)}
        queue = deque([((0, 0), 0)])
        seen = {(0, 0)}
        distance = None
        while queue:
            cell, cost = queue.popleft()
            if cell == (7, 7):
                distance = cost
                break
            for neighbor in grid.neighbors(cell):
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append((neighbor, cost + 1))
        path, explored = astar(grid, (0, 0), (7, 7))
        assert len(explored) == len(set(explored))
        if distance is None:
            assert path is None
        else:
            assert len(path) - 1 == distance
            assert all(grid.is_free(cell) for cell in path)
            assert all(abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1 for a, b in zip(path, path[1:]))


def test_reopening_route_resumes_robot():
    sim = Simulation()
    sim.grid = Grid(5, 3)
    sim.grid.blocked = {(2, y) for y in range(3)}
    sim.robot.set_goal(sim.grid, (4, 1))
    assert sim.robot.status == 'Traseu blocat'
    sim.edit((2, 1))
    assert sim.robot.status == 'In miscare'
    for _ in range(3):
        sim.robot.step(sim.grid)
    assert sim.robot.pos == (4, 1)
    assert sim.robot.steps_taken == 3
    assert sim.robot.status == 'Tinta atinsa'


def test_obstacle_on_route_is_avoided():
    sim = Simulation()
    sim.grid = Grid(5, 4)
    sim.robot.set_goal(sim.grid, (4, 1))
    sim.edit((2, 1))
    assert (2, 1) not in sim.robot.path
    assert len(sim.robot.path) == 5


def test_robot_defensively_replans_before_entering_obstacle():
    grid = Grid(4, 3)
    robot = Robot('Test', (0, 0))
    robot.set_goal(grid, (3, 0))
    grid.blocked.add((1, 0))
    robot.step(grid)
    assert robot.pos == (0, 0)
    assert (1, 0) not in robot.path
    assert robot.plans == 2


def test_invalid_goal_preserves_current_mission():
    grid = Grid(4, 3)
    robot = Robot('Test', (0, 0))
    robot.set_goal(grid, (3, 0))
    previous = robot.path[:]
    robot.set_goal(grid, (-1, 0))
    assert robot.goal == (3, 0)
    assert robot.path == previous


def test_current_cell_goal_is_complete():
    robot = Robot('Test', (1, 1))
    robot.set_goal(Grid(3, 3), (1, 1))
    assert robot.status == 'Tinta atinsa'
    assert robot.path == []
    assert robot.steps_taken == 0


def test_reset_preserves_edits_and_full_reset_restores_warehouse():
    sim = Simulation()
    sim.edit((0, 0))
    sim.reset()
    assert (0, 0) in sim.grid.blocked
    assert sim.robot.pos == START
    assert sim.grid.is_free(START)
    sim.reset(restore_map=True)
    assert sim.grid.blocked == make_warehouse().blocked


def test_protected_cells_cannot_be_blocked():
    sim = Simulation()
    sim.robot.set_goal(sim.grid, (2, 1))
    sim.robot.step(sim.grid)
    sim.edit(START)
    sim.edit(sim.robot.pos)
    assert sim.grid.is_free(START)
    assert sim.grid.is_free(sim.robot.pos)


def test_speed_is_bounded():
    sim = Simulation()
    sim.change_speed(100)
    assert sim.step_ms == min(SPEEDS)
    sim.change_speed(-100)
    assert sim.step_ms == max(SPEEDS)


@pytest.mark.parametrize('width,height', [(1, 1), (12, 4), (30, 10)])
def test_small_warehouse_has_no_out_of_bounds_obstacles(width, height):
    grid = make_warehouse(width, height)
    assert all(grid.in_bounds(cell) for cell in grid.blocked)


def test_grid_rejects_empty_dimensions():
    with pytest.raises(ValueError):
        Grid(0, 3)
