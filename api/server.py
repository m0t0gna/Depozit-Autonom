from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from typing import List

from engine.fleet import Fleet
from api.schemas import FleetState, RobotState, TaskState, TaskRequest, EditRequest

app = FastAPI(title="Micul Depozit API", version="2.0.0")

# Permite Frontend-ului (React) să facă cereri către acest backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Pentru producție ar trebui restricționat
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Starea globală a depozitului
fleet = Fleet(robot_count=5)
simulation_task = None
simulation_running = False

def get_fleet_state() -> FleetState:
    """Convertește starea obiectelor Python în Pydantic models (JSON serializabil)"""
    robots = []
    for r in fleet.robots:
        robots.append(RobotState(
            id=r.id,
            pos=r.pos,
            home=r.home,
            phase=r.phase,
            task_id=r.task_id,
            goal=r.goal,
            steps=r.steps,
            wait_ticks=r.wait_ticks,
            deliveries=r.deliveries,
            carrying=r.carrying
        ))
        
    tasks = []
    for t in fleet.tasks:
        tasks.append(TaskState(
            id=t.id,
            pickup=t.pickup,
            dropoff=t.dropoff,
            status=t.status,
            robot_id=t.robot_id
        ))

    return FleetState(
        tick=fleet.tick,
        robots=robots,
        tasks=tasks,
        grid_width=fleet.grid.width,
        grid_height=fleet.grid.height,
        blocked=list(fleet.grid.blocked),
        dropoffs=fleet.dropoffs,
        completed=fleet.completed,
        pending=fleet.pending
    )

@app.get("/api/fleet", response_model=FleetState)
def get_state():
    """Returnează starea curentă a întregului depozit."""
    return get_fleet_state()

@app.post("/api/fleet/step", response_model=FleetState)
def step_simulation():
    """Avansează simularea cu exact un 'tick'."""
    fleet.step()
    return get_fleet_state()

@app.post("/api/fleet/task")
def add_task(req: TaskRequest):
    """Adaugă o nouă comandă manuală."""
    try:
        fleet.add_task(req.pickup, req.dropoff)
        return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/fleet/task/random")
def add_random_task():
    """Adaugă o comandă aleatoare (pentru teste)."""
    try:
        fleet.random_task()
        return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/fleet/edit")
def edit_map(req: EditRequest):
    """Adaugă sau elimină un obstacol."""
    success = fleet.edit(req.cell)
    if not success:
        raise HTTPException(status_code=400, detail="Nu poți modifica această celulă (robot, stație sau punct protejat).")
    return {"status": "ok"}

@app.post("/api/fleet/reset")
def reset_fleet(robot_count: int = 5, coordination: str = 'window'):
    """Resetează complet simularea."""
    global fleet
    fleet = Fleet(robot_count=robot_count, coordination=coordination)
    return {"status": "ok"}

# Importăm websocket-ul pentru a înregistra rutele WS pe instanța app
import api.websocket
