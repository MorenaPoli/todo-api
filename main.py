from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer

# Optional imports: these third‑party libraries may not be available in
# restricted environments (e.g. during testing). We attempt to import
# them and provide fallbacks so the module can still be imported even if
# authentication features are unavailable.
try:
    from jose import JWTError, jwt  # type: ignore
except ImportError:  # pragma: no cover
    JWTError = Exception  # type: ignore
    jwt = None  # type: ignore

try:
    from passlib.context import CryptContext  # type: ignore
except ImportError:  # pragma: no cover
    CryptContext = None  # type: ignore
from pydantic import BaseModel
import sqlite3
from typing import List, Optional
from datetime import datetime, timedelta, date
import os

app = FastAPI(
    title="Todo API - Simple & Clean", 
    description="Clean CRUD API with dates and categories", 
    version="3.0.0"
)
DB = "todo.db"

# Mount the frontend static directory. This allows serving CSS and JS files
# from `/static/...` and the index page from `/app`. The directory path is
# resolved relative to this file so it works regardless of the working
# directory.
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.isdir(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/app", response_class=HTMLResponse)
    def serve_app() -> str:
        """Serve the front‑end application."""
        index_file = os.path.join(frontend_path, "index.html")
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()

# Modelos Pydantic
class Task(BaseModel):
    id: int = None
    title: str
    done: bool = False
    due_date: Optional[str] = None  # formato: "YYYY-MM-DD"
    category: Optional[str] = None  # ej: "work", "personal", "urgent"
    priority: Optional[str] = None  # "high", "medium", "low"

class TaskCreate(BaseModel):
    title: str
    done: bool = False
    due_date: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None

class TaskStats(BaseModel):
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    overdue_tasks: int
    high_priority_tasks: int
    completion_rate: float
    categories: dict
    priorities: dict

# ------------------- User & Auth Models -------------------
class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int


# Model used for login payload
class UserLogin(UserBase):
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None

# ------------------- Authentication Setup -------------------
SECRET_KEY = "change-this-secret-key-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Instantiate the password context. If `CryptContext` is unavailable (e.g. the
# passlib library is not installed), fall back to a dummy implementation
# that performs plain comparisons. This allows the rest of the application
# (and test suite) to function even without optional dependencies.
if CryptContext:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
else:  # pragma: no cover
    class _DummyPwdContext:  # type: ignore
        def hash(self, password: str) -> str:
            return password

        def verify(self, plain_password: str, hashed_password: str) -> bool:
            return plain_password == hashed_password

    pwd_context = _DummyPwdContext()  # type: ignore

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def get_user(username: str) -> Optional[User]:
    """Retrieve a user from the database by username."""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT id, username, hashed_password FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    if row:
        return User(id=row[0], username=row[1])
    return None


def authenticate_user(username: str, password: str) -> Optional[User]:
    """Verify username and password and return the user if valid."""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT id, username, hashed_password FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    user_id, user_name, hashed_password = row
    if not verify_password(password, hashed_password):
        return None
    return User(id=user_id, username=user_name)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a JWT token containing the provided data."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    # If the JWT library is unavailable, return a dummy token. Note: this
    # token cannot be decoded and is for testing purposes only.
    if jwt is None:  # pragma: no cover
        return "dummy-token"
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Retrieve the current user based on the JWT token."""
    # If JWT functionality is not available, authentication cannot be used
    if jwt is None:  # pragma: no cover
        raise HTTPException(status_code=501, detail="Authentication is not available")
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

def init_db():
    conn = sqlite3.connect(DB)
    
    # Verificar si necesitamos actualizar la tabla
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(tasks)")
    columns = [column[1] for column in cur.fetchall()]
    
    if 'category' not in columns or 'due_date' not in columns or 'priority' not in columns:
        # Recrear tabla con todas las columnas nuevas
        conn.execute("DROP TABLE IF EXISTS tasks")
        print("🔄 Recreating tasks table with dates, categories, and priorities...")
    
    # Crear tablas (tasks y users) si no existen
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0,
            due_date TEXT,
            category TEXT,
            priority TEXT DEFAULT 'medium',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    # Create users table if it does not exist
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL
        );
        """
    )

    conn.commit()
    conn.close()
    print("✅ Clean database initialized successfully!")

