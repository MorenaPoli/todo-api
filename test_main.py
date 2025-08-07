import pytest
from fastapi.testclient import TestClient
import os
import sqlite3
from main import app, init_db

# Configurar base de datos de prueba
TEST_DB = "test_todo.db"

def setup_module():
    """Setup para todos los tests - usar DB de prueba"""
    import main
    main.DB = TEST_DB
    # Inicializar la base de datos de prueba
    init_db()

def teardown_module():
    """Limpiar después de todos los tests"""
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except PermissionError:
            pass  # No pasa nada si no se puede eliminar

# Cliente de prueba (después del setup)
client = TestClient(app)

def test_read_root():
    """Test del endpoint raíz"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Todo API is running" in response.json()["message"]

def test_get_empty_tasks():
    """Test obtener tareas cuando la lista está vacía"""
    response = client.get("/tasks")
    assert response.status_code == 200
    assert response.json() == []

def test_create_task():
    """Test crear una nueva tarea"""
    task_data = {"title": "Test task", "done": False}
    response = client.post("/tasks", json=task_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test task"
    assert data["done"] == False
    assert data["id"] == 1

def test_get_tasks_with_data():
    """Test obtener tareas cuando hay datos"""
    response = client.get("/tasks")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Test task"

def test_create_multiple_tasks():
    """Test crear múltiples tareas"""
    tasks = [
        {"title": "Second task", "done": False},
        {"title": "Third task", "done": True}
    ]
    
    for i, task in enumerate(tasks, 2):
        response = client.post("/tasks", json=task)
        assert response.status_code == 200
        assert response.json()["id"] == i

def test_update_task():
    """Test actualizar una tarea existente"""
    updated_task = {"title": "Updated task", "done": True}
    response = client.put("/tasks/1", json=updated_task)
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated task"
    assert data["done"] == True
    assert data["id"] == 1

def test_update_nonexistent_task():
    """Test actualizar una tarea que no existe"""
    task_data = {"title": "Should fail", "done": False}
    response = client.put("/tasks/999", json=task_data)
    
    assert response.status_code == 404
    assert "Task not found" in response.json()["detail"]

def test_delete_task():
    """Test eliminar una tarea"""
    response = client.delete("/tasks/2")
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]
    
    # Verificar que se eliminó
    response = client.get("/tasks")
    tasks = response.json()
    task_ids = [task["id"] for task in tasks]
    assert 2 not in task_ids

def test_delete_nonexistent_task():
    """Test eliminar una tarea que no existe"""
    response = client.delete("/tasks/999")
    assert response.status_code == 404
    assert "Task not found" in response.json()["detail"]

def test_create_task_validation():
    """Test validación de datos al crear tarea"""
    # Sin título
    response = client.post("/tasks", json={"done": False})
    assert response.status_code == 422  # Validation error
    
    # Título vacío
    response = client.post("/tasks", json={"title": "", "done": False})
    assert response.status_code == 200  # FastAPI permite strings vacías por defecto

def test_final_tasks_count():
    """Test final: verificar estado de la base de datos"""
    response = client.get("/tasks")
    assert response.status_code == 200
    tasks = response.json()
    # Después de crear 3 tareas iniciales + 1 del test de validación y eliminar 1, quedan 3
    assert len(tasks) == 3
    # Verificar que la tarea eliminada (id=2) no está
    task_ids = [task["id"] for task in tasks]
    assert 2 not in task_ids