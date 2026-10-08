"""Serverul FastAPI: expune motorul de flota prin REST si WebSocket.

Pornire:  uvicorn api.server:app --reload     Documentatie interactiva: /docs
"""
import asyncio
import contextlib
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import EditRequest, FleetState, TaskRequest
from api.state import DEFAULT_ROBOTS, fleet_to_state, state
from api.websocket import publish, router as websocket_router, simulation_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Porneste bucla de simulare la pornirea serverului si o opreste la inchidere."""
    task = asyncio.create_task(simulation_loop())
    yield
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


app = FastAPI(title='Micul Depozit API', version='2.0.0', lifespan=lifespan)

# Permite frontend-ului (React, in dezvoltare) sa cheme acest backend.
# ATENTIE: "*" e acceptabil doar local; pentru publicare trebuie restrans la domeniul tau.
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)
app.include_router(websocket_router)


@app.get('/api/fleet', response_model=FleetState)
async def get_state():
    """Starea curenta a intregului depozit."""
    return fleet_to_state(state.fleet)


@app.post('/api/fleet/step', response_model=FleetState)
async def step_simulation():
    """Avanseaza simularea cu exact un tick."""
    state.fleet.step()
    await publish()
    return fleet_to_state(state.fleet)


@app.post('/api/fleet/task')
async def add_task(req: TaskRequest):
    """Adauga o comanda: ridica de la `pickup` si livreaza la `dropoff`."""
    try:
        state.fleet.add_task(req.pickup, req.dropoff)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    await publish()
    return {'status': 'ok'}


@app.post('/api/fleet/task/random')
async def add_random_task():
    """Adauga o comanda aleatoare (utila pentru teste)."""
    try:
        state.fleet.random_task()
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    await publish()
    return {'status': 'ok'}


@app.post('/api/fleet/edit')
async def edit_map(req: EditRequest):
    """Adauga sau elimina un perete la celula data."""
    if not state.fleet.edit(req.cell):
        raise HTTPException(status_code=400, detail='Celula nu poate fi modificata '
                            '(robot, statie sau punct al unei comenzi active).')
    await publish()
    return {'status': 'ok'}


@app.post('/api/fleet/reset', response_model=FleetState)
async def reset_fleet(
    robot_count: int = Query(DEFAULT_ROBOTS, ge=1, le=8),
    coordination: Literal['window', 'conservative'] = 'window',
    allocator: Literal['greedy', 'hungarian'] = 'greedy',
):
    """Reia simularea de la zero, cu numarul de roboti, coordonatorul si alocatorul alese.

    Valorile invalide sunt respinse automat de FastAPI cu eroarea 422.
    """
    try:
        state.reset(robot_count, coordination, allocator)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    await publish()
    return fleet_to_state(state.fleet)
