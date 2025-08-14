import sys
import time
import os
import json

from PyQt6.QtCore import QSize, QCoreApplication, QUrl, QMetaObject, QTimer
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtWebChannel import QWebChannel
from .Library.sshschemahandler import WebEngineUrlSchemeHandler
from .Library.sshshell import Backend

class Ui_Terminal(QWidget):
    """
    Terminal class extending QWidget to enable SSH connections in a Qt widget.
    """

    def __init__(self, connect_info, parent=None):
        """
        Initialization function for the Terminal class.

        :param connect_info: a dictionary that includes SSH credentials.
        :param parent: parent widget if any.
        """
        super().__init__(parent)
        self.host = connect_info.get('host')
        self.port = connect_info.get('port')  # Get port from connect_info
        self.username = connect_info.get('username')
        self.password = connect_info.get('password')
        self.div_height = 0
        self.initial_buffer = ""
        self._frontend_ready = False
        self._pending_outputs = []  # cola para datos antes de que JS defina handle_output

        self.setupUi(self)

    def setupUi(self, term):
        """
        Setups UI for the terminal widget.

        :param term: terminal widget instance.
        """
        term.setObjectName("term")
        QMetaObject.connectSlotsByName(term)
        layout = QVBoxLayout()
        self.handler = WebEngineUrlSchemeHandler()
        QWebEngineProfile.defaultProfile().installUrlSchemeHandler(b"ssh", self.handler)
        self.channel = QWebChannel()
        # Pass the port to the Backend constructor
        self.backend = Backend(host=self.host, port=self.port, username=self.username, password=self.password, parrent_widget=self)
        self.channel.registerObject("backend", self.backend)

        self.view = QWebEngineView()
        self.view.page().setWebChannel(self.channel)
        self.div_height = 0
        self.webview_size = self.view.size()

        self.view.resizeEvent = self.handle_resize_event
        self.view.loadFinished.connect(self.handle_load_finished)
        # Conectar salida del backend con protección hasta que JS esté listo
        self.backend.send_output.connect(self._on_backend_output)

        html_path = os.path.join(os.path.dirname(__file__), "qtsshcon.html")
        self.view.load(QUrl.fromLocalFile(os.path.abspath(html_path)))
        layout.addWidget(self.view)
        term.setLayout(layout)
        self.retranslateUi(term)

    def update_div_height(self):
        """
        Updates the div height of the terminal.
        """
        script = (
            "(function(){var el=document.getElementById('terminal');"
            f"if(el){{el.style.height='{self.div_height}px';}}"
            "})()"
        )
        self.view.page().runJavaScript(script)

    def handle_load_finished(self):
        """
        Handles actions after the web page load has finished.
        """
        self.div_height = self.view.size().height() - 30
        self.update_div_height()
        current_size = self.view.size()
        new_size = QSize(current_size.width(), current_size.height() + 1)
        self.view.resize(new_size)
        print("loaded..")

        # Comprobar si el entorno JS está listo (window.backend y handle_output)
        def mark_ready(ok):
            # ok es True si ambas funciones existen en JS
            self._frontend_ready = bool(ok)
            if self._frontend_ready:
                # volcar cualquier salida pendiente
                for data in self._pending_outputs:
                    try:
                        self.view.page().runJavaScript(f"window.handle_output({json.dumps(data)})")
                    except Exception as e:
                        print(f"Error flushing pending output: {e}")
                self._pending_outputs.clear()
            QTimer.singleShot(0, self.delayed_method)

        # Evaluar JS para verificar existencia de objetos/fns
        check_js = "typeof window !== 'undefined' && typeof window.handle_output === 'function' && typeof window.backend !== 'undefined'"
        self.view.page().runJavaScript(check_js, mark_ready)

    def handle_resize_event(self, event):
        """
        Handles resize events of the terminal.

        :param event: event object containing event details.
        """
        self.div_height = self.view.size().height() - 30
        if self.view.size() != self.webview_size:
            self.webview_size = self.view.size()
            self.update_div_height()

    def retranslateUi(self, term):
        """
        Retranslates the UI based on the current locale.

        :param term: terminal widget instance.
        """
        _translate = QCoreApplication.translate
        term.setWindowTitle(_translate("term", "term"))

    def delayed_method(self):
        """
        This method will be called after the web page load has finished.
        """
        print(f"Buffer: {json.dumps(self.initial_buffer)}")
        banner = json.dumps(self.initial_buffer).replace('"', '')
        # Escribir banner solo si 'term' existe en JS
        self.view.page().runJavaScript(
            "typeof term !== 'undefined'",
            lambda ok: self.view.page().runJavaScript(f"term.write('{banner}');") if ok else None,
        )

    def _on_backend_output(self, data: str):
        """Envía datos al frontend si está listo; si no, los acumula."""
        try:
            if self._frontend_ready:
                self.view.page().runJavaScript(f"window.handle_output({json.dumps(data)})")
            else:
                self._pending_outputs.append(data)
        except Exception as e:
            print(f"Error sending output to frontend: {e}")


if __name__ == "__main__":
    """
    Main function. Initializes and runs the application.
    """
    try:
        app = QApplication(sys.argv)
        mainWin = QMainWindow()
        mainWin.resize(800, 400)
        terminal = Ui_Terminal({"host":"10.0.0.12", "username": "rtruser", "password": "mypw"}, mainWin)
        mainWin.setCentralWidget(terminal)
        mainWin.setWindowTitle("PyQt6 - SSH Widget")
        mainWin.show()
        sys.exit(app.exec())

    except Exception as e:
        print(f"Exception in main: {e}")
