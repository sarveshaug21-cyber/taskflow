import re

# --- 1. Patch app.py: fix create_task to return id, add /complete route ---
with open('app.py', 'r') as f:
    content = f.read()

old_create_task = """@app.route('/api/tasks', methods=['POST'])
def create_task():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    status = data.get('status')
    due_date = data.get('due_date')
    if not title or not description or not status or not due_date:
        return jsonify({'error': 'Missing required fields'}), 400
    conn = get_db_connection()
    conn.execute('INSERT INTO tasks (title, description, status, due_date, user_id) VALUES (?, ?, ?, ?, ?)', (title, description, status, due_date, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Task created successfully'}), 201"""

new_create_task = """@app.route('/api/tasks', methods=['POST'])
def create_task():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    status = data.get('status')
    due_date = data.get('due_date')
    if not title or not description or not status or not due_date:
        return jsonify({'error': 'Missing required fields'}), 400
    conn = get_db_connection()
    cursor = conn.execute('INSERT INTO tasks (title, description, status, due_date, user_id) VALUES (?, ?, ?, ?, ?)', (title, description, status, due_date, session['user_id']))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return jsonify({'id': new_id, 'title': title, 'description': description, 'status': status, 'due_date': due_date}), 201

@app.route('/api/tasks/<int:id>/complete', methods=['PUT'])
def complete_task(id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db_connection()
    task = conn.execute('SELECT * FROM tasks WHERE id = ? AND user_id = ?', (id, session['user_id'])).fetchone()
    if task is None:
        conn.close()
        return jsonify({'error': 'Task not found'}), 404
    conn.execute('UPDATE tasks SET status = ? WHERE id = ?', ('completed', id))
    conn.commit()
    conn.close()
    return jsonify({'id': id, 'status': 'completed'}), 200"""

if old_create_task in content:
    content = content.replace(old_create_task, new_create_task)
    print("Patched create_task and added /complete route")
else:
    print("Could not find exact create_task block - app.py may differ from expected, no change made")

with open('app.py', 'w') as f:
    f.write(content)

# --- 2. Patch test_auth.py: fix test_login assertion ---
with open('test_auth.py', 'r') as f:
    test_content = f.read()

old_login_test = """def test_login(client):
    response = client.post('/login', data=dict(
        username='testuser',
        password='testpassword'
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data"""

new_login_test = """def test_login(client):
    response = client.post('/login', data=dict(
        username='testuser',
        password='testpassword'
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b'Welcome to TaskFlow' in response.data"""

if old_login_test in test_content:
    test_content = test_content.replace(old_login_test, new_login_test)
    print("Patched test_login assertion")
else:
    print("Could not find exact test_login block - no change made")

with open('test_auth.py', 'w') as f:
    f.write(test_content)
