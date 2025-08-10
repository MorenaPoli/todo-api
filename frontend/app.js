/*
 * JavaScript for interacting with the Todo API
 *
 * This script handles user authentication (signup/login), token storage,
 * dynamic UI switching, and CRUD operations on tasks. It also supports
 * additional fields such as due date, category and priority, plus interactive
 * charts for productivity analytics.
 */

// Global variable to store the JWT token after login
let authToken = null;

// Chart instances to manage updates
let chartInstances = {
    completion: null,
    priority: null,
    category: null,
    trend: null
};

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
  // Guardar en caché local
  try {
    localStorage.setItem('tasksCache', JSON.stringify(tasks));
  } catch (e) {}
  tasks.forEach((task) => {
    const li = document.createElement('li');
    if (task.done) {
      li.classList.add('done');
    }
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
        if (document.getElementById('chartsSection').style.display !== 'none') {
          refreshCharts();
        }
      } catch (err) {
        console.error('Failed to update task:', err);
      }
    });
    li.querySelector('.delete-btn').addEventListener('click', async () => {
      try {
        await fetch(`/tasks/${task.id}`, {
          method: 'DELETE',
          headers: getHeaders(),
        });
        fetchTasks();
        if (document.getElementById('chartsSection').style.display !== 'none') {
          refreshCharts();
        }
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
    // Refresh charts if visible
    if (document.getElementById('chartsSection').style.display !== 'none') {
      refreshCharts();
    }
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

/**
 * Fetch analytics data from the backend
 */
async function fetchAnalytics(timeframe = 'week') {
  try {
    const response = await fetch(`/analytics/productivity?timeframe=${timeframe}`, {
      headers: getHeaders(),
    });
    return await response.json();
  } catch (err) {
    console.error('Failed to fetch analytics:', err);
    return null;
  }
}

/**
 * Create completion status chart (pie chart)
 */
function createCompletionChart(data) {
  const ctx = document.getElementById('completionChart').getContext('2d');
  
  // Destroy existing chart if it exists
  if (chartInstances.completion) {
    chartInstances.completion.destroy();
  }
  
  const completionData = data.completion_overview;
  
  chartInstances.completion = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Completed', 'Pending', 'Overdue'],
      datasets: [{
        data: [completionData.completed, completionData.pending, completionData.overdue],
        backgroundColor: [
          'rgba(75, 192, 192, 0.8)',
          'rgba(255, 206, 86, 0.8)',
          'rgba(255, 99, 132, 0.8)'
        ],
        borderColor: [
          'rgba(75, 192, 192, 1)',
          'rgba(255, 206, 86, 1)',
          'rgba(255, 99, 132, 1)'
        ],
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
        }
      }
    }
  });
}

/**
 * Create priority distribution chart (bar chart)
 */
function createPriorityChart(data) {
  const ctx = document.getElementById('priorityChart').getContext('2d');
  
  if (chartInstances.priority) {
    chartInstances.priority.destroy();
  }
  
  const priorityData = data.priority_analytics;
  const labels = Object.keys(priorityData);
  const totals = labels.map(label => priorityData[label].total);
  const completed = labels.map(label => priorityData[label].completed);
  
  chartInstances.priority = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels.map(l => l.charAt(0).toUpperCase() + l.slice(1)),
      datasets: [
        {
          label: 'Total',
          data: totals,
          backgroundColor: 'rgba(54, 162, 235, 0.6)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 1
        },
        {
          label: 'Completed',
          data: completed,
          backgroundColor: 'rgba(75, 192, 192, 0.6)',
          borderColor: 'rgba(75, 192, 192, 1)',
          borderWidth: 1
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true
        }
      },
      plugins: {
        legend: {
          position: 'top',
        }
      }
    }
  });
}

/**
 * Create category distribution chart (horizontal bar chart)
 */
