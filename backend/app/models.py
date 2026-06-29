"""models.py
Esquemas de validación y serialización de la API, basados en Pydantic v2.

Se separan tres responsabilidades:

- :class:`TodoCreate`: cuerpo de entrada para ``POST /api/todos``.
- :class:`TodoUpdate`: cuerpo de entrada para ``PATCH /api/todos/{id}``.
- :class:`TodoResponse`: forma de las respuestas JSON.

Las validaciones de longitud y los valores permitidos para ``status``
se declaran aquí para que FastAPI genere automáticamente errores
``422 Unprocessable Entity`` con detalle por campo.
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class TodoBase(BaseModel):
    """Esquema base con los campos compartidos por creación y respuesta.

    Attributes:
        title: Título de la tarea. Obligatorio, entre 1 y 200 caracteres.
        description: Descripción opcional, hasta 1000 caracteres.
            Por defecto cadena vacía.
    """

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
    """Esquema de entrada para crear una tarea (``POST /api/todos``).

    Solo expone los campos editables por el cliente en el momento de
    creación (``title`` y ``description``); ``id``, ``status`` y
    ``created_at`` los asigna el servidor.
    """


class TodoUpdate(BaseModel):
    """Esquema de entrada para actualizar una tarea (``PATCH`` parcial).

    Todos los campos son opcionales para permitir actualizaciones
    parciales: se modifica únicamente lo que el cliente envíe.

    Attributes:
        title: Nuevo título (1-200 caracteres). Opcional.
        description: Nueva descripción (0-1000 caracteres). Opcional.
        status: Nuevo estado. Sólo se aceptan los literales
            ``"pending"`` y ``"done"``.
    """

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
    """Esquema de salida devuelto por todos los endpoints de la API.

    Attributes:
        id: Identificador único asignado por SQLite al insertar.
        status: Estado actual (``"pending"`` o ``"done"``).
        created_at: Fecha de creación en formato ISO 8601.
    """

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
    """Convierte una fila cruda de la base de datos en un :class:`TodoResponse`.

    Args:
        row: Diccionario con las claves ``id``, ``title``, ``description``,
            ``status`` y ``created_at`` tal y como las devuelve
            :mod:`app.database`.

    Returns:
        TodoResponse: Instancia validada y lista para serializar a JSON.

    Note:
        Si ``created_at`` llega como :class:`datetime.datetime` (cuando
        se consulta desde un cursor SQLite en ciertos modos), se
        convierte a su representación ISO 8601 para mantener la
        consistencia del contrato de la API, que siempre expone strings.
    """
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
