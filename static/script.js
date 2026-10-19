const taskForm = document.getElementById('add-task-form');
const taskTitleInput = document.getElementById('task-title');
const taskDescriptionInput = document.getElementById('task-description');
const taskDueDateInput = document.getElementById('task-due-date');
const taskPriorityInput = document.getElementById('task-priority');
const tasksContainer = document.getElementById('tasks-container');
const todayDate = document.getElementById('today-date');
const searchInput = document.getElementById('search-input');
const sortSelect = document.getElementById('sort-select');
const filterChips = document.querySelectorAll('.chip');

let allTasks = [];
let currentFilter = 'all';
let currentSort = 'due_date';
let currentSearch = '';
let editingTaskId = null;

if (todayDate) {
    todayDate.textContent = new Date().toLocaleDateString('en-US', {
        weekday: 'long', month: 'short', day: 'numeric'
    });
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str || '';
    return div.innerHTML;
}

function todayISO() {
    const d = new Date();
    return d.toISOString().split('T')[0];
}

function isOverdue(task) {
    return task.due_date && task.due_date < todayISO() && task.status !== 'completed';
}

function isToday(task) {
    return task.due_date === todayISO();
}

const PRIORITY_ORDER = { high: 0, medium: 1, low: 2 };

function applyFiltersSortAndSearch(tasks) {
    let result = tasks.slice();

    if (currentFilter === 'active') {
        result = result.filter(t => t.status !== 'completed');
    } else if (currentFilter === 'completed') {
        result = result.filter(t => t.status === 'completed');
    }

    if (currentSearch.trim()) {
        const q = currentSearch.trim().toLowerCase();
        result = result.filter(t =>
            (t.title || '').toLowerCase().includes(q) ||
            (t.description || '').toLowerCase().includes(q)
        );
    }

    if (currentSort === 'due_date') {
        result.sort((a, b) => {
            if (!a.due_date && !b.due_date) return 0;
            if (!a.due_date) return 1;
            if (!b.due_date) return -1;
            return a.due_date.localeCompare(b.due_date);
        });
    } else if (currentSort === 'priority') {
        result.sort((a, b) => (PRIORITY_ORDER[a.priority] ?? 1) - (PRIORITY_ORDER[b.priority] ?? 1));
    } else if (currentSort === 'newest') {
        result.sort((a, b) => b.id - a.id);
    }

    return result;
}

function groupTasks(tasks) {
    const groups = { overdue: [], today: [], upcoming: [], noDate: [], completed: [] };

    tasks.forEach(task => {
        if (task.status === 'completed') {
            groups.completed.push(task);
        } else if (isOverdue(task)) {
            groups.overdue.push(task);
        } else if (isToday(task)) {
            groups.today.push(task);
        } else if (task.due_date) {
            groups.upcoming.push(task);
        } else {
            groups.noDate.push(task);
        }
    });

    return groups;
}

function taskItemHtml(task) {
    if (editingTaskId === task.id) {
        return editFormHtml(task);
    }

    const overdue = isOverdue(task);
    const dueLabel = task.due_date ? (overdue ? 'OVERDUE' : 'DUE') : '';

    return `
        <li class="task-item priority-${escapeHtml(task.priority || 'medium')}${task.status === 'completed' ? ' completed' : ''}">
            <button class="task-checkbox${task.status === 'completed' ? ' checked' : ''}" data-id="${task.id}" aria-label="Toggle complete"></button>
            <div class="task-content">
                <p class="task-title">${escapeHtml(task.title)}</p>
                ${task.description ? `<p class="task-description">${escapeHtml(task.description)}</p>` : ''}
                ${task.due_date ? `<span class="task-due${overdue ? ' overdue' : ''}">${dueLabel} ${escapeHtml(task.due_date)}</span>` : ''}
            </div>
            <div class="task-buttons">
                <button class="task-edit" data-id="${task.id}" aria-label="Edit task">✎</button>
                <button class="task-delete" data-id="${task.id}" aria-label="Delete task">&times;</button>
            </div>
        </li>
    `;
}

function editFormHtml(task) {
    return `
        <li class="task-item editing">
            <div class="edit-form" data-id="${task.id}">
                <input type="text" class="edit-title" value="${escapeHtml(task.title)}" placeholder="Title">
                <textarea class="edit-description" placeholder="Notes (optional)">${escapeHtml(task.description || '')}</textarea>
                <div class="edit-line">
                    <input type="date" class="edit-due-date" value="${task.due_date || ''}">
                    <select class="edit-priority">
                        <option value="low"${task.priority === 'low' ? ' selected' : ''}>Low</option>
                        <option value="medium"${(!task.priority || task.priority === 'medium') ? ' selected' : ''}>Medium</option>
                        <option value="high"${task.priority === 'high' ? ' selected' : ''}>High</option>
                    </select>
                </div>
                <div class="edit-actions">
                    <button class="edit-save" data-id="${task.id}">Save</button>
                    <button class="edit-cancel" data-id="${task.id}">Cancel</button>
                </div>
            </div>
        </li>
    `;
}

