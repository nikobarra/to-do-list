"""models.py
Modelos de validación de datos con Pydantic para la API.
Define los esquemas de entrada y salida para los endpoints.
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class TodoBase(BaseModel):
    """Esquema base con los campos comunes de una tarea."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Título de la tarea (obligatorio, 1-200 caracteres)",
        examples=["Comprar leche"],
    )
    description: str = Field(
        default="",
        max_length=1000,
        description="Descripción opcional de la tarea (0-1000 caracteres)",
        examples=["Leche semidesnatada del Mercadona"],
    )


class TodoCreate(TodoBase):
    """Esquema para crear una tarea. Solo título y descripción."""
    pass


class TodoUpdate(BaseModel):
    """Esquema para actualizar una tarea. Todos los campos son opcionales
    porque PATCH permite actualizaciones parciales."""

    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Nuevo título (1-200 caracteres)",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Nueva descripción (0-1000 caracteres)",
    )
    status: Optional[Literal["pending", "done"]] = Field(
        default=None,
        description="Nuevo estado: 'pending' o 'done'",
    )


class TodoResponse(TodoBase):
    """Esquema de respuesta con todos los campos de la tarea."""

    id: int = Field(..., description="Identificador único de la tarea")
    status: Literal["pending", "done"] = Field(
        default="pending",
        description="Estado actual de la tarea",
    )
    created_at: str = Field(
        ...,
        description="Fecha de creación en formato ISO",
    )

    model_config = ConfigDict(from_attributes=True)


def todo_from_row(row: dict) -> TodoResponse:
    """Convierte una fila de la base de datos a un TodoResponse."""
    created_at = row["created_at"]
    if isinstance(created_at, datetime):
        created_at = created_at.isoformat()
    return TodoResponse(
        id=row["id"],
        title=row["title"],
        description=row["description"] or "",
        status=row["status"],
        created_at=created_at,
    )
