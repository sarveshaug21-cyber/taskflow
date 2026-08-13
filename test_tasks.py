import pytest
from app import app, get_db_connection

@pytest.fixture(autouse=True)
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_add_task(client):
    response = client.post('/api/tasks', headers={'Content-Type': 'application/json'}, data=dict(
        title='Test Task',
        description='This is a test task.',
        status='pending',
        due_date='2023-12-31'
    ))
    assert response.status_code == 201
    assert b'Test Task' in response.data

def test_get_tasks(client):
    response = client.get('/api/tasks')
    assert response.status_code == 200
    assert b'Test Task' in response.data

def test_mark_task_complete(client):
    response = client.put('/api/tasks/1/complete')
    assert response.status_code == 200
    assert b'status": "completed"' in response.data

def test_delete_task(client):
    response = client.delete('/api/tasks/1')
    assert response.status_code == 204
