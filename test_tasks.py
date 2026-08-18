import pytest
from app import app, get_db_connection

@pytest.fixture(autouse=True)
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        # Create a user and log in before each test
        client.post('/signup', data=dict(
            username='testuser',
            password='testpassword'
        ), follow_redirects=True)
        client.post('/login', data=dict(
            username='testuser',
            password='testpassword'
        ), follow_redirects=True)
        yield client

def test_add_task(client):
    response = client.post('/api/tasks', json=dict(
        title='Test Task',
        description='This is a test task.',
        status='pending',
        due_date='2023-12-31'
    ))
    assert response.status_code == 201
    assert b'Test Task' in response.data

def test_get_tasks(client):
    client.post('/api/tasks', json=dict(
        title='Test Task',
        description='This is a test task.',
        status='pending',
        due_date='2023-12-31'
    ))
    response = client.get('/api/tasks')
    assert response.status_code == 200
    assert b'Test Task' in response.data

def test_mark_task_complete(client):
    add_response = client.post('/api/tasks', json=dict(
        title='Test Task',
        description='This is a test task.',
        status='pending',
        due_date='2023-12-31'
    ))
    task_id = add_response.get_json()['id']
    response = client.put(f'/api/tasks/{task_id}/complete')
    assert response.status_code == 200

def test_delete_task(client):
    add_response = client.post('/api/tasks', json=dict(
        title='Test Task',
        description='This is a test task.',
        status='pending',
        due_date='2023-12-31'
    ))
    task_id = add_response.get_json()['id']
    response = client.delete(f'/api/tasks/{task_id}')
    assert response.status_code == 204

