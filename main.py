from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
import sqlite3
from typing import List, Optional
from datetime import datetime, timedelta

# Configuración de autenticación
SECRET_KEY = "tu_clave_secreta_super_segura_123456789"  # En producción usar variable de entorno
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(title="Todo API with Authentication", description="CRUD API with user authentication", version="2.0.0")
DB = "todo.db"

# Configuración de seguridad
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Modelos Pydantic
class User(BaseModel):
    id: int = None
    username: str
    email: str
    is_active: bool = True

class UserInDB(User):
    hashed_password: str

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class Task(BaseModel):
    id: int = None
    title: str
    done: bool = False
    user_id: int = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Funciones de utilidad
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def init_db():
    conn = sqlite3.connect(DB)
    
    # Tabla de usuarios
    conn.execute("""CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        hashed_password TEXT NOT NULL,
                        is_active INTEGER NOT NULL DEFAULT 1
                    );""")
    
    # Verificar si la tabla tasks ya existe y tiene user_id
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(tasks)")
    columns = [column[1] for column in cur.fetchall()]
    
    if 'user_id' not in columns:
        # Si no tiene user_id, recrear la tabla
        conn.execute("DROP TABLE IF EXISTS tasks")
        print("🔄 Recreating tasks table with user authentication...")
    
    # Crear tabla de tareas (ahora con user_id)
    conn.execute("""CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        done INTEGER NOT NULL DEFAULT 0,
                        user_id INTEGER NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    );""")
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")

def get_user(username: str):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT id, username, email, hashed_password, is_active FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    conn.close()
    if user:
        return UserInDB(
            id=user[0],
            username=user[1],
            email=user[2],
            hashed_password=user[3],
            is_active=bool(user[4])
        )

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
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

@app.on_event("startup")
def startup():
    init_db()

# Endpoints de autenticación
@app.post("/register", response_model=User)
def register_user(user: UserCreate):
    # Verificar si el usuario ya existe
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username = ? OR email = ?", (user.username, user.email))
    if cur.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    # Crear nuevo usuario
    hashed_password = get_password_hash(user.password)
    cur.execute("INSERT INTO users (username, email, hashed_password) VALUES (?, ?, ?)",
                (user.username, user.email, hashed_password))
    conn.commit()
    user_id = cur.lastrowid
    conn.close()
    
    return User(id=user_id, username=user.username, email=user.email)

@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    return current_user

# Endpoints principales (ahora protegidos)
@app.get("/")
def read_root():
    return {"message": "Todo API with Authentication is running! Register at /register or login at /token"}

@app.get("/tasks", response_model=List[Task])
def get_tasks(current_user: UserInDB = Depends(get_current_user)):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT id, title, done, user_id FROM tasks WHERE user_id = ?", (current_user.id,))
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "done": bool(r[2]), "user_id": r[3]} for r in rows]

@app.post("/tasks", response_model=Task)
def create_task(task: Task, current_user: UserInDB = Depends(get_current_user)):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (title, done, user_id) VALUES (?, ?, ?)", 
                (task.title, int(task.done), current_user.id))
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return {"id": last_id, "title": task.title, "done": task.done, "user_id": current_user.id}

@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task: Task, current_user: UserInDB = Depends(get_current_user)):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    # Verificar que la tarea existe y pertenece al usuario
    cur.execute("SELECT id FROM tasks WHERE id = ? AND user_id = ?", (task_id, current_user.id))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found or access denied")
    
    # Actualizar la tarea
    cur.execute("UPDATE tasks SET title = ?, done = ? WHERE id = ? AND user_id = ?", 
                (task.title, int(task.done), task_id, current_user.id))
    conn.commit()
    conn.close()
    
    return {"id": task_id, "title": task.title, "done": task.done, "user_id": current_user.id}

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, current_user: UserInDB = Depends(get_current_user)):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    # Verificar que la tarea existe y pertenece al usuario
    cur.execute("SELECT id FROM tasks WHERE id = ? AND user_id = ?", (task_id, current_user.id))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found or access denied")
    
    # Eliminar la tarea
    cur.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, current_user.id))
    conn.commit()
    conn.close()
    
    return {"message": f"Task {task_id} deleted successfully"}