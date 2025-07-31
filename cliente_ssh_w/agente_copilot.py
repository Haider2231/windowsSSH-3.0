import os
import openai
import html
import markdown
from dotenv import load_dotenv
from PyQt6.QtGui import QTextOption
from PyQt6 import QtWidgets, QtCore

def get_resource_path(relative_path):
    """
    Devuelve la ruta absoluta de un recurso a partir de una ruta relativa.
    """
    return os.path.join(os.path.dirname(__file__), relative_path)

class CopilotAgentWidget(QtWidgets.QWidget):
    """
    Widget principal para interactuar con un agente OpenAI en modo "Ask" o "Agent".
    Permite enviar preguntas o instrucciones y recibir respuestas o comandos automatizados.
    """

    def __init__(self, ssh_backend=None, parent=None):
        """
        Inicializa el widget con controles de UI, área de chat y configuración del agente.
        """
        super().__init__(parent)

        self.layout = QtWidgets.QVBoxLayout(self)

        # Configuración del modo del agente
        self.agent_mode = "ASK"
        self.mode_selector = QtWidgets.QComboBox()
        self.mode_selector.addItems(["Ask", "Agent"])
        self.mode_selector.setCurrentText("Ask")
        self.mode_selector.setFixedWidth(100)
        self.mode_selector.currentTextChanged.connect(self._on_mode_changed)

        # Botón para iniciar nuevo chat
        self.new_chat_button = QtWidgets.QPushButton("Nuevo chat")
        self.new_chat_button.setFixedWidth(100)
        self.new_chat_button.clicked.connect(self._reset_conversation)

        # Controles superiores
        self.top_controls = QtWidgets.QHBoxLayout()
        self.top_controls.addWidget(self.mode_selector)
        self.top_controls.addWidget(self.new_chat_button)
        self.top_controls.addStretch()
        self.layout.addLayout(self.top_controls)

        # Área de chat (solo lectura)
        self.chat_area = QtWidgets.QTextEdit()
        self.chat_area.document().setDefaultStyleSheet("""
        pre {
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        """)
        self.chat_area.setLineWrapMode(QtWidgets.QTextEdit.LineWrapMode.WidgetWidth)
        self.chat_area.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.chat_area.setReadOnly(True)
        self.chat_area.setAcceptRichText(True)
        self.chat_area.setMinimumHeight(320)
        self.chat_area.setMinimumWidth(220)
        self.layout.addWidget(self.chat_area)

        # Entrada del usuario
        self.input_layout = QtWidgets.QHBoxLayout()
        self.prompt_entry = QtWidgets.QLineEdit()
        self.prompt_entry.setPlaceholderText("Escribe tu pregunta o instrucción...")
        self.prompt_entry.returnPressed.connect(self.on_send)
        self.input_layout.addWidget(self.prompt_entry)
        self.send_button = QtWidgets.QPushButton("Enviar")
        self.send_button.clicked.connect(self.on_send)
        self.input_layout.addWidget(self.send_button)
        self.layout.addLayout(self.input_layout)

        # Inicialización de entorno y cliente OpenAI
        load_dotenv(get_resource_path('.env'))
        self.openai_client = None
        self._init_openai()

        # Backend SSH opcional
        self.ssh_backend = ssh_backend
        if self.ssh_backend:
            self.ssh_backend.send_output.connect(self._on_ssh_output)
        self.waiting_for_ssh = False

        # Prompts del sistema para ambos modos
        self.system_prompt_ask = (
            "Eres un agente inteligente integrado en una terminal embebida de Linux "
            "tambiénEres un asistente experto en Linux y administración de servidores. "
            "Tu objetivo es enseñar de forma clara, profesional y concisa. "
            "Cuando el usuario haga una pregunta, responde con explicaciones entendibles y ejemplos si es necesario, "
            "pero evita ser demasiado extenso."
        )

        self.system_prompt_agent = (
            "Eres un agente automatizado que responde únicamente con el comando exacto de Bash necesario para cumplir la instrucción del usuario. "
            "No incluyas explicaciones, contexto, ni advertencias. Solo responde con un bloque de código que contenga el comando necesario."
        )

        self._reset_conversation()
        self._load_styles()

    def _init_openai(self):
        """Inicializa el cliente de OpenAI con la clave de API del entorno."""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            self.chat_area.append("<span style='color:red'>[Error] No se encontró la variable OPENAI_API_KEY en el archivo .env.</span>")
            return
        self.openai_client = openai.OpenAI(api_key=api_key)

    def _reset_conversation(self):
        """Reinicia el historial y contexto de la conversación según el modo actual."""
        self.system_prompt = self.system_prompt_agent if self.agent_mode == "AGENT" else self.system_prompt_ask
        self.conversation_history = [{"role": "system", "content": self.system_prompt}]
        self.chat_area.clear()
        self._send_system_prompt()

    def _send_system_prompt(self):
        """Envía el prompt inicial del sistema al modelo para establecer el contexto."""
        try:
            self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": self.system_prompt}]
            )
        except Exception as e:
            self.chat_area.append(f"<span style='color:red'>[Error al inicializar contexto: {str(e)}]</span>")

    def _on_mode_changed(self, text):
        """Cambia el modo del agente y reinicia la conversación."""
        self.agent_mode = text.upper()
        self._reset_conversation()

    def on_send(self):
        """Envía la instrucción ingresada por el usuario al modelo."""
        prompt = self.prompt_entry.text().strip()
        if not prompt or not self.openai_client:
            return
        self.chat_area.append(f"<b>Tú:</b> {html.escape(prompt)}<br>")
        self.prompt_entry.clear()
        self.conversation_history.append({"role": "user", "content": prompt})
        QtCore.QTimer.singleShot(100, lambda: self._ask_openai())

    def _ask_openai(self):
        """Solicita una respuesta al modelo con el historial de conversación."""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=self.conversation_history
            )
            content = response.choices[0].message.content.strip()
            self.conversation_history.append({"role": "assistant", "content": content})
            html_content = self._render_markdown(content)
            self.chat_area.append(f"<b>Copilot:</b><br>{html_content}<br>")

            code = self._extract_code(content)
            if code and self.ssh_backend and self.agent_mode == "AGENT":
                self._send_ssh_command(code)

        except Exception as e:
            self.chat_area.append(f"<span style='color:red'>[Error] {html.escape(str(e))}</span>")

    def _render_markdown(self, md_text):
        """Convierte texto Markdown a HTML."""
        try:
            html_text = markdown.markdown(md_text, extensions=["fenced_code"])
            return html_text
        except Exception as e:
            return f"<pre>Error al renderizar Markdown: {html.escape(str(e))}</pre>"

    def _extract_code(self, content):
        """Extrae bloques de código de una respuesta en texto Markdown."""
        code_lines = []
        in_code = False
        for line in content.splitlines():
            if "```" in line:
                in_code = not in_code
                continue
            if in_code:
                code_lines.append(line)
        return "\n".join(code_lines) if code_lines else None

    def _send_ssh_command(self, code):
        """Envía un comando por SSH al servidor si hay backend conectado."""
        if self.ssh_backend:
            self.waiting_for_ssh = True
            self.last_command = code
            if not code.endswith("\n"):
                code += "\n"
            self.ssh_backend.write_data(code)
            self.chat_area.append("<i>Enviando comando al servidor SSH...</i><br>")
        else:
            self.chat_area.append("<span style='color:red'>[Error] No hay conexión SSH activa.</span><br>")

    def _on_ssh_output(self, data):
        """Muestra la salida del comando SSH y solicita una explicación al agente."""
        if self.waiting_for_ssh:
            self.chat_area.append(f"<b>SSH:</b><br><pre>{html.escape(data)}</pre><br>")
            self.waiting_for_ssh = False
            QtCore.QTimer.singleShot(100, lambda: self._explain_ssh_output(data))

    def _explain_ssh_output(self, ssh_output):
        """Envía al agente la salida SSH para que sea explicada en lenguaje simple."""
        try:
            prompt = (
                f"Acabo de ejecutar el comando: {self.last_command.strip()} en una terminal Linux. "
                f"Esta fue la salida:\n{ssh_output}\n\nExplícale al usuario de forma sencilla qué significa esta salida y qué archivos o información se listó, si aplica."
            )
            self.conversation_history.append({"role": "user", "content": prompt})
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=self.conversation_history
            )
            content = response.choices[0].message.content.strip()
            self.conversation_history.append({"role": "assistant", "content": content})
            html_content = self._render_markdown(content)
            self.chat_area.append(f"<b>Copilot (explicación):</b><br>{html_content}<br>")
        except Exception as e:
            self.chat_area.append(f"<span style='color:red'>[Error explicando salida SSH: {html.escape(str(e))}]</span>")

    def _load_styles(self):
        """Carga los estilos desde styles/copilot.qss."""
        try:
            qss_path = os.path.join(os.path.dirname(__file__), "styles", "copilot.qss")
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f"Error al cargar estilos del Copilot: {e}")
