from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QObject
import threading
import paramiko

class OutputSignal(QObject):
    output = pyqtSignal(str)

class SSHTerminal(QWidget):
    def __init__(self, transport, usuario):
        super().__init__()
        self.transport = transport
        self.usuario = usuario
        self.channel = None
        self.output_signal = OutputSignal()
        self.output_signal.output.connect(self.append_output)
        self.init_ui()
        self.start_ssh()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        self.layout.addWidget(self.terminal_output)
        self.input_line = QLineEdit()
        self.input_line.returnPressed.connect(self.send_command)
        self.layout.addWidget(self.input_line)
        self.send_button = QPushButton("Enviar")
        self.send_button.clicked.connect(self.send_command)
        self.layout.addWidget(self.send_button)

    def start_ssh(self):
        if not self.transport:
            self.output_signal.output.emit("No hay transporte SSH disponible.")
            return
        try:
            self.channel = self.transport.open_session()
            self.channel.get_pty(term="xterm-256color", width=80, height=24)
            self.channel.invoke_shell()
            threading.Thread(target=self.read_from_channel, daemon=True).start()
        except Exception as e:
            self.output_signal.output.emit(f"Error al abrir canal SSH: {e}")

    def read_from_channel(self):
        try:
            while True:
                if self.channel.recv_ready():
                    data = self.channel.recv(1024).decode(errors='ignore')
                    self.output_signal.output.emit(data)
                if self.channel.exit_status_ready():
                    break
        except Exception as e:
            self.output_signal.output.emit(f"Error de lectura: {e}")

    def send_command(self):
        cmd = self.input_line.text()
        if self.channel and cmd:
            try:
                self.channel.send(cmd + '\n')
                self.input_line.clear()
            except Exception as e:
                self.output_signal.output.emit(f"Error al enviar comando: {e}")

    def append_output(self, text):
        self.terminal_output.append(text)