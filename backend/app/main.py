"""main.py
Punto de entrada de la aplicación FastAPI.

Responsabilidades:
    1. Inicializar el esquema de la base de datos al importar el módulo
       (esto también ocurre al ejecutar los tests).
    2. Crear la instancia de ``FastAPI`` con metadatos (título,
       descripción y versión) que se muestran en ``/docs`` y ``/redoc``.
    3. Registrar el ``APIRouter`` definido en :mod:`app.routes`.
    4. Exponer un endpoint raíz ``GET /`` como health check.

Uso:
    $ uvicorn app.main:app --host 127.0.0.1 --port 8000

    También se puede ejecutar directamente con ``python -m app.main``.
"""
from fastapi import FastAPI

from .database import init_db
from .routes import router as todos_router


# Inicializar la DB al cargar el módulo (se ejecuta también en los tests)
init_db()

app = FastAPI(
    title="To-Do List API",
    description="API REST para gestión de tareas con FastAPI + SQLite",
    version="1.0.0",
)


@app.get("/", tags=["health"], summary="Health check")
def root():
    """Health check de la API.

    Pensado para sondeos de disponibilidad (load balancers, monitorización).
    No toca la base de datos, así que es seguro invocarlo con alta frecuencia.

    Returns:
        dict: ``{"status": "ok", "service": "todo-api"}``.
    """
    return {"status": "ok", "service": "todo-api"}


app.include_router(todos_router)


if __name__ == "__main__":
    # Permite ejecutar con `python -m app.main`
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
