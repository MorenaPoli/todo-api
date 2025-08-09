# 📝 Todo API

A simple and elegant REST API for managing tasks built with **FastAPI** and **SQLite**.

🚀 **Live Demo**: https://todo-api-ycrl.onrender.com/docs

## ✨ Features

The API has grown beyond a simple CRUD service. It now includes several
enhanced features such as task metadata and analytics. Highlights include:

- ✅ Complete CRUD operations (Create, Read, Update, Delete)
- ✅ Automatic interactive API documentation (Swagger/OpenAPI)
- ✅ SQLite database with automatic initialization
- ✅ Input validation with Pydantic models
- ✅ RESTful design principles
- ✅ Due dates to track deadlines
- ✅ Categories/tags to group related tasks
- ✅ Priority levels (high/medium/low)
- ✅ Search endpoints to quickly find tasks
- ✅ Statistics and dashboard endpoints for insights into your productivity

## 🛠️ Tech Stack

- **Python 3.8+**
- **FastAPI** - Modern web framework for building APIs
- **SQLite** - Lightweight database
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd todo-api
```

### 2. Create virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the application
```bash
uvicorn main:app --reload
```

### 5. Open your browser
- **API Documentation**: http://127.0.0.1:8000/docs
- **API Root**: http://127.0.0.1:8000/

## 📋 API Endpoints

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| GET | `/` | Welcome message | - |
| GET | `/tasks` | Get all tasks | - |
| POST | `/tasks` | Create new task | `{"title": "Buy groceries", "done": false}` |
| PUT | `/tasks/{id}` | Update existing task | `{"title": "Buy groceries", "done": true}` |
| DELETE | `/tasks/{id}` | Delete task | - |

## 🔧 Usage Examples

### Create a task
```bash
curl -X POST "http://127.0.0.1:8000/tasks" \
     -H "Content-Type: application/json" \
     -d '{"title": "Learn FastAPI", "done": false}'
```

### Get all tasks
```bash
curl -X GET "http://127.0.0.1:8000/tasks"
```

### Update a task
```bash
curl -X PUT "http://127.0.0.1:8000/tasks/1" \
     -H "Content-Type: application/json" \
     -d '{"title": "Learn FastAPI", "done": true}'
```

### Delete a task
```bash
curl -X DELETE "http://127.0.0.1:8000/tasks/1"
```

## 📁 Project Structure

```
todo-api/
├── main.py           # FastAPI application
├── requirements.txt  # Python dependencies
├── todo.db          # SQLite database (auto-created)
├── .gitignore       # Git ignore file
└── README.md        # This file
```

## 🎯 What I Learned

- Building REST APIs with FastAPI
- Database operations with SQLite
- API documentation with OpenAPI/Swagger
- Request/Response validation with Pydantic
- Git workflow and version control

## 🚧 Future Improvements

The following improvements are planned for future versions. Items marked as
completed have already been implemented in the current code base:

- [ ] **User authentication** – protect endpoints so only authenticated
  users can create, update, or delete tasks.
- [x] **Task categories/tags** – tasks can now be assigned an optional
  category to group related items.
- [x] **Due dates** – tasks may include an optional `due_date` in
  `YYYY-MM-DD` format.
- [x] **Task priority levels** – tasks support `high`, `medium`, and
  `low` priority.
- [x] **Search functionality** – the `/search` endpoint allows
  full‐text search in titles and categories.
- [ ] **Pagination** – support for limiting and offsetting results when
  fetching large lists of tasks.

## 🎉 Demo

*Interactive documentation available at `/docs` when running locally*

---

**Built with ❤️ using FastAPI**