document.addEventListener('DOMContentLoaded', () => {
    fetch('/api/tasks')
        .then(response => response.json())
        .then(tasks => {
            const tasksList = document.getElementById('tasks-list');
            tasks.forEach(task => {
                const li = document.createElement('li');
                li.textContent = task.title;
                li.innerHTML += ` - ${task.description} - Due: ${task.due_date}`;
                
                const completeButton = document.createElement('button');
                completeButton.textContent = 'Complete';
                completeButton.addEventListener('click', () => markTaskComplete(task.id));
                li.appendChild(completeButton);
                
                const deleteButton = document.createElement('button');
                deleteButton.textContent = 'Delete';
                deleteButton.addEventListener('click', () => deleteTask(task.id));
                li.appendChild(deleteButton);
                
                tasksList.appendChild(li);
            });
        })
        .catch(error => console.error('Error fetching tasks:', error));

    document.getElementById('add-task-form').addEventListener('submit', addTask);
});

function addTask(event) {
    event.preventDefault();
    const title = document.getElementById('task-title').value;
    const description = document.getElementById('task-description').value;

    fetch('/api/tasks', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ title, description })
    })
    .then(response => response.json())
    .then(task => {
        const tasksList = document.getElementById('tasks-list');
        const li = document.createElement('li');
        li.textContent = task.title;
        li.innerHTML += ` - ${task.description} - Due: ${task.due_date}`;
        
        const completeButton = document.createElement('button');
        completeButton.textContent = 'Complete';
        completeButton.addEventListener('click', () => markTaskComplete(task.id));
        li.appendChild(completeButton);
        
        const deleteButton = document.createElement('button');
        deleteButton.textContent = 'Delete';
        deleteButton.addEventListener('click', () => deleteTask(task.id));
        li.appendChild(deleteButton);
        
        tasksList.appendChild(li);
    })
    .catch(error => console.error('Error adding task:', error));

    document.getElementById('task-title').value = '';
    document.getElementById('task-description').value = '';
}

function markTaskComplete(taskId) {
    fetch(`/api/tasks/${taskId}/complete`, {
        method: 'PUT'
    })
    .then(response => response.json())
    .then(updatedTask => {
        const tasksList = document.getElementById('tasks-list');
        const li = tasksList.querySelector(`li[data-id="${updatedTask.id}"]`);
        if (li) {
            li.textContent = updatedTask.title;
            li.innerHTML += ` - ${updatedTask.description} - Due: ${updatedTask.due_date}`;
        }
    })
    .catch(error => console.error('Error marking task complete:', error));
}

function deleteTask(taskId) {
    fetch(`/api/tasks/${taskId}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (response.ok) {
            const tasksList = document.getElementById('tasks-list');
            const li = tasksList.querySelector(`li[data-id="${taskId}"]`);
            if (li) {
                tasksList.removeChild(li);
            }
        } else {
            console.error('Error deleting task:', response.statusText);
        }
    })
    .catch(error => console.error('Error deleting task:', error));
}
