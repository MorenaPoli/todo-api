/*
 * JavaScript for interacting with the Todo API
 *
 * This script handles user authentication (signup/login), token storage,
 * dynamic UI switching, and CRUD operations on tasks. It also supports
 * additional fields such as due date, category and priority.
 */

// Global variable to store the JWT token after login
let authToken = null;

/**
 * Helper function to build request headers.
 * Adds the Authorization header if the user is authenticated.
 */
function getHeaders() {
  const headers = { 'Content-Type': 'application/json' };
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }
  return headers;
}

/**
 * Show the main task UI and hide authentication forms.
 */
function showTaskUI() {
  document.getElementById('authSection').style.display = 'none';
  document.getElementById('taskForm').style.display = 'flex';
  // Show filters and search section
  const filterSection = document.getElementById('filterSection');
  if (filterSection) {
    filterSection.style.display = 'flex';
  }
  fetchTasks();
}

/**
 * Fetch tasks from the API and render them on the page.
 */
async function fetchTasks(filterBy = '', category = '', priority = '') {
  try {
    // Build query string based on filters
    const params = new URLSearchParams();
    if (filterBy) params.append('filter_by', filterBy);
    if (category) params.append('category', category);
    if (priority) params.append('priority', priority);
    const queryString = params.toString();
    const url = queryString ? `/tasks?${queryString}` : '/tasks';
    const response = await fetch(url, {
      headers: getHeaders(),
    });
    const tasks = await response.json();
    renderTasks(tasks);
  } catch (err) {
    console.error('Failed to fetch tasks:', err);
  }
}

/**
 * Render the list of tasks. Includes due date, category and priority when present.
 * Each task has buttons to toggle completion and delete it.
 */
function renderTasks(tasks) {
  const list = document.getElementById('taskList');
  list.innerHTML = '';
  tasks.forEach((task) => {
    const li = document.createElement('li');
    if (task.done) {
      li.classList.add('done');
    }
    // Compose auxiliary info line
    let infoParts = [];
    if (task.due_date) infoParts.push(`Due: ${task.due_date}`);
    if (task.category) infoParts.push(`Category: ${task.category}`);
    if (task.priority) infoParts.push(`Priority: ${task.priority}`);
    const infoLine = infoParts.join(' | ');

    li.innerHTML = `
      <div class="task-details">
        <span class="task-title">${task.title}</span>
        ${infoLine ? `<small class="task-meta">${infoLine}</small>` : ''}
      </div>
      <div class="task-actions">
        <button class="toggle-btn">${task.done ? 'Undo' : 'Done'}</button>
        <button class="delete-btn">Delete</button>
      </div>
    `;
    // Toggle button handler
    li.querySelector('.toggle-btn').addEventListener('click', async () => {
      try {
        await fetch(`/tasks/${task.id}`, {
          method: 'PUT',
          headers: getHeaders(),
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
          headers: getHeaders(),
        });
        fetchTasks();
      } catch (err) {
        console.error('Failed to delete task:', err);
      }
    });
    list.appendChild(li);
  });
}

/**
 * Handle creation of a new task.
 * Reads input values, sends them to the API, then refreshes the task list.
 */
document.getElementById('taskForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const titleInput = document.getElementById('title');
  const dueDateInput = document.getElementById('dueDate');
  const categoryInput = document.getElementById('category');
  const prioritySelect = document.getElementById('priority');
  const title = titleInput.value.trim();
  const due_date = dueDateInput.value || null;
  const category = categoryInput.value.trim() || null;
  const priority = prioritySelect.value;
  if (!title) return;
  try {
    await fetch('/tasks', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        title,
        done: false,
        due_date,
        category,
        priority,
      }),
    });
    // Clear the form
    titleInput.value = '';
    dueDateInput.value = '';
    categoryInput.value = '';
    prioritySelect.value = 'medium';
    fetchTasks();
  } catch (err) {
    console.error('Failed to create task:', err);
  }
});

/**
 * Handle login form submission.
 */
document.getElementById('loginForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const username = document.getElementById('loginUsername').value.trim();
  const password = document.getElementById('loginPassword').value;
  try {
    const res = await fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      throw new Error('Invalid credentials');
    }
    const data = await res.json();
    authToken = data.access_token;
    // Persist token for future sessions
    try {
      localStorage.setItem('authToken', authToken);
    } catch (e) {
      // In environments without localStorage, ignore
    }
    showTaskUI();
  } catch (err) {
    alert('Error al iniciar sesión: ' + err.message);
  }
});

/**
 * Handle signup form submission.
 */
document.getElementById('signupForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const username = document.getElementById('signupUsername').value.trim();
  const password = document.getElementById('signupPassword').value;
  try {
    const res = await fetch('/auth/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.detail || 'Error al registrarse');
    }
    // Auto login after successful signup
    const loginRes = await fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    const loginData = await loginRes.json();
    authToken = loginData.access_token;
    // Persist token
    try {
      localStorage.setItem('authToken', authToken);
    } catch (e) {
      // Ignore if not available
    }
    showTaskUI();
  } catch (err) {
    alert(err.message);
  }
});

// Toggle visibility between login and signup forms
document.getElementById('showSignup').addEventListener('click', (e) => {
  e.preventDefault();
  document.getElementById('loginForm').style.display = 'none';
  document.getElementById('signupForm').style.display = 'flex';
});

// Show login form from signup
const showLoginLink = document.getElementById('showLogin');
if (showLoginLink) {
  showLoginLink.addEventListener('click', (e) => {
    e.preventDefault();
    document.getElementById('signupForm').style.display = 'none';
    document.getElementById('loginForm').style.display = 'flex';
  });
}

// On page load, check if a token is saved in localStorage (optional for persistence)
window.addEventListener('DOMContentLoaded', () => {
  // Retrieve token from localStorage for persistent login (if available)
  try {
    const savedToken = localStorage.getItem('authToken');
    if (savedToken) {
      authToken = savedToken;
      showTaskUI();
    }
  } catch (e) {
    // localStorage may not be available in all environments
  }

  // Set up filter and search event listeners
  const applyBtn = document.getElementById('applyFilters');
  if (applyBtn) {
    applyBtn.addEventListener('click', (e) => {
      e.preventDefault();
      const filterBy = document.getElementById('filterBy').value;
      const category = document.getElementById('filterCategory').value.trim();
      const priority = document.getElementById('filterPriority').value;
      fetchTasks(filterBy, category, priority);
    });
  }
  const searchBtn = document.getElementById('searchBtn');
  if (searchBtn) {
    searchBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      const query = document.getElementById('searchQuery').value.trim();
      if (!query) {
        // If query is empty, reset to current filters
        const filterBy = document.getElementById('filterBy').value;
        const category = document.getElementById('filterCategory').value.trim();
        const priority = document.getElementById('filterPriority').value;
        fetchTasks(filterBy, category, priority);
        return;
      }
      try {
        const url = `/search?q=${encodeURIComponent(query)}&in_title=true&in_category=true`;
        const res = await fetch(url, {
          headers: getHeaders(),
        });
        const data = await res.json();
        // data.results contains the array of tasks
        renderTasks(data.results);
      } catch (err) {
        console.error('Search failed:', err);
      }
    });
  }
});