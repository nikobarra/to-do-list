# To-Do List (FastAPI + SQLite + Streamlit)

Aplicación completa de gestión de tareas dividida en **backend** (API REST con FastAPI + SQLite) y **frontend** (panel web con Streamlit).

## 📁 Estructura del proyecto

```
proyecto_1/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── database.py        # Conexión y CRUD con sqlite3
│   │   ├── models.py          # Validación con Pydantic
│   │   ├── routes.py          # 5 endpoints REST
│   │   └── main.py            # Aplicación FastAPI
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_todos.py      # 15 tests con pytest + TestClient
│   ├── conftest.py
│   ├── pytest.ini
│   └── requirements.txt
├── frontend/
│   └── app.py                  # Interfaz Streamlit
└── README.md
```

## 🔧 Backend (API REST)

### Endpoints

| Método | Ruta                       | Descripción                                  |
|--------|----------------------------|----------------------------------------------|
| GET    | `/api/todos`               | Listar tareas (`?status=pending` o `done`)   |
| GET    | `/api/todos/{id}`          | Detalle de una tarea (404 si no existe)      |
| POST   | `/api/todos`               | Crear tarea (`title` obligatorio)            |
| PATCH  | `/api/todos/{id}`          | Actualizar parcialmente                      |
| DELETE | `/api/todos/{id}`          | Eliminar (404 si no existe)                  |
| GET    | `/`                        | Health check                                 |

### Características técnicas
- ✅ **Pydantic** para validación (longitudes mínimas/máximas, `Literal` para `status`).
- ✅ **HTTPException** con mensajes claros y específicos (nada genérico).
- ✅ **404 explícito** cuando la tarea no existe (`"No se encontró ninguna tarea con id={id}..."`).
- ✅ **422** automático de Pydantic para datos inválidos.
- ✅ Tests con **pytest** + **TestClient** (httpx): **15 tests pasando**.

### Arrancar el backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Documentación interactiva: <http://127.0.0.1:8000/docs>

### Ejecutar tests

```bash
cd backend
pytest tests/ -v
```

Resultado: **15 passed**.

## 🎨 Frontend (Streamlit)

### Características
- 📋 **Tabla de tareas** con indicador visual:
  - 🟡 Tarjeta amarilla para pendientes.
  - 🟢 Tarjeta verde para completadas.
- ➕ **Formulario** para crear tareas (título obligatorio + descripción opcional).
- ✔️ **Botón "Completar"** solo visible/activo en tareas pendientes (deshabilitado en completadas).
- 🗑️ **Botón "Eliminar"** por cada tarea.
- 📊 **Resumen** con métricas: Total · Pendientes · Completadas.
- 🎛️ Filtro lateral: Todas / Pendientes / Completadas.

### Arrancar el frontend

> ⚠️ **Importante**: arranca primero la API y después Streamlit.

```bash
# Terminal 1: backend
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 2: frontend
streamlit run frontend/app.py
```

Streamlit se abrirá en <http://localhost:8501>.

## 🔄 Flujo completo

1. Levantar la API (`uvicorn`).
2. Levantar Streamlit (`streamlit run frontend/app.py`).
3. El panel usa `requests` para consumir los endpoints de la API.
4. Las mutaciones (crear/completar/eliminar) invalidan la cache y refrescan la vista automáticamente.

## 📊 Resumen de pruebas

```
tests/test_todos.py::test_list_todos_empty                         PASSED
tests/test_todos.py::test_list_todos_filter_by_status              PASSED
tests/test_todos.py::test_get_todo_by_id_ok                        PASSED
tests/test_todos.py::test_get_todo_by_id_404                       PASSED
tests/test_todos.py::test_create_todo_with_description             PASSED
tests/test_todos.py::test_create_todo_without_description          PASSED
tests/test_todos.py::test_create_todo_missing_title_422            PASSED
tests/test_todos.py::test_create_todo_empty_title_422              PASSED
tests/test_todos.py::test_patch_todo_update_status                 PASSED
tests/test_todos.py::test_patch_todo_update_title_description      PASSED
tests/test_todos.py::test_patch_todo_404                           PASSED
tests/test_todos.py::test_patch_todo_invalid_status_422            PASSED
tests/test_todos.py::test_delete_todo_ok                           PASSED
tests/test_todos.py::test_delete_todo_404                          PASSED
tests/test_todos.py::test_health_root                              PASSED

15 passed in ~2s
```