from engine.commands import TaskCommands
from engine.fleet import Fleet
from engine.grid import Grid


def test_single_right_click_creates_task_immediately():
    fleet = Fleet()
    commands = TaskCommands(fleet)
    task = commands.right_click((28, 5))
    assert len(fleet.tasks) == 1
    assert task.dropoff == (28, 5)
    assert task.pickup in fleet.pickups
    assert commands.pickup is None
    assert '#1' in commands.message


def test_auto_pickup_uses_reachable_shortest_route():
    grid = Grid(6, 5)
    grid.blocked.update((1, y) for y in range(4))
    fleet = Fleet(grid=grid, starts=[(5, 4)], pickups=[(0, 0), (4, 4)], dropoffs=[(2, 0)])
    task = TaskCommands(fleet).right_click((2, 0))
    assert task.pickup == (4, 4)


def test_shift_selects_pickup_then_one_click_submits_destination():
    fleet = Fleet()
    commands = TaskCommands(fleet)
    assert commands.right_click((0, 0), custom=True) is None
    assert not fleet.tasks
    task = commands.right_click((2, 0))
    assert (task.pickup, task.dropoff) == ((0, 0), (2, 0))
    assert commands.pickup is None


def test_invalid_click_keeps_manual_selection_and_explains_error():
    commands = TaskCommands(Fleet())
    commands.right_click((0, 0), custom=True)
    assert commands.right_click((4, 3)) is None
    assert commands.pickup == (0, 0)
    assert 'blocata' in commands.message
    assert commands.right_click((0, 0)) is None
    assert 'difere' in commands.message
    commands.cancel()
    assert commands.pickup is None


def test_unreachable_click_does_not_create_task():
    grid = Grid(5, 3)
    grid.blocked.update((2, y) for y in range(3))
    fleet = Fleet(grid=grid, starts=[(0, 0)], pickups=[(1, 1)], dropoffs=[(4, 1)])
    commands = TaskCommands(fleet)
    assert commands.right_click((4, 1)) is None
    assert not fleet.tasks
    assert 'accesibila' in commands.message


def test_real_ui_event_submits_on_first_click(monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    monkeypatch.setenv('SDL_AUDIODRIVER', 'dummy')
    import pygame
    import fleet_ui
    fleet = Fleet()
    monkeypatch.setattr(fleet_ui, 'Fleet', lambda **kwargs: fleet)
    frames = iter([
        [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE, mod=0),
         pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=3, pos=(fleet_ui.MAP_X + 27 * fleet_ui.CELL + 15, fleet_ui.HEADER + 5 * fleet_ui.CELL + 15))],
        [pygame.event.Event(pygame.QUIT)],
    ])
    monkeypatch.setattr(pygame.event, 'get', lambda: next(frames))
    fleet_ui.run()
    assert len(fleet.tasks) == 1  # Nicio comanda demo; prima apasare pune o cutie.
    assert fleet.tasks[-1].pickup == (27, 5)
    assert fleet.tasks[-1].dropoff == (28, 5)


def test_confirmation_is_not_overwritten_by_log_rendering(monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    monkeypatch.setenv('SDL_AUDIODRIVER', 'dummy')
    import pygame
    from fleet_ui import draw, window_size
    pygame.init()
    try:
        font = pygame.font.SysFont('consolas', 15)
        rendered = []

        class RecordingFont:
            def render(self, text, *args):
                rendered.append(text)
                return font.render(text, *args)

            def size(self, text):
                return font.size(text)

        fleet = Fleet()
        commands = TaskCommands(fleet)
        commands.right_click((28, 5))
        draw(pygame.Surface(window_size(fleet.grid)), RecordingFont(), fleet, message=commands.message)
        assert commands.message in rendered
    finally:
        pygame.quit()
