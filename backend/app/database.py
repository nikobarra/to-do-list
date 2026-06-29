"""database.py
Capa de persistencia de la aplicación.

Encapsula la conexión a SQLite, la creación del esquema y las operaciones
CRUD utilizadas por los endpoints REST definidos en :mod:`app.routes`.

El módulo está diseñado para ser trivialmente sustituible en tests:
basta con reasignar ``DB_PATH`` a un archivo temporal antes de importar
la aplicación (ver ``conftest.py`` y ``tests/test_todos.py``).
"""
import sqlite3
import os
from typing import List, Optional, Dict, Any


# Ruta de la base de datos. Se almacena en una variable para permitir
# su reemplazo en tests (por ejemplo, una DB en memoria o un archivo temporal).
DB_PATH = os.path.join(os.path.dirname(__file__), "todos.db")


def get_connection() -> sqlite3.Connection:
    """Abre y devuelve una nueva conexión SQLite.

    La conexión se configura con ``row_factory = sqlite3.Row`` para que
    las filas puedan indexarse tanto por posición como por nombre de
    columna, y activa las claves foráneas (``PRAGMA foreign_keys = ON``)
    como buena práctica de cara a futuras relaciones entre tablas.

    Returns:
        sqlite3.Connection: Conexión abierta. El llamador es responsable
        de cerrarla (típicamente con un bloque ``try/finally``).
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Activar claves foráneas (no se usan aún, pero es buena práctica)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Crea la tabla ``todos`` si aún no existe.

    El esquema es:

    - ``id``: entero autoincremental, clave primaria.
    - ``title``: texto obligatorio (1-200 caracteres, validado en Pydantic).
    - ``description``: texto opcional, por defecto cadena vacía.
    - ``status``: ``'pending'`` o ``'done'`` (validado en Pydantic).
    - ``created_at``: timestamp ISO rellenado por SQLite.

    Idempotente: se puede llamar múltiples veces sin efectos adversos.
    """
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
    """Convierte una fila ``sqlite3.Row`` en un diccionario plano.

    Args:
        row: Fila devuelta por una consulta SQLite.

    Returns:
        Dict[str, Any]: Mapeo ``nombre_columna -> valor`` listo para
        serializar o para construir un modelo Pydantic.
    """
    return {key: row[key] for key in row.keys()}


def get_all_todos(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lista todas las tareas, opcionalmente filtradas por estado.

    Args:
        status: Si se proporciona (``'pending'`` o ``'done'``), devuelve
            únicamente las tareas con ese estado. Si es ``None``,
            devuelve todas.

    Returns:
        List[Dict[str, Any]]: Tareas ordenadas por ``id`` descendente
        (la más reciente primero). Lista vacía si no hay coincidencias.
    """
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
    """Obtiene una tarea por su identificador.

    Args:
        todo_id: Identificador numérico de la tarea.

    Returns:
        Optional[Dict[str, Any]]: La tarea como diccionario, o ``None``
        si no existe ninguna tarea con ese ``id``.
    """
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
        row = cursor.fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def create_todo(title: str, description: str = "") -> Dict[str, Any]:
    """Inserta una nueva tarea en estado ``pending`` y la devuelve.

    Args:
        title: Título de la tarea (ya validado por Pydantic).
        description: Descripción opcional. Por defecto cadena vacía.

    Returns:
        Dict[str, Any]: La tarea recién creada, incluyendo su ``id``
        y ``created_at`` asignados por SQLite.
    """
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
    """Actualiza parcialmente una tarea existente.

    Cualquier argumento ``None`` deja el campo correspondiente sin tocar,
    lo que hace esta función adecuada para soportar ``PATCH`` parcial.

    Args:
        todo_id: Identificador de la tarea a actualizar.
        title: Nuevo título (opcional).
        description: Nueva descripción (opcional).
        status: Nuevo estado, ``'pending'`` o ``'done'`` (opcional).

    Returns:
        Optional[Dict[str, Any]]: La tarea ya actualizada, o ``None`` si
        no existía ninguna tarea con ese ``id``.
    """
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
    """Elimina una tarea por su identificador.

    Args:
        todo_id: Identificador de la tarea a eliminar.

    Returns:
        bool: ``True`` si se eliminó una fila, ``False`` si no existía
        ninguna tarea con ese ``id`` (idempotencia para el llamador).
    """
    conn = get_connection()
    try:
        cursor = conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
