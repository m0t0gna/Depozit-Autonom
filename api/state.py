"""Starea comuna a serverului: o singura flota, la care au acces atat REST cat si WebSocket.

De ce un modul separat: daca server.py si websocket.py si-ar importa fiecare `fleet`
direct (`from api.server import fleet`), fiecare ar pastra propria referinta. Dupa un reset,
una dintre ele ar continua sa foloseasca flota veche. Aici toata lumea cere `state.fleet`
de fiecare data, deci vede mereu flota curenta.
"""
from api.schemas import FleetState, RobotState, TaskState
from engine.fleet import Fleet

DEFAULT_ROBOTS = 5


class SimulationState:
    def __init__(self):
        self.fleet = Fleet(robot_count=DEFAULT_ROBOTS)
        # True cat timp simularea ruleaza continuu (pornita prin WebSocket cu "play").
        # Toate endpoint-urile sunt `async def`, deci ruleaza in acelasi thread (event loop):
        # nu exista curse de date intre un `step` si un `edit`, iar un lock nu e necesar.
        self.running = False

    def reset(self, robot_count, coordination, allocator):
        """Creeaza o flota noua. Ridica ValueError daca parametrii sunt invalizi."""
        self.fleet = Fleet(robot_count=robot_count, coordination=coordination, allocator=allocator)
        self.running = False


state = SimulationState()


def fleet_to_state(fleet: Fleet) -> FleetState:
    """Transforma obiectele motorului in modele Pydantic (serializabile JSON)."""
    return FleetState(
        tick=fleet.tick,
        coordination=fleet.coordinator.name,
        allocator=fleet.allocator.name,
        robots=[RobotState(
            id=r.id, pos=r.pos, home=r.home, phase=r.phase, task_id=r.task_id, goal=r.goal,
            steps=r.steps, wait_ticks=r.wait_ticks, deliveries=r.deliveries, carrying=r.carrying,
        ) for r in fleet.robots],
        tasks=[TaskState(
            id=t.id, pickup=t.pickup, dropoff=t.dropoff, status=t.status, robot_id=t.robot_id,
        ) for t in fleet.tasks],
        grid_width=fleet.grid.width,
        grid_height=fleet.grid.height,
        blocked=sorted(fleet.grid.blocked),
        dropoffs=fleet.dropoffs,
        completed=fleet.completed,
        pending=fleet.pending,
    )
