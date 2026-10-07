from fastapi import WebSocket, WebSocketDisconnect
from typing import List
import asyncio
import json

from api.server import app, fleet, get_fleet_state

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast_state(self):
        state_dict = get_fleet_state().model_dump()
        state_json = json.dumps(state_dict)
        for connection in self.active_connections:
            try:
                await connection.send_text(state_json)
            except:
                pass

manager = ConnectionManager()

# Background task global pentru a rula simularea în buclă dacă e "play"
simulation_running = False

async def simulation_loop():
    global simulation_running
    while True:
        if simulation_running and len(manager.active_connections) > 0:
            fleet.step()
            await manager.broadcast_state()
            await asyncio.sleep(0.1) # 100ms per tick (10 FPS)
        else:
            await asyncio.sleep(0.1)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(simulation_loop())

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Trimitem starea imediat la conectare
        await websocket.send_text(json.dumps(get_fleet_state().model_dump()))
        
        while True:
            data = await websocket.receive_text()
            # Aici putem primi comenzi direct prin WebSocket (ex: "play", "pause")
            global simulation_running
            if data == "play":
                simulation_running = True
            elif data == "pause":
                simulation_running = False
            elif data == "step":
                simulation_running = False
                fleet.step()
                await manager.broadcast_state()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