function groupSectionHtml(label, tasks) {
    if (tasks.length === 0) return '';
    return `
        <div class="group-section">
            <p class="group-label">${label}</p>
            <ul class="tasks-list">
                ${tasks.map(taskItemHtml).join('')}
            </ul>
        </div>
    `;
}

function render() {
    const filtered = applyFiltersSortAndSearch(allTasks);

    if (allTasks.length === 0) {
        tasksContainer.innerHTML = '<p class="empty-state">Nothing on the list. Add something above.</p>';
        return;
    }

    if (filtered.length === 0) {
        tasksContainer.innerHTML = '<p class="empty-state">No tasks match your search or filter.</p>';
        return;
    }

    // If sorting by priority or newest, skip date-grouping and show a flat list.
    if (currentSort !== 'due_date') {
        tasksContainer.innerHTML = `<ul class="tasks-list">${filtered.map(taskItemHtml).join('')}</ul>`;
        return;
    }

    const groups = groupTasks(filtered);
    tasksContainer.innerHTML = [
        groupSectionHtml('Overdue', groups.overdue),
        groupSectionHtml('Today', groups.today),
        groupSectionHtml('Upcoming', groups.upcoming),
        groupSectionHtml('No due date', groups.noDate),
        groupSectionHtml('Completed', groups.completed)
    ].join('');
}

function fetchTasks() {
    fetch('/api/tasks')
        .then(response => response.json())
        .then(tasks => {
            allTasks = tasks;
            render();
        })
        .catch(error => {
            console.error('Error fetching tasks:', error);
            tasksContainer.innerHTML = '<p class="empty-state">Could not load tasks.</p>';
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
            due_date: taskDueDateInput.value || null,
            priority: taskPriorityInput.value
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

searchInput.addEventListener('input', event => {
    currentSearch = event.target.value;
    render();
});

sortSelect.addEventListener('change', event => {
    currentSort = event.target.value;
    render();
});

filterChips.forEach(chip => {
    chip.addEventListener('click', () => {
        filterChips.forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        currentFilter = chip.dataset.filter;
        render();
    });
});

tasksContainer.addEventListener('click', event => {
    const target = event.target;
    const id = target.dataset.id;
    if (!id) return;

    if (target.classList.contains('task-checkbox')) {
        fetch(`/api/tasks/${id}/complete`, { method: 'PUT' })
            .then(response => {
                if (!response.ok) throw new Error('Failed to update task');
                fetchTasks();
            })
            .catch(error => alert('Error updating task: ' + error.message));
    }

    if (target.classList.contains('task-delete')) {
        fetch(`/api/tasks/${id}`, { method: 'DELETE' })
            .then(response => {
                if (!response.ok && response.status !== 204) throw new Error('Failed to delete task');
                fetchTasks();
            })
            .catch(error => alert('Error deleting task: ' + error.message));
    }

    if (target.classList.contains('task-edit')) {
        editingTaskId = parseInt(id, 10);
        render();
    }

    if (target.classList.contains('edit-cancel')) {
        editingTaskId = null;
        render();
    }

    if (target.classList.contains('edit-save')) {
        const formEl = target.closest('.edit-form');
        const updated = {
            title: formEl.querySelector('.edit-title').value.trim(),
            description: formEl.querySelector('.edit-description').value.trim(),
            due_date: formEl.querySelector('.edit-due-date').value || null,
            priority: formEl.querySelector('.edit-priority').value
        };
        if (!updated.title) {
            alert('Title cannot be empty.');
            return;
        }
        fetch(`/api/tasks/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updated)
        })
            .then(response => {
                if (!response.ok) throw new Error('Failed to save task');
                editingTaskId = null;
                fetchTasks();
            })
            .catch(error => alert('Error saving task: ' + error.message));
    }
});

fetchTasks();

// ---------------- Keyboard shortcuts ----------------
//
// Shortcuts are ignored when the user is typing in an input, textarea,
// select, or contentEditable element, and when any modifier key
// (Ctrl, Alt, Meta, Shift) is held. This prevents conflicts with form
// entry and browser/OS shortcuts.

function isTypingTarget(el) {
  if (!el) return false;
  const tag = el.tagName;
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return true;
  if (el.isContentEditable) return true;
  return false;
}

window.addEventListener('keydown', (event) => {
  if (event.ctrlKey || event.altKey || event.metaKey || event.shiftKey) return;
  if (isTypingTarget(document.activeElement)) return;

  switch (event.key.toLowerCase()) {
    case 'c':
      event.preventDefault();
      if (taskTitleInput) taskTitleInput.focus();
      break;
    case 't':
      event.preventDefault();
      if (taskDueDateInput) {
        taskDueDateInput.value = todayISO();
      }
      break;
  }
});
