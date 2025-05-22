import sys
import time
import os
import json

from PyQt6.QtCore import QSize, QCoreApplication, QUrl, QMetaObject, QTimer, pyqtSignal, QObject
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtWebChannel import QWebChannel
from sshschemahandler import WebEngineUrlSchemeHandler
from sshshell import Backend

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
        self.username = connect_info.get('username')
        self.password = connect_info.get('password')
        self.port = connect_info.get('port', 9000)  # <--- Añade esto
        self.div_height = 0
        self.initial_buffer = ""  # Evita AttributeError

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
        # No intentes instalar un handler para el esquema 'file'
        # QWebEngineProfile.defaultProfile().installUrlSchemeHandler(b"file", self.handler)
        self.channel = QWebChannel()
        self.backend = Backend(
            host=self.host,
            username=self.username,
            password=self.password,
            parrent_widget=self,
            port=int(getattr(self, 'port', getattr(self, 'default_port', 22))) if hasattr(self, 'port') or hasattr(self, 'default_port') else 22
        )
        self.channel.registerObject("backend", self.backend)

        self.view = QWebEngineView()
        self.view.page().setWebChannel(self.channel)
        self.div_height = 0
        self.webview_size = self.view.size()

        self.view.resizeEvent = self.handle_resize_event
        self.view.loadFinished.connect(self.handle_load_finished)

        # ENVÍA LA SALIDA DIRECTAMENTE, SIN BUFFER NI TIMER
        self.backend.send_output.connect(
            lambda data: self.view.page().runJavaScript(f"window.handle_output({json.dumps(data)})")
        )

        self.view.load(QUrl.fromLocalFile(os.path.abspath("qtsshcon.html")))
        layout.addWidget(self.view)
        term.setLayout(layout)
        self.retranslateUi(term)

    def update_div_height(self):
        # Evita error JS si el elemento no existe
        script = (
            "if (document.getElementById('terminal')) {"
            f"document.getElementById('terminal').style.height = '{self.div_height}px';"
            "}"
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
        QTimer.singleShot(0, self.delayed_method)

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
        # Solo imprime el buffer si existe
        print(f"Buffer: {json.dumps(self.initial_buffer)}")
        banner = json.dumps(self.initial_buffer).replace('"', '')
        # Evita error JS si term no existe
        self.view.page().runJavaScript(
            "if (typeof term !== 'undefined' && term.write) { term.write('%s'); }" % banner
        )


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
