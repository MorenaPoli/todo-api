from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from typing import List

app = FastAPI(title="Todo API", description="Simple CRUD API for managing tasks", version="1.0.0")
DB = "todo.db"

class Task(BaseModel):
    id: int = None
    title: str
    done: bool = False

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("""CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        done INTEGER NOT NULL DEFAULT 0
                    );""")
    conn.commit()
    conn.close()

@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def read_root():
    return {"message": "Todo API is running! Go to /docs to see the interactive documentation"}

@app.get("/tasks", response_model=List[Task])
def get_tasks():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT id, title, done FROM tasks")
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "done": bool(r[2])} for r in rows]

@app.post("/tasks", response_model=Task)
def create_task(task: Task):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", (task.title, int(task.done)))
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return {"id": last_id, "title": task.title, "done": task.done}
