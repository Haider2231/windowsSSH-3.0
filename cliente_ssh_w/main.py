import os
import sys
from dotenv import load_dotenv
# Eliminado load_dotenv() global para usar ruta absoluta dentro de main
from PyQt6 import QtWidgets
from PyQt6.QtWebEngineCore import QWebEngineUrlScheme
from gui.vista import Vista
from controller import Controlador
from resources import resource_path, load_qss
from copilot.openai_service import OpenAIService
from copilot.markdown_service import MarkdownService
from copilot.copilot_controller import CopilotController

import sys
# Add UglyWidgets to sys.path
uglywidgets_path = resource_path("UglyWidgets")
if uglywidgets_path not in sys.path:
    sys.path.insert(0, uglywidgets_path)
library_path = resource_path("UglyWidgets/Library")
if library_path not in sys.path:
    sys.path.insert(0, library_path)



def main():
    # Crear la aplicación antes de instanciar cualquier QWidget
    app = QtWidgets.QApplication(sys.argv)
    # Cargar variables de entorno desde .env dentro del bundle (compatible con PyInstaller)
    # Intentar varias ubicaciones posibles según --add-data
    env_candidates = ['.env', 'cliente_ssh_w/.env']
    loaded_from = None
    for cand in env_candidates:
        try:
            path = resource_path(cand)
            if os.path.exists(path):
                load_dotenv(path)
                loaded_from = path
        except Exception:
            pass
    # Registrar esquema 'ssh' personalizado
    if QWebEngineUrlScheme.schemeByName(b"ssh").name().isEmpty():
        ssh_scheme = QWebEngineUrlScheme(b"ssh")
        QWebEngineUrlScheme.registerScheme(ssh_scheme)

    # Leer configuración de entorno
    default_host = os.environ.get("DEFAULT_HOST", "")
    default_port = int(os.environ.get("DEFAULT_PORT", "22"))
    usuario = os.environ.get("DEFAULT_USER", "")
    clave = os.environ.get("DEFAULT_PASS", "")

    # Inicializar servicios de OpenAI y Markdown
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        hint = loaded_from if loaded_from else "(no se encontró .env empaquetado)"
        QtWidgets.QMessageBox.critical(None, "Error crítico", f"No se encontró la clave OPENAI_API_KEY. Verifica .env en: {hint}")
        sys.exit(1)
    openai_service = OpenAIService(api_key)
    markdown_service = MarkdownService()

    # Inicializar controlador SSH y Copilot
    controlador = Controlador(default_host, default_port, usuario, clave)
    copilot_controller = CopilotController(openai_service, markdown_service, ssh_service=None)

    # Aplicar hoja de estilos
    app.setStyleSheet(load_qss("styles/main.qss"))

    # Crear y mostrar la ventana principal
    vista = Vista(controlador, default_host, default_port, usuario, clave, copilot_controller)
    vista.show()

    # Ejecutar loop de la aplicación y capturar errores
    try:
        sys.exit(app.exec())
    except Exception as e:
        QtWidgets.QMessageBox.critical(None, "Error crítico", f"Error en main: {e}")

if __name__ == "__main__":
    main()
