

import os
import sys
from dotenv import load_dotenv
load_dotenv()
from PyQt6 import QtWidgets
from PyQt6.QtWebEngineCore import QWebEngineUrlScheme
from gui.vista import Vista
from controller import Controlador
from resources import resource_path, load_qss
from copilot.openai_service import OpenAIService
from copilot.markdown_service import MarkdownService
from copilot.copilot_controller import CopilotController

import sys
# Add UglyWidgets to sys.path (mover aquí desde vista.py)
uglywidgets_path = resource_path("UglyWidgets")
if uglywidgets_path not in sys.path:
    sys.path.insert(0, uglywidgets_path)
library_path = resource_path("UglyWidgets/Library")
if library_path not in sys.path:
    sys.path.insert(0, library_path)

# Register the custom 'ssh' scheme early
if QWebEngineUrlScheme.schemeByName(b"ssh").name().isEmpty():
    ssh_scheme = QWebEngineUrlScheme(b"ssh")
    QWebEngineUrlScheme.registerScheme(ssh_scheme)



def main():
    try:
        default_host = os.environ.get("DEFAULT_HOST", "")
        default_port = int(os.environ.get("DEFAULT_PORT", "22"))
        usuario = os.environ.get("DEFAULT_USER", "")
        clave = os.environ.get("DEFAULT_PASS", "")

        # Inicializa servicios
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            QtWidgets.QMessageBox.critical(None, "Error crítico", "No se encontró la clave OPENAI_API_KEY en el entorno.")
            sys.exit(1)
        openai_service = OpenAIService(api_key)
        markdown_service = MarkdownService()

        # Inicializa controlador SSH (si lo usas)
        controlador = Controlador(default_host, default_port, usuario, clave)

        # Pasa el servicio SSH al controlador Copilot
        copilot_controller = CopilotController(openai_service, markdown_service, ssh_service=controlador)

        app = QtWidgets.QApplication(sys.argv)
        app.setStyleSheet(load_qss("styles/main.qss"))

        # Pasa el controlador Copilot a la Vista
        vista = Vista(controlador, default_host, default_port, usuario, clave, copilot_controller)
        vista.show()
        sys.exit(app.exec())
    except Exception as e:
        QtWidgets.QMessageBox.critical(None, "Error crítico", f"Error en main: {e}")

if __name__ == "__main__":
    main()
