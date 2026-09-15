import sys
import os

def get_resource_path(relative_path):
    """
    Obtiene la ruta absoluta a un recurso, funcionando tanto en desarrollo como empaquetado.
    """
    if getattr(sys, 'frozen', False):
        # Empaquetado con PyInstaller
        base_path = sys._MEIPASS
    else:
        # Modo desarrollo
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    return os.path.join(base_path, relative_path)

def get_backend_root():
    """
    Obtiene la raíz del backend (donde están los archivos de datos, modelos, etc.)
    """
    if getattr(sys, 'frozen', False):
        # En modo empaquetado, los recursos están en _internal/
        return os.path.dirname(os.path.abspath(sys.executable))
    else:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))