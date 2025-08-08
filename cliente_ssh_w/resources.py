import os

def resource_path(rel):
    """Devuelve la ruta absoluta de un recurso a partir de una ruta relativa al archivo actual."""
    return os.path.join(os.path.dirname(__file__), rel)


def load_qss(file):
    """Carga y retorna el contenido de un archivo QSS de estilos."""
    try:
        with open(resource_path(file), "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error cargando QSS '{file}': {e}")
        return ""
