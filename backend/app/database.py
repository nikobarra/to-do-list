"""database.py
Configuración y gestión de la base de datos SQLite.
Encapsula la conexión, creación de tablas y operaciones CRUD básicas.
"""
import sqlite3
import os
from typing import List, Optional, Dict, Any


# Ruta de la base de datos. Se almacena en una variable para permitir
# su reemplazo en tests (por ejemplo, una DB en memoria).
DB_PATH = os.path.join(os.path.dirname(__file__), "todos.db")


def get_connection() -> sqlite3.Connection:
    """Devuelve una conexión SQLite configurada con row_factory para
    acceder a las columnas como un diccionario."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Activar claves foráneas (no se usan aún, pero es buena práctica)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Crea la tabla `todos` si no existe."""
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """Convierte una fila de sqlite3.Row en un diccionario."""
    return {key: row[key] for key in row.keys()}


def get_all_todos(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Obtiene todas las tareas. Si se pasa `status`, filtra por estado."""
    conn = get_connection()
    try:
        if status is not None:
            cursor = conn.execute(
                "SELECT * FROM todos WHERE status = ? ORDER BY id DESC",
                (status,)
            )
        else:
            cursor = conn.execute("SELECT * FROM todos ORDER BY id DESC")
        return [_row_to_dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_todo_by_id(todo_id: int) -> Optional[Dict[str, Any]]:
    """Devuelve una tarea por su ID o None si no existe."""
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
        row = cursor.fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def create_todo(title: str, description: str = "") -> Dict[str, Any]:
    """Crea una nueva tarea y devuelve el registro recién creado."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO todos (title, description, status) VALUES (?, ?, 'pending')",
            (title, description)
        )
        conn.commit()
        new_id = cursor.lastrowid
    finally:
        conn.close()
    return get_todo_by_id(new_id)  # type: ignore[return-value]


def update_todo(
    todo_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Actualiza los campos indicados de una tarea. Si un campo es None,
    no se modifica. Devuelve la tarea actualizada o None si no existe."""
    existing = get_todo_by_id(todo_id)
    if existing is None:
        return None

    new_title = title if title is not None else existing["title"]
    new_description = description if description is not None else existing["description"]
    new_status = status if status is not None else existing["status"]

    conn = get_connection()
    try:
        conn.execute(
            """UPDATE todos
               SET title = ?, description = ?, status = ?
               WHERE id = ?""",
            (new_title, new_description, new_status, todo_id)
        )
        conn.commit()
    finally:
        conn.close()

    return get_todo_by_id(todo_id)


def delete_todo(todo_id: int) -> bool:
    """Elimina una tarea por ID. Devuelve True si eliminó, False si no existía."""
    conn = get_connection()
    try:
        cursor = conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
