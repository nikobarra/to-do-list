"""conftest.py
Configuración de pytest para el paquete ``backend``.

Pytest descubre los tests desde ``backend/tests`` y necesita que
``app`` sea importable como paquete de Python. Este archivo añade
el directorio ``backend`` a ``sys.path`` para que ``import app...``
funcione tanto al ejecutar ``pytest`` desde ``backend/`` como desde
la raíz del repositorio.
"""
import os
import sys

# Añade el directorio backend al sys.path para que `import app...` funcione
sys.path.insert(0, os.path.dirname(__file__))
