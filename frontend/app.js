// JavaScript for interacting with the Todo API

async function fetchTasks() {
  try {
    const response = await fetch('/tasks');
    const tasks = await response.json();
    renderTasks(tasks);
  } catch (err) {
    console.error('Failed to fetch tasks:', err);
  }
}

function renderTasks(tasks) {
  const list = document.getElementById('taskList');
  list.innerHTML = '';
  tasks.forEach((task) => {
    const li = document.createElement('li');
    if (task.done) {
      li.classList.add('done');
    }
    li.innerHTML = `
      <span>${task.title}</span>
      <div>
        <button class="toggle-btn">${task.done ? 'Undo' : 'Done'}</button>
        <button class="delete-btn">Delete</button>
      </div>
    `;
    // Toggle button handler
    li.querySelector('.toggle-btn').addEventListener('click', async () => {
      try {
        await fetch(`/tasks/${task.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: task.title,
            done: !task.done,
            due_date: task.due_date,
            category: task.category,
            priority: task.priority,
          }),
        });
        fetchTasks();
      } catch (err) {
        console.error('Failed to update task:', err);
      }
    });
    // Delete button handler
    li.querySelector('.delete-btn').addEventListener('click', async () => {
      try {
        await fetch(`/tasks/${task.id}`, {
          method: 'DELETE',
        });
        fetchTasks();
      } catch (err) {
        console.error('Failed to delete task:', err);
      }
    });
    list.appendChild(li);
  });
}

// Handle form submission to create a new task
document.getElementById('taskForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const input = document.getElementById('title');
  const title = input.value.trim();
  if (!title) return;
  try {
    await fetch('/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, done: false }),
    });
    input.value = '';
    fetchTasks();
  } catch (err) {
    console.error('Failed to create task:', err);
  }
});

// Initial load
fetchTasks();