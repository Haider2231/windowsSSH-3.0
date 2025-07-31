import os
import sys

# Agrega el directorio UglyWidgets al sys.path para importar widgets personalizados
uglywidgets_path = os.path.join(os.path.dirname(__file__), "UglyWidgets")
if uglywidgets_path not in sys.path:
    sys.path.insert(0, uglywidgets_path)

from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel,
    QMessageBox, QSizePolicy, QFrame, QGroupBox, QFormLayout
)
from UglyWidgets.qtssh_widget import Ui_Terminal  # Widget de terminal embebida
from agente_copilot import CopilotAgentWidget  # Widget del agente copiloto

class Vista(QMainWindow):
    """
    Clase principal de la GUI para el cliente SSH Upiloto.
    Gestiona el formulario de conexión, la terminal embebida y el asistente Copilot.
    """

    def __init__(self, controlador, default_host, default_port, default_usuario, default_clave):
        """
        Constructor de la clase Vista.
        Configura la ventana inicial, carga estilos, crea formulario y guarda referencias iniciales.
        """
        super().__init__()
        self.setWindowTitle("Cliente SSH Upiloto")
        self.resize(500, 350)

        self.controlador = controlador
        self.default_host = default_host
        self.default_port = default_port
        self.default_usuario = default_usuario
        self.default_clave = default_clave

        # Contenedor central y layout principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        central_widget.setLayout(self.main_layout)

        self._crear_header()
        self._crear_formulario_conexion()
        self._load_styles()

        # Cargar último usuario utilizado (si existe)
        settings = QtCore.QSettings("Upiloto", "SSHClient")
        last_user = settings.value("user", "")
        self.user_entry.setText(last_user)

        # Inicialización de atributos
        self.terminal_panel = None
        self.terminal_container = None
        self.ssh_terminal_widget = None
        self.ssh_backend = None
        self.copilot_widget = None

    def _load_styles(self):
        """Carga y aplica los estilos definidos en styles/main.qss."""
        def get_resource_path(relative_path):
            return os.path.join(os.path.dirname(__file__), relative_path)

        qss_path = get_resource_path("styles/main.qss")
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f"Error al cargar estilos: {e}")

    def _crear_header(self):
        """Crea el encabezado de la ventana con botones de configuración y copiloto."""
        header_layout = QHBoxLayout()
        header_label = QLabel("🔌 Cliente SSH")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        self.settings_button = QPushButton("⚙")
        self.settings_button.setFixedSize(32, 32)
        self.settings_button.clicked.connect(self.on_settings_clicked)
        header_layout.addWidget(self.settings_button)

        self.copilot_button = QPushButton("🤖 Copilot")
        self.copilot_button.setFixedSize(100, 32)
        self.copilot_button.clicked.connect(self.on_copilot_clicked)
        header_layout.addWidget(self.copilot_button)

        self.main_layout.addLayout(header_layout)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        self.main_layout.addWidget(line)

    def _crear_formulario_conexion(self):
        """Crea el formulario de conexión SSH con campos y botón de conexión."""
        self.form_widget = QGroupBox("Datos de conexión")
        form_layout = QFormLayout()
        self.form_widget.setLayout(form_layout)
        self.main_layout.addWidget(self.form_widget)

        self.host_entry = QLineEdit()
        self.host_entry.setPlaceholderText("Host")
        self.host_entry.setVisible(False)
        form_layout.addRow("Host:", self.host_entry)

        self.port_entry = QLineEdit()
        self.port_entry.setPlaceholderText("Puerto")
        self.port_entry.setVisible(False)
        form_layout.addRow("Puerto:", self.port_entry)

        self.user_entry = QLineEdit()
        self.user_entry.setPlaceholderText("Usuario")
        form_layout.addRow("Usuario:", self.user_entry)

        self.password_entry = QLineEdit()
        self.password_entry.setPlaceholderText("Clave")
        self.password_entry.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Clave:", self.password_entry)

        self.connect_button = QPushButton("🌐 Conectar")
        self.connect_button.clicked.connect(self.on_connect_clicked)
        form_layout.addRow(self.connect_button)

    def on_connect_clicked(self):
        """
        Intenta conectar con el servidor SSH utilizando los datos ingresados.
        Si es exitoso, reemplaza el formulario por la terminal y habilita copiloto.
        """
        host_val = self.host_entry.text() or self.default_host
        user_val = self.user_entry.text() or self.default_usuario
        password_val = self.password_entry.text() or self.default_clave

        try:
            port_val_str = self.port_entry.text() or str(self.default_port)
            port_val = int(port_val_str)
        except ValueError:
            self.show_error("El puerto debe ser un número válido.")
            return

        if not host_val or not user_val or not password_val:
            self.show_error("Host, usuario y clave son obligatorios.")
            return

        ssh_params = {
            "host": host_val,
            "port": port_val,
            "username": user_val,
            "password": password_val
        }

        if self.terminal_panel:
            self.terminal_panel.deleteLater()
            self.terminal_panel = None

        try:
            # Crear panel y terminal embebida
            self.terminal_panel = QWidget()
            terminal_layout = QHBoxLayout()
            terminal_layout.setContentsMargins(0, 20, 0, 0)
            self.terminal_panel.setLayout(terminal_layout)

            self.terminal_container = QWidget()
            terminal_container_layout = QVBoxLayout()
            terminal_container_layout.setContentsMargins(0, 0, 0, 0)
            self.terminal_container.setLayout(terminal_container_layout)
            self.terminal_container.setFixedWidth(780)

            self.ssh_terminal_widget = Ui_Terminal(connect_info=ssh_params, parent=self.terminal_container)
            terminal_container_layout.addWidget(self.ssh_terminal_widget)

            self.ssh_backend = getattr(self.ssh_terminal_widget, 'backend', None)

            terminal_layout.addWidget(self.terminal_container)
            self.main_layout.addWidget(self.terminal_panel)
            self.resize(1200, 700)
            self.centrar_ventana()

            self.form_widget.setVisible(False)
            self.settings_button.setVisible(False)

        except Exception as e:
            self.show_error("No se pudo conectar: credenciales incorrectas o error de conexión.\n" + str(e))
            if self.terminal_panel:
                self.terminal_panel.deleteLater()
            self.terminal_panel = None
            self.terminal_container = None
            self.ssh_terminal_widget = None
            self.ssh_backend = None

    @QtCore.pyqtSlot(str)
    def show_error(self, message):
        """Muestra un cuadro de diálogo con un mensaje de error."""
        QMessageBox.critical(self, "Error", message)

    def on_settings_clicked(self):
        """Alterna la visibilidad de los campos host y puerto en el formulario."""
        visible = self.host_entry.isVisible()
        self.host_entry.setVisible(not visible)
        self.port_entry.setVisible(not visible)

    def on_copilot_clicked(self):
        """Muestra u oculta el widget Copilot si ya hay una sesión activa."""
        if not self.terminal_panel:
            self.show_error("Conéctate primero para activar el copiloto.")
            return

        if self.copilot_widget:
            self.copilot_widget.deleteLater()
            self.copilot_widget = None
            return

        self.copilot_widget = CopilotAgentWidget(ssh_backend=self.ssh_backend)
        self.copilot_widget.setFixedWidth(400)
        self.terminal_panel.layout().addWidget(self.copilot_widget)

    def closeEvent(self, event):
        """Cierra la conexión SSH al cerrar la ventana, si aplica."""
        try:
            self.controlador.desconectar()
        except Exception as e:
            print(f"Error al desconectar: {e}")
        event.accept()

    def centrar_ventana(self):
        """Centra la ventana en la pantalla actual."""
        frame_geo = self.frameGeometry()
        screen_center = QtWidgets.QApplication.primaryScreen().availableGeometry().center()
        frame_geo.moveCenter(screen_center)
        self.move(frame_geo.topLeft())
