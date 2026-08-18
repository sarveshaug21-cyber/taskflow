import os
import sqlite3
from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from models import init_db

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-me-do-not-use-in-production')

# Database setup
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def ensure_priority_column():
    """Idempotent migration: adds a priority column if it doesn't already exist."""
    conn = get_db_connection()
    try:
        conn.execute("ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT 'medium'")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists
    conn.close()

# Initialize the database on startup
init_db()
ensure_priority_column()

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
    conn = get_db_connection()
    tasks = conn.execute('SELECT * FROM tasks WHERE user_id = ?', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('dashboard.html', tasks=tasks)

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

# ---------------- API endpoints ----------------

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
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    conn = get_db_connection()
    cursor = conn.execute(
        'INSERT INTO tasks (title, description, status, due_date, priority, user_id) VALUES (?, ?, ?, ?, ?, ?)',
        (title, description, status, due_date, priority, session['user_id'])
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return jsonify({
        'id': new_id, 'title': title, 'description': description,
        'status': status, 'due_date': due_date, 'priority': priority
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
    new_status = 'pending' if task['status'] == 'completed' else 'completed'
    conn.execute('UPDATE tasks SET status = ? WHERE id = ?', (new_status, id))
    conn.commit()
    conn.close()
    return jsonify({'id': id, 'status': new_status}), 200

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db_connection()
    tasks = conn.execute('SELECT * FROM tasks WHERE user_id = ?', (session['user_id'],)).fetchall()
    conn.close()
    return jsonify([dict(task) for task in tasks]), 200

@app.route('/api/tasks/<int:id>', methods=['PUT'])
def update_task(id):
    """Partial update: any field not supplied keeps its current value."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db_connection()
    task = conn.execute('SELECT * FROM tasks WHERE id = ? AND user_id = ?', (id, session['user_id'])).fetchone()
    if not task:
        conn.close()
        return jsonify({'error': 'Task not found'}), 404

    data = request.get_json() or {}
    task_keys = task.keys()
    title = data.get('title', task['title'])
    description = data.get('description', task['description'])
    status = data.get('status', task['status'])
    due_date = data.get('due_date', task['due_date'])
    current_priority = task['priority'] if 'priority' in task_keys else 'medium'
    priority = data.get('priority', current_priority)

    conn.execute(
        'UPDATE tasks SET title = ?, description = ?, status = ?, due_date = ?, priority = ? WHERE id = ?',
        (title, description, status, due_date, priority, id)
    )
    conn.commit()
    conn.close()
    return jsonify({
        'id': id, 'title': title, 'description': description,
        'status': status, 'due_date': due_date, 'priority': priority
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
    conn.execute('DELETE FROM tasks WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)
