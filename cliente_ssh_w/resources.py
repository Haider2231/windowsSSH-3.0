import os
import sys

def resource_path(rel):
    """Devuelve la ruta absoluta de un recurso, compatible con PyInstaller (onefile/onedir).

    - En desarrollo usa la carpeta del archivo actual.
    - En ejecutable onefile usa la carpeta temporal sys._MEIPASS donde PyInstaller extrae los datos.
    """
    base = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
    return os.path.join(base, rel)


def load_qss(file):
    """Carga y retorna el contenido de un archivo QSS de estilos."""
    try:
        with open(resource_path(file), "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error cargando QSS '{file}': {e}")
        return ""
