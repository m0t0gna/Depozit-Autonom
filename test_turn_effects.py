from fleet import Fleet
from grid import Grid
from retro_view import Animation
from turn_effects import TurnDust, LIFETIME_MS, MAX_PUFFS


def setup():
    fleet = Fleet(robot_count=1, grid=Grid(30, 20), pickups=[])
    animation = Animation()
    animation.capture(fleet, 120, 0)
    return fleet, animation


def test_dust_only_after_real_direction_change():
    fleet, animation = setup()
    robot = fleet.robots[0]
    robot.pos = (2, 1)
    animation.capture(fleet, 120, 100)
    robot.pos = (3, 1)
    animation.capture(fleet, 120, 200)
    assert not animation.dust.puffs
    robot.pos = (3, 2)
    state = fleet.rng.getstate()
    animation.capture(fleet, 120, 300)
    assert len(animation.dust.puffs) == 3
    assert all(p[1] == (3, 1) for p in animation.dust.puffs)
    assert robot.pos == (3, 2) and robot.steps == 0
    assert fleet.rng.getstate() == state


def test_waiting_does_not_emit_but_keeps_last_movement_direction():
    fleet, animation = setup()
    robot = fleet.robots[0]
    robot.pos = (2, 1)
    animation.capture(fleet, 120, 100)
    for now in (200, 300, 400):
        animation.capture(fleet, 120, now)
    assert not animation.dust.puffs
    robot.pos = (2, 2)
    animation.capture(fleet, 120, 500)
    assert len(animation.dust.puffs) == 3
    animation.capture(fleet, 120, 510)
    assert len(animation.dust.puffs) == 3


def test_particles_expire_and_have_hard_memory_limit():
    dust = TurnDust()
    for _ in range(100):
        dust.emit((2, 2), (1, 0), (0, 1), 100)
    assert len(dust.puffs) == MAX_PUFFS
    dust.expire(100 + LIFETIME_MS)
    assert not dust.puffs


def test_teleport_and_reset_do_not_emit_dust():
    fleet, animation = setup()
    fleet.robots[0].pos = (2, 1)
    animation.capture(fleet, 120, 100)
    fleet.robots[0].pos = (10, 10)
    animation.capture(fleet, 120, 200)
    fleet.robots[0].pos = (10, 11)
    animation.capture(fleet, 120, 300)
    assert not animation.dust.puffs
    assert not Animation().dust.puffs
