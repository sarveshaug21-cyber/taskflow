const taskForm = document.getElementById('add-task-form');
const taskTitleInput = document.getElementById('task-title');
const taskDescriptionInput = document.getElementById('task-description');
const taskDueDateInput = document.getElementById('task-due-date');
const tasksList = document.getElementById('tasks-list');

function renderTasks(tasks) {
    tasksList.innerHTML = '';

    if (!tasks || tasks.length === 0) {
        tasksList.innerHTML = '<li class="empty-state">No tasks yet — add one above to get started.</li>';
        return;
    }

    tasks.forEach(task => {
        const li = document.createElement('li');
        li.className = 'task-item' + (task.status === 'completed' ? ' completed' : '');
        li.innerHTML = `
            <div class="task-content">
                <p class="task-title">${escapeHtml(task.title)}</p>
                ${task.description ? `<p class="task-description">${escapeHtml(task.description)}</p>` : ''}
                ${task.due_date ? `<span class="task-due">Due ${escapeHtml(task.due_date)}</span>` : ''}
            </div>
            <div class="task-actions">
                ${task.status !== 'completed' ? `<button class="btn-complete" data-id="${task.id}">Complete</button>` : ''}
                <button class="btn-delete" data-id="${task.id}">Delete</button>
            </div>
        `;
        tasksList.appendChild(li);
    });
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function fetchTasks() {
    fetch('/api/tasks')
        .then(response => response.json())
        .then(tasks => renderTasks(tasks))
        .catch(error => {
            console.error('Error fetching tasks:', error);
            tasksList.innerHTML = '<li class="empty-state">Could not load tasks.</li>';
        });
}

taskForm.addEventListener('submit', event => {
    event.preventDefault();

    const title = taskTitleInput.value.trim();
    if (!title) return;

    fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            title: title,
            description: taskDescriptionInput.value.trim(),
            status: 'pending',
            due_date: taskDueDateInput.value || null
        })
    })
        .then(response => {
            if (!response.ok) throw new Error('Failed to add task');
            return response.json();
        })
        .then(() => {
            taskForm.reset();
            fetchTasks();
        })
        .catch(error => {
            alert('Error adding task: ' + error.message);
        });
});

tasksList.addEventListener('click', event => {
    const id = event.target.dataset.id;
    if (!id) return;

    if (event.target.classList.contains('btn-complete')) {
        fetch(`/api/tasks/${id}/complete`, { method: 'PUT' })
            .then(response => {
                if (!response.ok) throw new Error('Failed to mark task complete');
                fetchTasks();
            })
            .catch(error => {
                alert('Error marking task complete: ' + error.message);
            });
    }

    if (event.target.classList.contains('btn-delete')) {
        fetch(`/api/tasks/${id}`, { method: 'DELETE' })
            .then(response => {
                if (!response.ok && response.status !== 204) {
                    throw new Error('Failed to delete task');
                }
                fetchTasks();
            })
            .catch(error => {
                alert('Error deleting task: ' + error.message);
            });
    }
});

fetchTasks();
