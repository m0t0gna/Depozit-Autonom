from fleet import Fleet, FleetRobot
from fleet_ui import DepotUI
from grid import Grid
from route_view import display_route
from retro_view import roster_rects, button_rects


def test_short_planning_window_is_extended_to_goal():
    grid = Grid(30, 4)
    robot = FleetRobot(1, (1, 1), (1, 1), goal=(28, 1), path=[(2, 1), (3, 1)])
    route, reachable = display_route(grid, robot)
    assert reachable and route[0] == robot.pos and route[-1] == robot.goal
    assert len(route) == 28
    assert robot.path == [(2, 1), (3, 1)]


def test_waits_collapse_but_backtracking_keeps_order():
    robot = FleetRobot(1, (0, 0), (0, 0), goal=(3, 0),
                       path=[(0, 0), (1, 0), (1, 1), (1, 0), (2, 0)])
    route, reachable = display_route(Grid(4, 3), robot)
    assert reachable
    assert route == ((0, 0), (1, 0), (1, 1), (1, 0), (2, 0), (3, 0))


def test_route_refreshes_when_wall_invalidates_old_path():
    grid = Grid(5, 3)
    robot = FleetRobot(1, (0, 0), (0, 0), goal=(4, 0), path=[(1, 0), (2, 0)])
    display_route(grid, robot)
    grid.blocked.add((2, 0))
    route, reachable = display_route(grid, robot)
    assert reachable and (2, 0) not in route
    assert route[-1] == robot.goal
    assert all(abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1 for a, b in zip(route, route[1:]))


def test_idle_and_unreachable_routes_are_explicit():
    robot = FleetRobot(1, (0, 0), (0, 0))
    grid = Grid(3, 1)
    assert display_route(grid, robot) == ((), True)
    robot.goal = (2, 0)
    grid.blocked.add((1, 0))
    route, reachable = display_route(grid, robot)
    assert not reachable and route == ((0, 0),)


def test_icon_selection_shows_only_selected_robot_and_no_paths_button():
    ui = DepotUI(Fleet())
    assert len(roster_rects(ui.fleet)) == 5
    assert 'paths' not in button_rects(ui.fleet.grid)
    assert not ui.show_paths
    for rid in (2, 5, 1):
        ui.click(roster_rects(ui.fleet)[rid].center, 1, 0, 0)
        assert ui.selected == rid and ui.show_paths


def test_running_robot_route_always_reaches_current_goal():
    fleet = Fleet(grid=Grid(30, 20), pickups=[])
    fleet.add_task((15, 7), (28, 17))
    for _ in range(60):
        fleet.step()
        for robot in fleet.robots:
            route, reachable = display_route(fleet.grid, robot)
            if robot.goal is not None and robot.pos != robot.goal:
                assert reachable
                assert route[0] == robot.pos and route[-1] == robot.goal
