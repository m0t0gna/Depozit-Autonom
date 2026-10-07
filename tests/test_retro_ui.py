"""Regresii pentru interactiunile UI-ului retro, nu pentru detalii de desen."""
import pytest
import pygame

from engine.fleet import Fleet
from ui.fleet_ui import DepotUI
from ui.retro_view import (CELL, MAP_X, HEADER, cell_at, button_rects,
                        roster_rects, help_close_rect, window_size, Animation)


def center(cell):
    return MAP_X + cell[0] * CELL + CELL // 2, HEADER + cell[1] * CELL + CELL // 2


def test_map_coordinates_exclude_header_margins_and_buttons():
    fleet = Fleet()
    assert cell_at(center((0, 0)), fleet.grid) == (0, 0)
    assert cell_at(center((29, 19)), fleet.grid) == (29, 19)
    for point in ((MAP_X - 1, HEADER), (MAP_X, HEADER - 1),
                  (MAP_X + 900, HEADER), button_rects(fleet.grid)['pause'].center):
        assert cell_at(point, fleet.grid) is None


def test_mouse_buttons_pause_step_and_create_task_without_editing_map():
    ui = DepotUI(Fleet())
    before = ui.fleet.grid.blocked.copy()
    buttons = button_rects(ui.fleet.grid)
    ui.click(buttons['step'].center, 1, 0, 10)
    assert ui.fleet.tick == 0
    ui.click(buttons['pause'].center, 1, 0, 20)
    assert ui.paused
    ui.click(buttons['step'].center, 1, 0, 30)
    assert ui.fleet.tick == 1
    ui.click(buttons['task'].center, 1, 0, 40)
    assert ui.tool == 'box'
    assert not ui.fleet.tasks
    ui.click(center((3, 0)), 1, 0, 50)
    assert len(ui.fleet.tasks) == 1
    assert ui.fleet.grid.blocked == before


def test_help_blocks_simulation_and_click_through_then_resumes_without_catchup():
    ui = DepotUI(Fleet())
    ui.action('help', 0)
    ui.update(10000)
    assert ui.fleet.tick == 0
    ui.click(center((0, 0)), 3, 0, 10000)
    ui.click(button_rects(ui.fleet.grid)['task'].center, 1, 0, 10000)
    assert not ui.fleet.tasks
    ui.key(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_t, mod=0), 10000)
    assert not ui.fleet.tasks
    ui.click(help_close_rect(ui.fleet.grid).center, 1, 0, 10000)
    assert not ui.show_help
    ui.update(10001)
    assert ui.fleet.tick == 0
    ui.update(10120)
    assert ui.fleet.tick == 1


def test_escape_closes_help_before_closing_application():
    ui = DepotUI(Fleet())
    escape = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0)
    ui.show_help = True
    assert ui.key(escape, 0)
    assert not ui.show_help
    assert not ui.key(escape, 0)


def test_roster_selects_eighth_robot_and_preserves_map():
    ui = DepotUI(Fleet(robot_count=8))
    before = ui.fleet.grid.blocked.copy()
    ui.click(roster_rects(ui.fleet)[8].center, 1, 0, 0)
    assert ui.selected == 8
    assert ui.fleet.grid.blocked == before


def test_animated_robot_can_be_selected_at_visible_position():
    ui = DepotUI(Fleet())
    robot = ui.fleet.robots[1]
    start = robot.pos
    robot.pos = (start[0] + 1, start[1])
    ui.animation.capture(ui.fleet, 120, 100)
    ui.click(center(start), 1, 0, 100)
    assert ui.selected == 2
    assert start not in ui.fleet.grid.blocked


def test_animation_interpolates_without_changing_engine_state():
    fleet = Fleet()
    animation = Animation()
    animation.capture(fleet, 120, 0)
    robot = fleet.robots[0]
    robot.pos = (2, 1)
    animation.capture(fleet, 120, 100)
    position, facing, moving = animation.position(robot, 160)
    assert position == (1.5, 1)
    assert facing == 'right' and moving
    assert robot.pos == (2, 1)
    assert animation.position(robot, 500)[0] == (2, 1)