function createCategoryChart(data) {
  const ctx = document.getElementById('categoryChart').getContext('2d');
  
  if (chartInstances.category) {
    chartInstances.category.destroy();
  }
  
  const categoryData = data.category_analytics;
  const labels = Object.keys(categoryData);
  const totals = labels.map(label => categoryData[label].total);
  const completionRates = labels.map(label => categoryData[label].completion_rate);
  
  chartInstances.category = new Chart(ctx, {
    type: 'horizontalBar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Total Tasks',
          data: totals,
          backgroundColor: 'rgba(153, 102, 255, 0.6)',
          borderColor: 'rgba(153, 102, 255, 1)',
          borderWidth: 1
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          beginAtZero: true
        }
      },
      plugins: {
        legend: {
          position: 'top',
        },
        tooltip: {
          callbacks: {
            afterLabel: function(context) {
              const index = context.dataIndex;
              return `Completion Rate: ${completionRates[index]}%`;
            }
          }
        }
      }
    }
  });
}

/**
 * Create productivity trend chart (line chart)
 */
function createTrendChart(data) {
  const ctx = document.getElementById('trendChart').getContext('2d');
  
  if (chartInstances.trend) {
    chartInstances.trend.destroy();
  }
  
  const dailyData = data.daily_productivity.reverse(); // Reverse to show chronological order
  const labels = dailyData.map(d => {
    const date = new Date(d.date);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  });
  const created = dailyData.map(d => d.created);
  const completed = dailyData.map(d => d.completed);
  
  chartInstances.trend = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Tasks Created',
          data: created,
          borderColor: 'rgba(255, 206, 86, 1)',
          backgroundColor: 'rgba(255, 206, 86, 0.2)',
          tension: 0.4,
          fill: false
        },
        {
          label: 'Tasks Completed',
          data: completed,
          borderColor: 'rgba(75, 192, 192, 1)',
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          tension: 0.4,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true
        }
      },
      plugins: {
        legend: {
          position: 'top',
        }
      }
    }
  });
}

/**
 * Initialize all charts with data
 */
async function initializeCharts(timeframe = 'week') {
  const data = await fetchAnalytics(timeframe);
  if (!data) return;
  
  createCompletionChart(data);
  createPriorityChart(data);
  createCategoryChart(data);
  createTrendChart(data);
}

/**
 * Refresh all charts
 */
async function refreshCharts() {
  const timeframe = document.getElementById('chartTimeframe').value;
  await initializeCharts(timeframe);
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
  } catch (e) {}

  // Restaurar modo oscuro si estaba activado
  try {
    if (localStorage.getItem('darkMode') === 'true') {
      document.body.classList.add('dark-mode');
      const modeToggle = document.getElementById('modeToggle');
      if (modeToggle) modeToggle.textContent = '☀️';
    }
  } catch (e) {}

  // Guardar el estado de modo oscuro
  const modeToggle = document.getElementById('modeToggle');
  if (modeToggle) {
    modeToggle.addEventListener('click', () => {
      const isDark = document.body.classList.contains('dark-mode');
      try { localStorage.setItem('darkMode', isDark ? 'true' : 'false'); } catch (e) {}
    });
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
        renderTasks(data.results);
      } catch (err) {
        console.error('Search failed:', err);
      }
    });
  }

  // Charts toggle button
  const toggleChartsBtn = document.getElementById('toggleCharts');
  if (toggleChartsBtn) {
    toggleChartsBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      const chartsSection = document.getElementById('chartsSection');
      if (chartsSection.style.display === 'none' || chartsSection.style.display === '') {
        chartsSection.style.display = 'block';
        await initializeCharts();
      } else {
        chartsSection.style.display = 'none';
      }
    });
  }

  // Refresh charts button
  const refreshChartsBtn = document.getElementById('refreshCharts');
  if (refreshChartsBtn) {
    refreshChartsBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      await refreshCharts();
    });
  }

  // Chart timeframe selector
  const chartTimeframe = document.getElementById('chartTimeframe');
  if (chartTimeframe) {
    chartTimeframe.addEventListener('change', async (e) => {
      await refreshCharts();
    });
  }

  // Si hay tareas en caché, mostrarlas primero para carga rápida
  try {
    const cachedTasks = localStorage.getItem('tasksCache');
    if (cachedTasks) {
      renderTasks(JSON.parse(cachedTasks));
    }
  } catch (e) {}
});
