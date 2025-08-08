from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import sqlite3
from typing import List, Optional
from datetime import datetime, timedelta, date

app = FastAPI(
    title="Todo API - Simple & Clean", 
    description="Clean CRUD API with dates and categories", 
    version="3.0.0"
)
DB = "todo.db"

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
    
    # Crear tabla limpia y moderna
    conn.execute("""CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        done INTEGER NOT NULL DEFAULT 0,
                        due_date TEXT,
                        category TEXT,
                        priority TEXT DEFAULT 'medium',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );""")
    
    conn.commit()
    conn.close()
    print("✅ Clean database initialized successfully!")

@app.on_event("startup")
def startup():
    init_db()

# Endpoint principal
@app.get("/")
def read_root():
    return {
        "message": "Todo API - Simple & Clean! 🚀", 
        "docs": "/docs",
        "features": ["✅ CRUD", "📅 Due dates", "🏷️ Categories", "📊 Stats"]
    }

# CRUD Endpoints
@app.get("/tasks", response_model=List[Task])
def get_tasks(
    filter_by: Optional[str] = Query(None, description="Filter by: 'overdue', 'today', 'week', 'completed', 'pending', 'high', 'medium', 'low'"),
    category: Optional[str] = Query(None, description="Filter by category"),
    priority: Optional[str] = Query(None, description="Filter by priority: 'high', 'medium', 'low'"),
    sort_by: Optional[str] = Query("priority", description="Sort by: 'date', 'category', 'priority', 'created'")
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
    
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    # Verificar que la tarea existe
    cur.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Actualizar tarea
    cur.execute("UPDATE tasks SET title = ?, done = ?, due_date = ?, category = ?, priority = ? WHERE id = ?", 
                (task.title, int(task.done), task.due_date, task.category, task.priority, task_id))
    conn.commit()
    conn.close()
    
    return {"id": task_id, "title": task.title, "done": task.done, "due_date": task.due_date, "category": task.category, "priority": task.priority}

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
    in_category: bool = Query(True, description="Search in category")
):
    """Búsqueda avanzada en tareas"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    conditions = []
    params = []
    
    if in_title:
        conditions.append("title LIKE ?")
        params.append(f"%{q}%")
    
    if in_category:
        conditions.append("category LIKE ?")
        params.append(f"%{q}%")
    
    where_clause = " OR ".join(conditions)
    query = f"SELECT id, title, done, due_date, category, priority FROM tasks WHERE ({where_clause}) ORDER BY done ASC, priority = 'high' DESC"
    
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    
    results = [{"id": r[0], "title": r[1], "done": bool(r[2]), "due_date": r[3], "category": r[4], "priority": r[5]} for r in rows]
    
    return {
        "query": q,
        "results_count": len(results),
        "results": results
    }