def test_manual_pickup_reset_and_mouse_feedback():
    ui = DepotUI(Fleet())
    ui.click(center((0, 0)), 3, pygame.KMOD_SHIFT, 0)
    assert ui.commands.pickup == (0, 0)
    ui.click(center((2, 0)), 3, 0, 0)
    assert len(ui.fleet.tasks) == 1
    ui.click(center((0, 2)), 1, 0, 0)
    assert 'adaugat' in ui.commands.message
    ui.key(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r, mod=0), 0)
    assert not ui.fleet.tasks
    assert (0, 2) in ui.fleet.grid.blocked
    assert ui.commands.pickup is None
    assert ui.animation.frames[1]['end'] == ui.fleet.robots[0].home


@pytest.mark.parametrize('count', [3, 5, 8])
def test_controls_fit_window_and_do_not_overlap_map(count):
    fleet = Fleet(robot_count=count)
    bounds = pygame.Rect((0, 0), window_size(fleet.grid))
    map_rect = pygame.Rect(MAP_X, HEADER, fleet.grid.width * CELL, fleet.grid.height * CELL)
    rects = list(button_rects(fleet.grid).values()) + list(roster_rects(fleet).values())
    for i, rect in enumerate(rects):
        assert bounds.contains(rect)
        assert not map_rect.colliderect(rect)
        assert not any(rect.colliderect(other) for other in rects[i + 1:])


def test_startup_is_empty_without_demo_tasks(monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    monkeypatch.setenv('SDL_AUDIODRIVER', 'dummy')
    import fleet_ui
    created = []
    def factory(**kwargs):
        fleet = Fleet(**kwargs)
        created.append(fleet)
        return fleet
    monkeypatch.setattr(fleet_ui, 'Fleet', factory)
    monkeypatch.setattr(pygame.event, 'get', lambda: [pygame.event.Event(pygame.QUIT)])
    fleet_ui.run()
    fleet = created[0]
    assert not fleet.grid.blocked
    assert not fleet.tasks
    assert not fleet.pickups
    assert all(not r.carrying for r in fleet.robots)
    ui = DepotUI(fleet)
    assert not ui.show_paths
    for tick in range(100):
        ui.update(tick * 120)
    assert not fleet.tasks


def test_user_placed_box_is_delivered_and_duplicate_is_rejected():
    from engine.grid import Grid
    fleet = Fleet(grid=Grid(30, 20), pickups=[])
    ui = DepotUI(fleet)
    ui.action('task', 0)
    ui.click(center((10, 5)), 1, 0, 0)
    ui.click(center((10, 5)), 1, 0, 0)
    assert len(fleet.tasks) == 1
    task = fleet.tasks[0]
    assert task.pickup == (10, 5)
    for tick in range(120):
        ui.advance(tick * 120)
    assert task.status == 'completed'


def test_full_reset_returns_to_empty_map():
    from engine.grid import Grid
    ui = DepotUI(Fleet(grid=Grid(30, 20), pickups=[]))
    ui.click(center((3, 0)), 1, 0, 0)
    assert ui.fleet.grid.blocked
    ui.place_box((10, 5))
    ui.key(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r, mod=pygame.KMOD_SHIFT), 0)
    assert not ui.fleet.grid.blocked
    assert not ui.fleet.tasks
    assert not ui.fleet.pickups


def test_box_requires_free_cell_and_reachable_exit():
    from engine.grid import Grid
    ui = DepotUI(Fleet(grid=Grid(30, 20), pickups=[]))
    for cell in (ui.fleet.robots[0].pos, ui.fleet.dropoffs[0]):
        ui.place_box(cell)
    ui.fleet.grid.blocked.add((5, 5))
    ui.place_box((5, 5))
    ui.fleet.grid.blocked.update((27, y) for y in range(20))
    ui.place_box((5, 6))
    assert not ui.fleet.tasks
    assert 'acces' in ui.commands.message
