import pytest
from fastapi.testclient import TestClient

from api.server import app


@pytest.fixture
def client():
    # `with` porneste si ciclul de viata al aplicatiei (bucla de simulare din fundal).
    with TestClient(app) as test_client:
        test_client.post('/api/fleet/reset')  # stare curata pentru fiecare test
        yield test_client


def test_get_state(client):
    data = client.get('/api/fleet').json()
    assert data['tick'] == 0
    assert len(data['robots']) == 5
    assert data['coordination'] == 'window'
    assert data['allocator'] == 'greedy'


def test_step_simulation(client):
    assert client.post('/api/fleet/step').json()['tick'] == 1
    assert client.get('/api/fleet').json()['tick'] == 1


def test_add_random_task(client):
    assert client.post('/api/fleet/task/random').status_code == 200
    assert len(client.get('/api/fleet').json()['tasks']) == 1


def test_add_task_rejects_same_pickup_and_dropoff(client):
    response = client.post('/api/fleet/task', json={'pickup': [4, 2], 'dropoff': [4, 2]})
    assert response.status_code == 400


def test_edit_refuses_robot_cell_and_toggles_free_cell(client):
    assert client.post('/api/fleet/edit', json={'cell': [1, 1]}).status_code == 400  # baza unui robot
    before = client.get('/api/fleet').json()['blocked']
    assert client.post('/api/fleet/edit', json={'cell': [15, 6]}).status_code == 200
    assert client.get('/api/fleet').json()['blocked'] != before


def test_reset_selects_robots_coordination_and_allocator(client):
    data = client.post('/api/fleet/reset?robot_count=3&coordination=conservative&allocator=hungarian').json()
    assert len(data['robots']) == 3
    assert data['coordination'] == 'conservative'
    assert data['allocator'] == 'hungarian'
    assert client.get('/api/fleet').json()['allocator'] == 'hungarian'


@pytest.mark.parametrize('query', ['allocator=nope', 'coordination=nope', 'robot_count=0', 'robot_count=9'])
def test_reset_rejects_invalid_values(client, query):
    assert client.post(f'/api/fleet/reset?{query}').status_code == 422


def test_websocket_steps_the_current_fleet_after_reset(client):
    """Regresie: dupa reset, WebSocket-ul trebuie sa foloseasca flota NOUA, nu pe cea veche."""
    client.post('/api/fleet/reset?robot_count=3&allocator=hungarian')
    with client.websocket_connect('/ws/live') as ws:
        first = ws.receive_json()
        assert (first['tick'], len(first['robots']), first['allocator']) == (0, 3, 'hungarian')
        ws.send_text('step')
        assert ws.receive_json()['tick'] == 1
    assert client.get('/api/fleet').json()['tick'] == 1  # REST vede aceeasi flota


def test_rest_changes_are_pushed_to_websocket_clients(client):
    with client.websocket_connect('/ws/live') as ws:
        ws.receive_json()
        client.post('/api/fleet/task/random')
        assert len(ws.receive_json()['tasks']) == 1
