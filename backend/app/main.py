"""main.py
Aplicación principal FastAPI. Inicializa la base de datos y registra
las rutas del módulo de tareas.
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
    """Endpoint raíz de salud."""
    return {"status": "ok", "service": "todo-api"}


app.include_router(todos_router)


if __name__ == "__main__":
    # Permite ejecutar con `python -m app.main`
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
