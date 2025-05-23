import os
import sys

# Add UglyWidgets to sys.path
uglywidgets_path = os.path.join(os.path.dirname(__file__), "UglyWidgets")
if uglywidgets_path not in sys.path:
    sys.path.insert(0, uglywidgets_path)

from PyQt6.QtWebEngineCore import QWebEngineUrlScheme # Import QWebEngineUrlScheme

# Register the custom 'ssh' scheme early
# It's important to do this before the QApplication is created or the scheme is used.
# Corrected condition: check if the scheme name is empty
if QWebEngineUrlScheme.schemeByName(b"ssh").name().isEmpty(): # Check if not already registered
    ssh_scheme = QWebEngineUrlScheme(b"ssh")
    # You can set properties for the scheme if needed, e.g.:
    # ssh_scheme.setSyntax(QWebEngineUrlScheme.Syntax.HostAndPort)
    # ssh_scheme.setDefaultPort(22) # Default port for this scheme if not specified in URL
    # ssh_scheme.setFlags(QWebEngineUrlScheme.Flag.SecureScheme | QWebEngineUrlScheme.Flag.CorsEnabled)
    QWebEngineUrlScheme.registerScheme(ssh_scheme)

# Busca la ruta de los DLLs de PyQt6-WebEngine automáticamente
def add_pyqt6_dll_dir():
    import site
    for path in site.getsitepackages() + [site.getusersitepackages()]:
        qt_bin = os.path.join(path, "PyQt6", "Qt6", "bin")
        if os.path.isdir(qt_bin):
            os.add_dll_directory(qt_bin)
            return
    # Si no se encuentra, muestra advertencia
    print("ADVERTENCIA: No se encontró la carpeta de DLLs de PyQt6-WebEngine.")

add_pyqt6_dll_dir()

from PyQt6 import QtWidgets # Mantenemos QtWidgets, QtCore podría no ser necesario aquí directamente
from gui import Vista
from controller import Controlador # Asumimos que el controlador aún se usa

def main():
    try:
        default_host = "200.115.181.211"
        default_port = 9000
        host = default_host
        puerto = default_port # Aseguramos que puerto esté definido
        usuario = "tu_usuario"  # Reemplaza con tu usuario real
        clave = "tu_clave"      # Reemplaza con tu clave real

        # El controlador podría necesitar ser ajustado o eliminado si el widget maneja todo.
        # Por ahora, lo pasamos como antes.
        controlador = Controlador(host, puerto, usuario, clave)
                                        
        app = QtWidgets.QApplication(sys.argv)
        # Pasamos las credenciales a Vista para que pueda inicializar el QtSSH_Widget
        vista = Vista(controlador, default_host, default_port, usuario, clave)
        vista.show()
        sys.exit(app.exec()) # app.exec() en PyQt6
    except Exception as e:
        print(f"Error en main: {e}") # Mejor seguimiento de errores

if __name__ == "__main__":
    main()
