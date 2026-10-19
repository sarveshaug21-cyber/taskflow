import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from models import init_db

app = Flask(__name__)

# Secret key: required for Flask session signing.
#   - Production: the SECRET_KEY environment variable must be set. The app
#     refuses to start without it so a weak fallback is never silently used.
#   - Local development / tests: a dev-only fallback is used when SECRET_KEY
#     is unset and the app is in debug/testing mode.
_secret_key = os.environ.get('SECRET_KEY')
_flask_env = os.environ.get('FLASK_ENV', 'development').lower()
if _secret_key:
    app.secret_key = _secret_key
elif _flask_env == 'production':
    raise RuntimeError(
        'SECRET_KEY environment variable is required in production. '
        'Generate one with: python3 -c "import secrets; print(secrets.token_hex(32))"'
    )
else:
    # Development / testing only: dev fallback. Never used when FLASK_ENV=production.
    app.secret_key = 'dev-secret-change-me-insecure-do-not-use-in-production'

def get_db_connection():
    db_path = app.config.get('DATABASE', 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def run_migrations():
    """Idempotent migrations so existing databases pick up new columns/tables."""
    conn = get_db_connection()

    for stmt in [
        "ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT 'medium'",
        "ALTER TABLE tasks ADD COLUMN recurrence TEXT DEFAULT 'none'",
        "ALTER TABLE tasks ADD COLUMN project_id INTEGER",
    ]:
        try:
            conn.execute(stmt)
            conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists

    conn.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            user_id INTEGER NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS subtasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            completed INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()
run_migrations()

def next_due_date(current_due_date, recurrence):
    """Given a due date string (YYYY-MM-DD) and a recurrence rule, compute the next one."""
    if not current_due_date:
        base = datetime.now()
    else:
        try:
            base = datetime.strptime(current_due_date, '%Y-%m-%d')
        except ValueError:
            base = datetime.now()

    if recurrence == 'daily':
        nxt = base + timedelta(days=1)
    elif recurrence == 'weekly':
        nxt = base + timedelta(weeks=1)
    elif recurrence == 'monthly':
        month = base.month + 1
        year = base.year + (1 if month > 12 else 0)
        month = 1 if month > 12 else month
        day = min(base.day, 28)  # avoid invalid dates like Feb 30
        nxt = base.replace(year=year, month=month, day=day)
    else:
        return None

    return nxt.strftime('%Y-%m-%d')

# ---------------- Pages ----------------

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        if conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone() is not None:
            return render_template('signup.html', error='Username already exists')
        password_hash = generate_password_hash(password)
        conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template('signup.html')

# ---------------- Projects API ----------------

@app.route('/api/projects', methods=['GET'])
def get_projects():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db_connection()
    projects = conn.execute('SELECT * FROM projects WHERE user_id = ?', (session['user_id'],)).fetchall()
    conn.close()
    return jsonify([dict(p) for p in projects]), 200

@app.route('/api/projects', methods=['POST'])
def create_project():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    conn = get_db_connection()
    cursor = conn.execute('INSERT INTO projects (name, user_id) VALUES (?, ?)', (name, session['user_id']))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return jsonify({'id': new_id, 'name': name}), 201

@app.route('/api/projects/<int:id>', methods=['DELETE'])
def delete_project(id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db_connection()
    project = conn.execute('SELECT * FROM projects WHERE id = ? AND user_id = ?', (id, session['user_id'])).fetchone()
    if not project:
        conn.close()
        return jsonify({'error': 'Project not found'}), 404
    conn.execute('UPDATE tasks SET project_id = NULL WHERE project_id = ?', (id,))
    conn.execute('DELETE FROM projects WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return '', 204

# ---------------- Tasks API ----------------

@app.route('/api/tasks', methods=['POST'])
def create_task():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    title = data.get('title')
    description = data.get('description', '')
    status = data.get('status', 'pending')
    due_date = data.get('due_date')
    priority = data.get('priority', 'medium')
    recurrence = data.get('recurrence', 'none')
    project_id = data.get('project_id')
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    conn = get_db_connection()
    cursor = conn.execute(
        'INSERT INTO tasks (title, description, status, due_date, priority, recurrence, project_id, user_id) '
        'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (title, description, status, due_date, priority, recurrence, project_id, session['user_id'])
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return jsonify({
        'id': new_id, 'title': title, 'description': description, 'status': status,
        'due_date': due_date, 'priority': priority, 'recurrence': recurrence, 'project_id': project_id
    }), 201

@app.route('/api/tasks/<int:id>/complete', methods=['PUT'])
def complete_task(id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db_connection()
    task = conn.execute('SELECT * FROM tasks WHERE id = ? AND user_id = ?', (id, session['user_id'])).fetchone()
    if task is None:
        conn.close()
        return jsonify({'error': 'Task not found'}), 404

    was_completed = task['status'] == 'completed'
    new_status = 'pending' if was_completed else 'completed'
    conn.execute('UPDATE tasks SET status = ? WHERE id = ?', (new_status, id))

    created_next = None
    recurrence = task['recurrence'] if 'recurrence' in task.keys() else 'none'
    if not was_completed and recurrence and recurrence != 'none':
        new_due = next_due_date(task['due_date'], recurrence)
        cursor = conn.execute(
            'INSERT INTO tasks (title, description, status, due_date, priority, recurrence, project_id, user_id) '
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (task['title'], task['description'], 'pending', new_due, task['priority'],
             recurrence, task['project_id'] if 'project_id' in task.keys() else None, session['user_id'])
        )
        created_next = cursor.lastrowid

    conn.commit()
    conn.close()
    return jsonify({'id': id, 'status': new_status, 'created_next_task_id': created_next}), 200

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db_connection()
    tasks = conn.execute('SELECT * FROM tasks WHERE user_id = ?', (session['user_id'],)).fetchall()
    result = []
    for task in tasks:
        t = dict(task)
        subtasks = conn.execute('SELECT * FROM subtasks WHERE task_id = ?', (task['id'],)).fetchall()
        t['subtasks'] = [dict(s) for s in subtasks]
        result.append(t)
    conn.close()
    return jsonify(result), 200

@app.route('/api/tasks/<int:id>', methods=['PUT'])
def update_task(id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db_connection()
    task = conn.execute('SELECT * FROM tasks WHERE id = ? AND user_id = ?', (id, session['user_id'])).fetchone()
    if not task:
        conn.close()
        return jsonify({'error': 'Task not found'}), 404

    data = request.get_json() or {}
    keys = task.keys()
    title = data.get('title', task['title'])
    description = data.get('description', task['description'])
    status = data.get('status', task['status'])
    due_date = data.get('due_date', task['due_date'])
    priority = data.get('priority', task['priority'] if 'priority' in keys else 'medium')
    recurrence = data.get('recurrence', task['recurrence'] if 'recurrence' in keys else 'none')
    project_id = data.get('project_id', task['project_id'] if 'project_id' in keys else None)

    conn.execute(
        'UPDATE tasks SET title = ?, description = ?, status = ?, due_date = ?, priority = ?, '
        'recurrence = ?, project_id = ? WHERE id = ?',
        (title, description, status, due_date, priority, recurrence, project_id, id)
    )
    conn.commit()
    conn.close()
    return jsonify({
        'id': id, 'title': title, 'description': description, 'status': status,
        'due_date': due_date, 'priority': priority, 'recurrence': recurrence, 'project_id': project_id
    }), 200

@app.route('/api/tasks/<int:id>', methods=['DELETE'])
def delete_task(id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db_connection()
    task = conn.execute('SELECT * FROM tasks WHERE id = ? AND user_id = ?', (id, session['user_id'])).fetchone()
    if not task:
        conn.close()
        return jsonify({'error': 'Task not found'}), 404
    conn.execute('DELETE FROM subtasks WHERE task_id = ?', (id,))
    conn.execute('DELETE FROM tasks WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return '', 204

# ---------------- Subtasks API ----------------

@app.route('/api/tasks/<int:task_id>/subtasks', methods=['POST'])
def create_subtask(task_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db_connection()
    task = conn.execute('SELECT * FROM tasks WHERE id = ? AND user_id = ?', (task_id, session['user_id'])).fetchone()
    if not task:
        conn.close()
        return jsonify({'error': 'Task not found'}), 404
    data = request.get_json()
    title = (data.get('title') or '').strip()
    if not title:
        conn.close()
        return jsonify({'error': 'Title is required'}), 400
    cursor = conn.execute('INSERT INTO subtasks (task_id, title, completed) VALUES (?, ?, 0)', (task_id, title))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return jsonify({'id': new_id, 'task_id': task_id, 'title': title, 'completed': 0}), 201

@app.route('/api/subtasks/<int:id>', methods=['PUT'])
def toggle_subtask(id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db_connection()
    subtask = conn.execute(
        'SELECT subtasks.* FROM subtasks JOIN tasks ON subtasks.task_id = tasks.id '
        'WHERE subtasks.id = ? AND tasks.user_id = ?', (id, session['user_id'])
    ).fetchone()
    if not subtask:
        conn.close()
        return jsonify({'error': 'Subtask not found'}), 404
    new_completed = 0 if subtask['completed'] else 1
    conn.execute('UPDATE subtasks SET completed = ? WHERE id = ?', (new_completed, id))
    conn.commit()
    conn.close()
    return jsonify({'id': id, 'completed': new_completed}), 200

@app.route('/api/subtasks/<int:id>', methods=['DELETE'])
def delete_subtask(id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db_connection()
    subtask = conn.execute(
        'SELECT subtasks.* FROM subtasks JOIN tasks ON subtasks.task_id = tasks.id '
        'WHERE subtasks.id = ? AND tasks.user_id = ?', (id, session['user_id'])
    ).fetchone()
    if not subtask:
        conn.close()
        return jsonify({'error': 'Subtask not found'}), 404
    conn.execute('DELETE FROM subtasks WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)
