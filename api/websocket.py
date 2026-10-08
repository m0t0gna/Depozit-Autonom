"""Canalul WebSocket /ws/live: trimite starea flotei si primeste comenzi simple.

Comenzi acceptate (text): "play", "pause", "step". Orice altceva e ignorat.
"""
import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.state import fleet_to_state, state

router = APIRouter()
TICK_SECONDS = 0.1  # 10 tick-uri pe secunda cand simularea ruleaza continuu


class ConnectionManager:
    def __init__(self):
        self.connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.connections:
            self.connections.remove(websocket)
        if not self.connections:
            state.running = False  # nimeni nu se uita: punem simularea pe pauza

    async def broadcast(self, payload: str):
        dead = []
        for websocket in list(self.connections):
            try:
                await websocket.send_text(payload)
            except Exception:  # clientul s-a deconectat brusc
                dead.append(websocket)
        for websocket in dead:
            self.disconnect(websocket)


manager = ConnectionManager()


def snapshot_json() -> str:
    return fleet_to_state(state.fleet).model_dump_json()


async def publish():
    """Trimite starea curenta tuturor clientilor conectati."""
    await manager.broadcast(snapshot_json())


async def simulation_loop():
    """Task de fundal pornit de server: avanseaza simularea cat timp `state.running` e True."""
    while True:
        if state.running and manager.connections:
            state.fleet.step()
            await publish()
        await asyncio.sleep(TICK_SECONDS)


@router.websocket('/ws/live')
async def live(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await websocket.send_text(snapshot_json())
        while True:
            command = await websocket.receive_text()
            if command == 'play':
                state.running = True
            elif command == 'pause':
                state.running = False
            elif command == 'step':
                state.running = False
                state.fleet.step()
                await publish()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
