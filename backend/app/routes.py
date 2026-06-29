"""routes.py
Definición de los endpoints de la API REST para la gestión de tareas.
Cada endpoint maneja sus errores con HTTPException para no devolver
errores genéricos.
"""
from typing import Optional, Literal

from fastapi import APIRouter, HTTPException, Query, status

from . import database as db
from .models import TodoCreate, TodoResponse, TodoUpdate, todo_from_row


router = APIRouter(prefix="/api", tags=["todos"])


@router.get(
    "/todos",
    response_model=list[TodoResponse],
    summary="Listar tareas",
    description=(
        "Devuelve todas las tareas. Soporta filtro opcional por estado "
        "con el parámetro `status` (`pending` o `done`)."
    ),
)
def list_todos(status: Optional[Literal["pending", "done"]] = Query(None)):
    """Devuelve todas las tareas, opcionalmente filtradas por estado."""
    try:
        rows = db.get_all_todos(status=status)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Parámetro `status` inválido: {exc}",
        )
    return [todo_from_row(row) for row in rows]


@router.get(
    "/todos/{todo_id}",
    response_model=TodoResponse,
    summary="Detalle de una tarea",
    description="Devuelve una tarea concreta por su ID. 404 si no existe.",
)
def get_todo(todo_id: int):
    """Devuelve el detalle de una tarea por ID."""
    row = db.get_todo_by_id(todo_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró ninguna tarea con id={todo_id}",
        )
    return todo_from_row(row)


@router.post(
    "/todos",
    response_model=TodoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva tarea",
    description="Crea una tarea con título (obligatorio) y descripción (opcional).",
)
def create_todo(payload: TodoCreate):
    """Crea una nueva tarea."""
    row = db.create_todo(title=payload.title, description=payload.description or "")
    return todo_from_row(row)


@router.patch(
    "/todos/{todo_id}",
    response_model=TodoResponse,
    summary="Actualizar una tarea",
    description=(
        "Actualiza parcialmente una tarea: título, descripción y/o estado. "
        "404 si la tarea no existe."
    ),
)
def update_todo(todo_id: int, payload: TodoUpdate):
    """Actualiza una tarea existente con PATCH (parcial)."""
    existing = db.get_todo_by_id(todo_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró ninguna tarea con id={todo_id} para actualizar",
        )
    updated = db.update_todo(
        todo_id=todo_id,
        title=payload.title,
        description=payload.description,
        status=payload.status,
    )
    if updated is None:
        # Defensa en profundidad (no debería ocurrir, ya validamos arriba)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró ninguna tarea con id={todo_id} para actualizar",
        )
    return todo_from_row(updated)


@router.delete(
    "/todos/{todo_id}",
    status_code=status.HTTP_200_OK,
    summary="Eliminar una tarea",
    description="Elimina una tarea por su ID. 404 si no existe.",
)
def delete_todo(todo_id: int):
    """Elimina una tarea existente."""
    deleted = db.delete_todo(todo_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró ninguna tarea con id={todo_id} para eliminar",
        )
    return {"detail": f"Tarea con id={todo_id} eliminada correctamente"}
