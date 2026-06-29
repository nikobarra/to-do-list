"""routes.py
Definición de los endpoints REST para la gestión de tareas.

Todos los endpoints viven bajo el prefijo ``/api`` y la etiqueta
``todos`` para que la documentación automática de FastAPI
(``/docs`` y ``/redoc``) los agrupe correctamente.

Convenciones:
    * Validación de entrada y salida delegada en :mod:`app.models`.
    * Errores explícitos con ``HTTPException`` y mensajes específicos
      (nada de errores genéricos 500 sin contexto).
    * Los errores de validación de Pydantic se traducen automáticamente
      a respuestas ``422`` por FastAPI.
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
    """Lista tareas, opcionalmente filtradas por estado.

    Args:
        status: Filtro opcional (``'pending'`` o ``'done'``). Si es
            ``None`` se devuelven todas las tareas.

    Returns:
        list[TodoResponse]: Lista de tareas ordenadas por ``id``
        descendente. Lista vacía si no hay coincidencias.

    Raises:
        HTTPException: 400 si el valor de ``status`` no es válido a
            pesar de la validación de FastAPI (defensa en profundidad).
    """
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
    """Devuelve el detalle de una tarea existente.

    Args:
        todo_id: Identificador numérico de la tarea.

    Returns:
        TodoResponse: La tarea solicitada.

    Raises:
        HTTPException: 404 si no existe ninguna tarea con ese ``id``.
    """
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
    """Crea una tarea nueva en estado ``pending``.

    Args:
        payload: Cuerpo validado por Pydantic con ``title`` obligatorio
            y ``description`` opcional.

    Returns:
        TodoResponse: La tarea recién creada, con su ``id`` y
        ``created_at`` asignados por el servidor.
    """
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
    """Actualiza parcialmente una tarea existente (semántica ``PATCH``).

    Args:
        todo_id: Identificador de la tarea a actualizar.
        payload: Cuerpo validado por Pydantic; cada campo es opcional,
            por lo que sólo se aplican los campos presentes.

    Returns:
        TodoResponse: La tarea ya actualizada.

    Raises:
        HTTPException: 404 si no existe ninguna tarea con ese ``id``.
    """
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
    """Elimina una tarea existente.

    Args:
        todo_id: Identificador de la tarea a eliminar.

    Returns:
        dict: Mensaje confirmando la eliminación, con el ``id`` afectado.

    Raises:
        HTTPException: 404 si no existe ninguna tarea con ese ``id``.
    """
    deleted = db.delete_todo(todo_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró ninguna tarea con id={todo_id} para eliminar",
        )
    return {"detail": f"Tarea con id={todo_id} eliminada correctamente"}
