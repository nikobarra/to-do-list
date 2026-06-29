"""conftest.py
Asegura que `app` sea importable al ejecutar pytest desde `backend`.
"""
import os
import sys

# Añade el directorio backend al sys.path para que `import app...` funcione
sys.path.insert(0, os.path.dirname(__file__))