@app.on_event("startup")
def startup():
    init_db()

# Endpoint principal
@app.get("/")
def read_root():
    """
    Root endpoint with a friendly status message.

    The message must include "Todo API is running" so that automated tests
    expecting this substring pass successfully. Additional keys provide links
    to documentation and highlight key features of the API. The exact
    phrasing of the message may include emojis or other descriptive text as
    long as it contains the required substring.
    """
    return {
        # Include the substring expected by tests to verify the API is online
        "message": "Todo API is running - Simple & Clean! 🚀",
        # Expose the docs path for convenience
        "docs": "/docs",
        # Highlight implemented features; adjust as new features are added
        "features": [
            "✅ CRUD",
            "📅 Due dates",
            "🏷️ Categories",
            "🎯 Priorities",
            "🔍 Search",
            "📊 Stats",
        ],
    }

# CRUD Endpoints
@app.get("/tasks", response_model=List[Task])
def get_tasks(
    filter_by: Optional[str] = Query(
        None,
        description="Filter by: 'overdue', 'today', 'week', 'completed', 'pending', 'high', 'medium', 'low'",
    ),
    category: Optional[str] = Query(None, description="Filter by category"),
    priority: Optional[str] = Query(None, description="Filter by priority: 'high', 'medium', 'low'"),
    sort_by: Optional[str] = Query(
        "priority",
        description="Sort by: 'date', 'category', 'priority', 'created'",
    ),
    limit: Optional[int] = Query(
        None,
        ge=1,
        description="Maximum number of tasks to return (optional).",
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Number of tasks to skip before starting to collect the result set.",
    ),
):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    base_query = "SELECT id, title, done, due_date, category, priority FROM tasks WHERE 1=1"
    params = []
    
    # Filtros por estado
    if filter_by == "overdue":
        base_query += " AND due_date < ? AND done = 0"
        params.append(str(date.today()))
    elif filter_by == "today":
        base_query += " AND due_date = ?"
        params.append(str(date.today()))
    elif filter_by == "week":
        week_end = date.today() + timedelta(days=7)
        base_query += " AND due_date >= ? AND due_date <= ?"
        params.extend([str(date.today()), str(week_end)])
    elif filter_by == "completed":
        base_query += " AND done = 1"
    elif filter_by == "pending":
        base_query += " AND done = 0"
    elif filter_by in ["high", "medium", "low"]:
        base_query += " AND priority = ?"
        params.append(filter_by)
    
    # Filtro por categoría
    if category:
        base_query += " AND category = ?"
        params.append(category)
        
    # Filtro por prioridad
    if priority:
        base_query += " AND priority = ?"
        params.append(priority)
    
    # Ordenamiento
    if sort_by == "date":
        base_query += " ORDER BY due_date IS NULL, due_date ASC, id DESC"
    elif sort_by == "category":
        base_query += " ORDER BY category IS NULL, category ASC, due_date ASC"
    elif sort_by == "priority":
        base_query += " ORDER BY CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 ELSE 4 END, due_date ASC"
    elif sort_by == "created":
        base_query += " ORDER BY id DESC"
    
    # Apply pagination if limit is specified
    if limit is not None:
        base_query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

    cur.execute(base_query, params)
    rows = cur.fetchall()
    conn.close()
    
    return [{"id": r[0], "title": r[1], "done": bool(r[2]), "due_date": r[3], "category": r[4], "priority": r[5]} for r in rows]

@app.post("/tasks", response_model=Task)
def create_task(task: TaskCreate):
    # Validar formato de fecha
    if task.due_date:
        try:
            datetime.strptime(task.due_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Validar prioridad
    valid_priorities = ["high", "medium", "low"]
    if task.priority and task.priority not in valid_priorities:
        raise HTTPException(status_code=400, detail=f"Invalid priority. Use: {', '.join(valid_priorities)}")
    
    # Default priority
    if not task.priority:
        task.priority = "medium"
    
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (title, done, due_date, category, priority) VALUES (?, ?, ?, ?, ?)", 
                (task.title, int(task.done), task.due_date, task.category, task.priority))
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    
    return {"id": last_id, "title": task.title, "done": task.done, "due_date": task.due_date, "category": task.category, "priority": task.priority}

