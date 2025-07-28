import os
import sys

# Add UglyWidgets to sys.path
# Assuming UglyWidgets is a sibling directory to the one containing gui.py
# Adjust the path if UglyWidgets is located elsewhere relative to gui.py
uglywidgets_path = os.path.join(os.path.dirname(__file__), "UglyWidgets")
if uglywidgets_path not in sys.path:
    sys.path.insert(0, uglywidgets_path)

from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel,
    QMessageBox, QSizePolicy, QFrame, QGroupBox, QFormLayout
)
from qtssh_widget import Ui_Terminal  # Usar el widget correcto
from agente_copilot import CopilotAgentWidget

class Vista(QMainWindow):
    def __init__(self, controlador, default_host, default_port, default_usuario, default_clave):
        super().__init__()
        self.setWindowTitle("Cliente SSH Upiloto")
        self.resize(800, 600)
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI';
                font-size: 14px;
            }
            QPushButton {
                background-color: #0078d7;
                color: white;
                padding: 6px 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #005fa1;
            }
            QLineEdit {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QLabel {
                font-weight: bold;
            }
        """)

        self.controlador = controlador
        self.default_host = default_host
        self.default_port = default_port
        self.default_usuario = default_usuario
        self.default_clave = default_clave

        # Widget central y layout principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(60, 40, 60, 40)
        central_widget.setLayout(self.main_layout)

        self._crear_header()
        self._crear_formulario_conexion()
        self._crear_terminal_area()

    def _crear_header(self):
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

    def _crear_terminal_area(self):
        # Crear un splitter horizontal para terminal y Copilot
        self.terminal_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.terminal_container_widget = QWidget()
        self.terminal_layout = QVBoxLayout()
        self.terminal_container_widget.setLayout(self.terminal_layout)
        self.terminal_splitter.addWidget(self.terminal_container_widget)
        # Widget Copilot (inicialmente oculto)
        self.copilot_widget = None
        self.copilot_panel = QWidget()
        self.copilot_layout = QVBoxLayout(self.copilot_panel)
        self.copilot_panel.setMinimumWidth(350)
        self.copilot_panel.setVisible(False)
        self.terminal_splitter.addWidget(self.copilot_panel)
        self.main_layout.addWidget(self.terminal_splitter)
        self.terminal_container_widget.setVisible(False)
        self.ssh_terminal_widget = None
        self.ssh_backend = None  # Referencia al backend SSH

    def on_connect_clicked(self):
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

        self.form_widget.setVisible(False)
        self.settings_button.setVisible(False)

        if self.ssh_terminal_widget:
            self.ssh_terminal_widget.deleteLater()
            self.ssh_terminal_widget = None
            self.ssh_backend = None

        try:
            self.ssh_terminal_widget = Ui_Terminal(connect_info=ssh_params, parent=self.terminal_container_widget)
            self.terminal_layout.addWidget(self.ssh_terminal_widget)
            self.terminal_container_widget.setVisible(True)
            # Guardar referencia al backend SSH
            self.ssh_backend = getattr(self.ssh_terminal_widget, 'backend', None)
        except Exception as e:
            self.show_error("No se pudo conectar: credenciales incorrectas o error de conexión.\n" + str(e))
            self.form_widget.setVisible(True)
            self.settings_button.setVisible(True)
            self.terminal_container_widget.setVisible(False)
            if self.ssh_terminal_widget:
                self.ssh_terminal_widget.deleteLater()
                self.ssh_terminal_widget = None
            self.ssh_backend = None
        # El controlador original (self.controlador) ya no se usa para la conexión aquí,
        # ya que Ui_Terminal maneja su propia lógica de conexión SSH.

    @QtCore.pyqtSlot(str)
    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)

    def on_settings_clicked(self):
        visible = self.host_entry.isVisible()
        self.host_entry.setVisible(not visible)
        self.port_entry.setVisible(not visible)

    def on_copilot_clicked(self):
        # Alternar visibilidad del panel Copilot sin cambiar el tamaño de la terminal
        if self.copilot_widget is None:
            self.copilot_widget = CopilotAgentWidget(ssh_backend=self.ssh_backend)
            self.copilot_layout.addWidget(self.copilot_widget)
        is_visible = self.copilot_panel.isVisible()
        self.copilot_panel.setVisible(not is_visible)
        if not is_visible:
            # Agrandar la ventana principal para mostrar el chat sin reducir la terminal
            main_width = self.width()
            copilot_width = self.copilot_panel.minimumWidth() if self.copilot_panel.minimumWidth() > 0 else 350
            self.resize(main_width + copilot_width, self.height())
        else:
            # Si se oculta el chat, reducir la ventana
            main_width = self.width()
            copilot_width = self.copilot_panel.minimumWidth() if self.copilot_panel.minimumWidth() > 0 else 350
            self.resize(max(main_width - copilot_width, 800), self.height())

    def closeEvent(self, event):
        try:
            self.controlador.desconectar()
        except Exception as e:
            print(f"Error al desconectar: {e}")
        event.accept()