"""Regresii pentru rezervari in timp, siguranta si progres."""
from coordination import WindowCoordinator, distances, timed_path, safe_joint_step
from fleet import Fleet, FleetRobot
from grid import Grid
from test_fleet import assert_safe_step


def test_space_time_waits_for_reserved_cell():
    grid = Grid(3, 1)
    path, _ = timed_path(grid, (0, 0), (2, 0), 5, distances(grid, (2, 0)),
                         vertices=frozenset({((1, 0), 1)}))
    assert path[:4] == [(0, 0), (0, 0), (1, 0), (2, 0)]
    assert len(path) == 6


def test_space_time_avoids_forbidden_edge():
    grid = Grid(3, 1)
    path, _ = timed_path(grid, (0, 0), (2, 0), 5, distances(grid, (2, 0)),
                         edges=frozenset({((0, 0), (1, 0), 1)}))
    assert path[1] == (0, 0)
    assert path[-1] == (2, 0)


def test_goal_must_remain_safe_after_arrival():
    grid = Grid(3, 1)
    path, _ = timed_path(grid, (0, 0), (1, 0), 5, distances(grid, (1, 0)),
                         vertices=frozenset({((1, 0), 3)}))
    assert path[3] != (1, 0)
    assert path[-1] == (1, 0)


def test_horizon_prefix_makes_progress_to_distant_goal():
    grid = Grid(20, 1)
    path, _ = timed_path(grid, (0, 0), (19, 0), 4, distances(grid, (19, 0)))
    assert path == [(x, 0) for x in range(5)]


def test_corridor_with_refuge_resolves_opposing_robots():
    grid = Grid(5, 3)
    grid.blocked = {(x, y) for x in range(5) for y in range(3) if y != 1 and (x, y) != (2, 0)}
    fleet = Fleet(grid=grid, starts=[(0, 1), (4, 1)], pickups=[(0, 1)], dropoffs=[(4, 1)])
    for robot, goal in zip(fleet.robots, [(4, 1), (0, 1)]):
        robot.phase, robot.goal = 'parking', goal
    used_refuge = False
    for _ in range(12):
        assert_safe_step(fleet)
        used_refuge |= any(r.pos == (2, 0) for r in fleet.robots)
    assert used_refuge
    assert [r.pos for r in fleet.robots] == [(4, 1), (0, 1)]
    assert fleet.coordinator.fallbacks == 0


def test_same_direction_robots_can_follow_in_one_tick():
    grid = Grid(7, 1)
    robots = [FleetRobot(1, (1, 0), (1, 0), goal=(5, 0)),
              FleetRobot(2, (0, 0), (0, 0), goal=(4, 0))]
    planner = WindowCoordinator()
    paths = planner.paths(grid, robots, 1)
    assert [paths[r.id][1] for r in robots] == [(2, 0), (1, 0)]
    assert safe_joint_step(grid, {r.id: r.pos for r in robots}, {r.id: paths[r.id][1] for r in robots})


def test_map_edit_discards_cached_reservations():
    fleet = Fleet()
    fleet.add_task((4, 2), (28, 5))
    fleet.step()
    moving = next(r for r in fleet.robots if r.task_id)
    cell = next(c for c in moving.path if c not in (moving.pos, moving.goal, moving.home)
                and c not in fleet.pickups + fleet.dropoffs and c not in [r.home for r in fleet.robots])
    assert fleet.edit(cell)
    for _ in range(70):
        assert_safe_step(fleet)
    assert fleet.completed == 1


def test_idle_robot_is_reserved_for_entire_window():
    grid = Grid(5, 3)
    robots = [FleetRobot(1, (2, 1), (2, 1)), FleetRobot(2, (0, 1), (0, 1), goal=(4, 1))]
    paths = WindowCoordinator().paths(grid, robots, 1)
    assert set(paths[1]) == {(2, 1)}
    assert (2, 1) not in paths[2]
    assert paths[2][-1] == (4, 1)


def test_budget_fallback_is_collision_free():
    grid = Grid(3, 3)
    robots = [FleetRobot(1, (0, 1), (0, 1), goal=(2, 1)),
              FleetRobot(2, (1, 0), (1, 0), goal=(1, 2))]
    planner = WindowCoordinator(max_nodes=1)
    paths = planner.paths(grid, robots, 1)
    assert planner.fallbacks == 1
    assert safe_joint_step(grid, {r.id: r.pos for r in robots},
                           {rid: p[1] if len(p) > 1 else p[0] for rid, p in paths.items()})


def test_safety_barrier_rejects_invalid_moves():
    grid = Grid(4, 2)
    before = {1: (0, 0), 2: (1, 0)}
    assert not safe_joint_step(grid, before, {1: (1, 0), 2: (0, 0)})
    assert not safe_joint_step(grid, before, {1: (1, 0), 2: (1, 0)})
    assert not safe_joint_step(grid, before, {1: (3, 0), 2: (1, 0)})
