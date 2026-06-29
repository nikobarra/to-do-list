"""tests
Suite de pruebas automatizadas (``pytest`` + ``TestClient`` de FastAPI).

Los tests usan una base de datos SQLite temporal única por test (ver
:func:`test_todos.client_with_db`), por lo que son completamente
aislados y pueden ejecutarse en cualquier orden.
"""
