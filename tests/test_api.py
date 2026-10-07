from fastapi.testclient import TestClient
from api.server import app

client = TestClient(app)

def test_get_state():
    response = client.get("/api/fleet")
    assert response.status_code == 200
    data = response.json()
    assert "tick" in data
    assert "robots" in data
    assert len(data["robots"]) == 5 # implicit robot_count=5

def test_step_simulation():
    res1 = client.get("/api/fleet")
    tick1 = res1.json()["tick"]
    
    res2 = client.post("/api/fleet/step")
    assert res2.status_code == 200
    tick2 = res2.json()["tick"]
    
    assert tick2 == tick1 + 1

def test_add_random_task():
    res = client.post("/api/fleet/task/random")
    assert res.status_code == 200
    
    state = client.get("/api/fleet").json()
    assert len(state["tasks"]) > 0