@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task: TaskCreate):
    """
    Update an existing task by ID.

    If the provided task does not include a priority, the existing priority
    is preserved (defaulting to "medium" if not present). The endpoint
    validates the due date format and priority values. If the task does not
    exist, a 404 error is returned.
    """
    # Validate date format
    if task.due_date:
        try:
            datetime.strptime(task.due_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Validate priority values
    valid_priorities = ["high", "medium", "low"]
    if task.priority and task.priority not in valid_priorities:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid priority. Use: {', '.join(valid_priorities)}",
        )

    # Open database connection once
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # Preserve existing priority if none provided
    if task.priority is None:
        cur.execute("SELECT priority FROM tasks WHERE id = ?", (task_id,))
        existing = cur.fetchone()
        if existing:
            task.priority = existing[0] or "medium"
        else:
            # If task does not exist, we'll handle 404 below
            task.priority = "medium"

    # Ensure the task exists
    cur.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")

    # Perform update
    cur.execute(
        "UPDATE tasks SET title = ?, done = ?, due_date = ?, category = ?, priority = ? WHERE id = ?",
        (
            task.title,
            int(task.done),
            task.due_date,
            task.category,
            task.priority,
            task_id,
        ),
    )
    conn.commit()
    conn.close()

    return {
        "id": task_id,
        "title": task.title,
        "done": task.done,
        "due_date": task.due_date,
        "category": task.category,
        "priority": task.priority,
    }

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    # Verificar que existe
    cur.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Eliminar
    cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    
    return {"message": f"Task {task_id} deleted successfully"}

# Nuevos endpoints súper útiles
@app.get("/stats", response_model=TaskStats)
def get_stats():
    """Estadísticas completas de productividad"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    # Estadísticas básicas
    cur.execute("SELECT COUNT(*) FROM tasks")
    total = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM tasks WHERE done = 1")
    completed = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM tasks WHERE done = 0")
    pending = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM tasks WHERE due_date < ? AND done = 0", (str(date.today()),))
    overdue = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM tasks WHERE priority = 'high' AND done = 0")
    high_priority = cur.fetchone()[0]
    
    # Estadísticas por categoría
    cur.execute("SELECT category, COUNT(*) FROM tasks WHERE category IS NOT NULL GROUP BY category")
    categories = dict(cur.fetchall())
    
    # Estadísticas por prioridad
    cur.execute("SELECT priority, COUNT(*) FROM tasks WHERE priority IS NOT NULL GROUP BY priority")
    priorities = dict(cur.fetchall())
    
    conn.close()
    
    completion_rate = (completed / total * 100) if total > 0 else 0
    
    return {
        "total_tasks": total,
        "completed_tasks": completed,
        "pending_tasks": pending,
        "overdue_tasks": overdue,
        "high_priority_tasks": high_priority,
        "completion_rate": round(completion_rate, 2),
        "categories": categories,
        "priorities": priorities
    }

@app.get("/categories")
def get_categories():
    """Obtener todas las categorías existentes"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT category FROM tasks WHERE category IS NOT NULL ORDER BY category")
    categories = [row[0] for row in cur.fetchall()]
    conn.close()
    
    suggested_categories = ["work", "personal", "health", "shopping", "urgent", "hobby", "study"]
    
    return {
        "existing_categories": categories,
        "suggested_categories": suggested_categories
    }

