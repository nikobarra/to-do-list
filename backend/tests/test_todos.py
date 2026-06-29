"""test_todos.py
Tests automatizados de los 5 endpoints de la API To-Do.
Se usa TestClient (basado en httpx) y pytest.

Cada test hace un `seed` propio para no depender del orden de ejecución.
La fixture `client_with_db` sobrescribe `database.DB_PATH` para que
cada test use un archivo de SQLite temporal único y de este modo
los tests sean completamente aislados.
"""
import os
import tempfile
import sqlite3

import pytest
from fastapi.testclient import TestClient

import app.database as database
from app.main import app


@pytest.fixture()
def client_with_db():
    """Crea un cliente de pruebas apuntando a una DB SQLite temporal."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    original_path = database.DB_PATH
    database.DB_PATH = tmp.name

    # Re-crear la tabla en la DB temporal
    database.init_db()

    client = TestClient(app)
    try:
        yield client
    finally:
        # Cerrar cualquier conexión abierta (sqlite3.Connection a archivo)
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
        database.DB_PATH = original_path


# ---------- GET /api/todos ----------

def test_list_todos_empty(client_with_db):
    """GET /api/todos sin tareas -> [] con status 200."""
    response = client_with_db.get("/api/todos")
    assert response.status_code == 200
    assert response.json() == []


def test_list_todos_filter_by_status(client_with_db):
    """GET /api/todos?status=pending/done devuelve solo los registros esperados."""
    # Crear 2 pendientes y 1 completada
    t1 = client_with_db.post("/api/todos", json={"title": "A", "description": ""}).json()
    t2 = client_with_db.post("/api/todos", json={"title": "B", "description": ""}).json()
    t3 = client_with_db.post("/api/todos", json={"title": "C", "description": ""}).json()
    client_with_db.patch(f"/api/todos/{t3['id']}", json={"status": "done"})

    pending_resp = client_with_db.get("/api/todos", params={"status": "pending"})
    done_resp = client_with_db.get("/api/todos", params={"status": "done"})

    assert pending_resp.status_code == 200
    assert done_resp.status_code == 200

    pending = pending_resp.json()
    done = done_resp.json()
    assert {t["id"] for t in pending} == {t1["id"], t2["id"]}
    assert {t["id"] for t in done} == {t3["id"]}
    assert all(t["status"] == "pending" for t in pending)
    assert all(t["status"] == "done" for t in done)


# ---------- GET /api/todos/{id} ----------

def test_get_todo_by_id_ok(client_with_db):
    """GET /api/todos/{id} devuelve el detalle cuando existe."""
    created = client_with_db.post(
        "/api/todos",
        json={"title": "Leer un libro", "description": "Clean Architecture"},
    ).json()

    response = client_with_db.get(f"/api/todos/{created['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["title"] == "Leer un libro"
    assert body["description"] == "Clean Architecture"
    assert body["status"] == "pending"
    assert "created_at" in body


def test_get_todo_by_id_404(client_with_db):
    """GET /api/todos/{id} -> 404 con mensaje claro si no existe."""
    response = client_with_db.get("/api/todos/9999")
    assert response.status_code == 404
    detail = response.json()["detail"]
    assert "9999" in detail
    assert "no se encontró" in detail.lower()


# ---------- POST /api/todos ----------

def test_create_todo_with_description(client_with_db):
    """POST /api/todos con título y descripción -> 201 y datos correctos."""
    response = client_with_db.post(
        "/api/todos",
        json={"title": "Comprar pan", "description": "En la panadería de la esquina"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["title"] == "Comprar pan"
    assert body["description"] == "En la panadería de la esquina"
    assert body["status"] == "pending"


def test_create_todo_without_description(client_with_db):
    """POST /api/todos sin descripción -> descripción vacía por defecto."""
    response = client_with_db.post("/api/todos", json={"title": "Solo título"})
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Solo título"
    assert body["description"] == ""


def test_create_todo_missing_title_422(client_with_db):
    """POST /api/todos sin título -> 422 (validación Pydantic)."""
    response = client_with_db.post("/api/todos", json={"description": "sin título"})
    assert response.status_code == 422


def test_create_todo_empty_title_422(client_with_db):
    """POST /api/todos con título vacío -> 422 (validación Pydantic)."""
    response = client_with_db.post("/api/todos", json={"title": ""})
    assert response.status_code == 422


# ---------- PATCH /api/todos/{id} ----------

def test_patch_todo_update_status(client_with_db):
    """PATCH /api/todos/{id} con status='done' -> el estado cambia."""
    created = client_with_db.post("/api/todos", json={"title": "Pasear al perro"}).json()

    response = client_with_db.patch(f"/api/todos/{created['id']}", json={"status": "done"})
    assert response.status_code == 200
    assert response.json()["status"] == "done"


def test_patch_todo_update_title_description(client_with_db):
    """PATCH /api/todos/{id} actualiza título y descripción."""
    created = client_with_db.post(
        "/api/todos",
        json={"title": "viejo", "description": "desc vieja"},
    ).json()

    response = client_with_db.patch(
        f"/api/todos/{created['id']}",
        json={"title": "nuevo", "description": "desc nueva"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "nuevo"
    assert body["description"] == "desc nueva"
    assert body["status"] == "pending"  # no se ha tocado


def test_patch_todo_404(client_with_db):
    """PATCH /api/todos/{id} de una tarea inexistente -> 404 claro."""
    response = client_with_db.patch("/api/todos/4242", json={"status": "done"})
    assert response.status_code == 404
    assert "4242" in response.json()["detail"]


def test_patch_todo_invalid_status_422(client_with_db):
    """PATCH /api/todos/{id} con status fuera de Literal -> 422."""
    created = client_with_db.post("/api/todos", json={"title": "t"}).json()
    response = client_with_db.patch(
        f"/api/todos/{created['id']}", json={"status": "in-progress"}
    )
    assert response.status_code == 422


# ---------- DELETE /api/todos/{id} ----------

def test_delete_todo_ok(client_with_db):
    """DELETE /api/todos/{id} -> 200 y la tarea ya no aparece."""
    created = client_with_db.post("/api/todos", json={"title": "Eliminar esto"}).json()

    response = client_with_db.delete(f"/api/todos/{created['id']}")
    assert response.status_code == 200

    # Verificar que ya no está (GET -> 404)
    response_get = client_with_db.get(f"/api/todos/{created['id']}")
    assert response_get.status_code == 404


def test_delete_todo_404(client_with_db):
    """DELETE /api/todos/{id} de una tarea inexistente -> 404 claro."""
    response = client_with_db.delete("/api/todos/7777")
    assert response.status_code == 404
    assert "7777" in response.json()["detail"]


# ---------- Health check ----------

def test_health_root(client_with_db):
    """Endpoint raíz devuelve un OK."""
    response = client_with_db.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
