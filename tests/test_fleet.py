"""Teste de comportament pentru alocare, transport si siguranta flotei."""
import pytest

from engine.fleet import Fleet
from engine.grid import Grid


def small(starts, width=7, height=5):
    return Fleet(grid=Grid(width, height), starts=starts,
                 pickups=[(2, 0)], dropoffs=[(width - 1, height - 1)])


def assert_safe_step(fleet):
    before = [r.pos for r in fleet.robots]
    fleet.step()
    after = [r.pos for r in fleet.robots]
    assert len(set(after)) == len(after), 'Coliziune in aceeasi celula'
    for i, (a, b) in enumerate(zip(before, after)):
        assert fleet.grid.is_free(b)
        assert abs(a[0] - b[0]) + abs(a[1] - b[1]) <= 1
        for j in range(i + 1, len(after)):
            assert not (b == before[j] and after[j] == a), 'Schimb frontal'


def test_assignment_uses_actual_path_distance():
    fleet = small([(0, 0), (4, 4)], width=5)
    fleet.grid.blocked.update((1, y) for y in range(4))
    task = fleet.add_task((2, 0), (4, 0))
    fleet.assign()
    assert task.robot_id == 2  # Robot 1 e aproape geometric, dar are un ocol mare.


def test_tie_breaking_is_deterministic():
    fleet = small([(0, 0), (4, 0)])
    task = fleet.add_task((2, 0), (6, 4))
    fleet.assign()
    assert task.robot_id == 1


def test_pickup_delivery_and_return_home():
    fleet = small([(0, 0)])
    task = fleet.add_task((2, 0), (4, 0))
    for _ in range(20):
        assert_safe_step(fleet)
    assert task.status == 'completed'
    assert task.created_tick <= task.assigned_tick <= task.picked_tick < task.completed_tick
    robot = fleet.robots[0]
    assert robot.pos == robot.home
    assert robot.phase == 'idle'
    assert robot.available and not robot.carrying
    assert robot.deliveries == 1
    assert robot.steps == 8


def test_busy_robot_does_not_receive_second_task():
    fleet = small([(0, 0)])
    first = fleet.add_task((2, 0), (4, 0))
    second = fleet.add_task((3, 0), (5, 0))
    fleet.assign()
    assert first.status == 'assigned'
    assert second.status == 'pending'
    for _ in range(30):
        assert_safe_step(fleet)
    assert fleet.completed == 2


def test_unreachable_task_does_not_consume_robot_or_block_other_tasks():
    fleet = small([(0, 0)])
    fleet.grid.blocked.update((3, y) for y in range(5))
    blocked = fleet.add_task((2, 0), (6, 0))
    reachable = fleet.add_task((1, 0), (2, 0))
    fleet.assign()
    assert blocked.status == 'pending'
    assert reachable.status == 'assigned'


def test_reopening_route_retries_pending_task():
    fleet = small([(0, 0)])
    fleet.grid.blocked.update((3, y) for y in range(5))
    task = fleet.add_task((2, 0), (6, 0))
    fleet.step()
    assert task.status == 'pending'
    assert fleet.edit((3, 0))
    for _ in range(20):
        assert_safe_step(fleet)
    assert task.status == 'completed'


def test_live_obstacle_forces_detour():
    fleet = small([(0, 0)])
    task = fleet.add_task((2, 0), (6, 0))
    fleet.step()
    assert fleet.edit((3, 0))
    for _ in range(25):
        assert_safe_step(fleet)
    assert task.status == 'completed'
    assert fleet.robots[0].steps > 12


def test_vertex_conflict_is_prevented():
    fleet = small([(0, 1), (2, 1)])
    for robot in fleet.robots:
        robot.phase, robot.goal = 'parking', (1, 1)
        fleet.plan(robot)
    assert_safe_step(fleet)
    assert sum(r.pos == (1, 1) for r in fleet.robots) == 1


def test_head_on_swap_waits_safely_in_narrow_corridor():
    fleet = Fleet(grid=Grid(4, 1), starts=[(1, 0), (2, 0)],
                  pickups=[(0, 0)], dropoffs=[(3, 0)])
    for robot, goal in zip(fleet.robots, [(2, 0), (1, 0)]):
        robot.phase, robot.goal = 'parking', goal
        fleet.plan(robot)
    for _ in range(5):
        assert_safe_step(fleet)
    assert [r.pos for r in fleet.robots] == [(1, 0), (2, 0)]
    assert all(r.wait_ticks == 5 for r in fleet.robots)
    # Limite connue: la siguranta nu implica rezolvarea deadlock-ului.


def test_station_home_robot_and_task_endpoints_are_protected():
    fleet = small([(0, 0)])
    task = fleet.add_task((1, 1), (5, 1))
    for cell in [fleet.robots[0].home, fleet.pickups[0], fleet.dropoffs[0], task.pickup, task.dropoff]:
        assert not fleet.edit(cell)
        assert fleet.grid.is_free(cell)


def test_invalid_task_leaves_queue_unchanged():
    fleet = small([(0, 0)])
    for a, b in [((0, 0), (0, 0)), ((-1, 0), (2, 0))]:
        with pytest.raises(ValueError):
            fleet.add_task(a, b)
    assert not fleet.tasks


@pytest.mark.parametrize('count', [3, 5, 8])
def test_demo_finishes_and_parks_without_collisions(count):
    fleet = Fleet(robot_count=count, seed=42)
    for _ in range(5):
        fleet.random_task()
    for _ in range(600):
        assert_safe_step(fleet)
    assert fleet.completed == 5
    assert all(r.pos == r.home and r.phase == 'idle' for r in fleet.robots)


@pytest.mark.parametrize('seed', [7, 19, 42])
def test_generated_traffic_remains_safe_with_live_edits(seed):
    fleet = Fleet(robot_count=8, seed=seed)
    for tick in range(300):
        if tick % 25 == 0:
            fleet.random_task()
        if tick in (50, 150):
            fleet.edit((15, 7))
        assert_safe_step(fleet)


def test_seed_reproduces_tasks_and_motion():
    a, b = Fleet(seed=17), Fleet(seed=17)
    for tick in range(100):
        if tick % 20 == 0:
            a.random_task()
            b.random_task()
        a.step()
        b.step()
        assert a.tasks == b.tasks
        assert a.robots == b.robots
        assert list(a.log) == list(b.log)


@pytest.mark.parametrize('count', [0, 9])
def test_rejects_invalid_fleet_size(count):
    with pytest.raises(ValueError):
        Fleet(robot_count=count)


def test_rejects_overlapping_starts():
    with pytest.raises(ValueError):
        small([(0, 0), (0, 0)])