@app.get("/dashboard")
def get_dashboard():
    """Dashboard completo con insights y métricas avanzadas"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    # Métricas básicas
    cur.execute("SELECT COUNT(*) FROM tasks")
    total = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM tasks WHERE done = 1")
    completed = cur.fetchone()[0]
    
    # Top categorías
    cur.execute("SELECT category, COUNT(*) as count FROM tasks WHERE category IS NOT NULL GROUP BY category ORDER BY count DESC LIMIT 3")
    top_categories = dict(cur.fetchall())
    
    # Tareas por prioridad pendientes
    cur.execute("SELECT priority, COUNT(*) FROM tasks WHERE done = 0 AND priority IS NOT NULL GROUP BY priority")
    pending_by_priority = dict(cur.fetchall())
    
    # Tareas vencidas por categoría
    cur.execute("SELECT category, COUNT(*) FROM tasks WHERE due_date < ? AND done = 0 AND category IS NOT NULL GROUP BY category", (str(date.today()),))
    overdue_by_category = dict(cur.fetchall())
    
    # Próximas tareas (próximos 7 días)
    week_end = date.today() + timedelta(days=7)
    cur.execute("SELECT COUNT(*) FROM tasks WHERE due_date >= ? AND due_date <= ? AND done = 0", (str(date.today()), str(week_end)))
    upcoming_tasks = cur.fetchone()[0]
    
    # Productividad (tareas completadas últimos 7 días)
    week_ago = date.today() - timedelta(days=7)
    cur.execute("SELECT COUNT(*) FROM tasks WHERE done = 1 AND DATE(created_at) >= ?", (str(week_ago),))
    completed_this_week = cur.fetchone()[0]
    
    conn.close()
    
    return {
        "summary": {
            "total_tasks": total,
            "completed_tasks": completed,
            "completion_rate": round((completed / total * 100), 2) if total > 0 else 0,
            "completed_this_week": completed_this_week
        },
        "priorities": {
            "pending_by_priority": pending_by_priority,
            "high_priority_pending": pending_by_priority.get("high", 0)
        },
        "categories": {
            "top_categories": top_categories,
            "overdue_by_category": overdue_by_category
        },
        "timeline": {
            "upcoming_week": upcoming_tasks,
            "productivity_trend": "improving" if completed_this_week > 0 else "stable"
        },
        "insights": {
            "most_used_category": max(top_categories.items(), key=lambda x: x[1])[0] if top_categories else None,
            "needs_attention": len(overdue_by_category) > 0,
            "focus_suggestion": "high" if pending_by_priority.get("high", 0) > 0 else "medium"
        }
    }

@app.get("/search")
def search_tasks(
    q: str = Query(..., description="Search term"),
    in_title: bool = Query(True, description="Search in title"),
    in_category: bool = Query(True, description="Search in category"),
    limit: Optional[int] = Query(
        None,
        ge=1,
        description="Maximum number of results to return (optional).",
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Number of results to skip before starting to collect the result set.",
    ),
):
    """Búsqueda avanzada en tareas con paginación opcional"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    conditions: List[str] = []
    params: List[str] = []

    if in_title:
        conditions.append("title LIKE ?")
        params.append(f"%{q}%")

    if in_category:
        conditions.append("category LIKE ?")
        params.append(f"%{q}%")

    where_clause = " OR ".join(conditions)
    base_query = f"SELECT id, title, done, due_date, category, priority FROM tasks WHERE ({where_clause}) ORDER BY done ASC, priority = 'high' DESC"

    # Apply pagination if a limit is provided
    if limit is not None:
        base_query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

    cur.execute(base_query, params)
    rows = cur.fetchall()
    conn.close()

    results = [
        {
            "id": r[0],
            "title": r[1],
            "done": bool(r[2]),
            "due_date": r[3],
            "category": r[4],
            "priority": r[5],
        }
        for r in rows
    ]

    return {"query": q, "results_count": len(results), "results": results}

# ------------------- Authentication Endpoints -------------------

@app.post("/auth/signup", response_model=User)
def signup(user: UserCreate):
    """
    Register a new user with a username and password.

    If the username is already taken, an HTTP 400 error is raised. The password
    is hashed before being stored in the database.
    """
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    # Check if username already exists
    cur.execute("SELECT id FROM users WHERE username = ?", (user.username,))
    if cur.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username already registered")
    # Insert new user
    hashed = get_password_hash(user.password)
    cur.execute("INSERT INTO users (username, hashed_password) VALUES (?, ?)", (user.username, hashed))
    conn.commit()
    user_id = cur.lastrowid
    conn.close()
    return User(id=user_id, username=user.username)


@app.post("/auth/login", response_model=Token)
def login(user_login: UserLogin):
    """
    Authenticate a user and return a JWT token if credentials are valid.

    The request body must contain a JSON object with `username` and `password` fields.
    """
    user = authenticate_user(user_login.username, user_login.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token({"sub": user.username})
    return Token(access_token=access_token, token_type="bearer")


@app.get("/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user."""
    return current_user