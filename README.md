# 📝 Todo API

A simple and elegant REST API for managing tasks built with **FastAPI** and **SQLite**.

🚀 **Live Demo**: *[Coming soon - deploy in progress]*

## ✨ Features

- ✅ Complete CRUD operations (Create, Read, Update, Delete)
- ✅ Automatic interactive API documentation
- ✅ SQLite database with automatic initialization
- ✅ Input validation with Pydantic models
- ✅ RESTful design principles

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

- [ ] Add user authentication
- [ ] Add task categories/tags
- [ ] Add due dates
- [ ] Add task priority levels
- [ ] Add search functionality
- [ ] Add pagination

## 🎉 Demo

*Interactive documentation available at `/docs` when running locally*

---

**Built with ❤️ using FastAPI**