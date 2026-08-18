import pytest
from app import app, get_db_connection

@pytest.fixture(autouse=True)
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_signup(client):
    response = client.post('/signup', data=dict(
        username='testuser',
        password='testpassword'
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data

def test_login(client):
    response = client.post('/login', data=dict(
        username='testuser',
        password='testpassword'
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b"Today's list" in response.data

def test_logout(client):
    response = client.get('/logout')
    assert response.status_code == 302
