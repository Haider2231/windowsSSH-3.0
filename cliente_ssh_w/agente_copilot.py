import os
import openai
import html
import markdown
from dotenv import load_dotenv
from PyQt6.QtGui import QTextOption
from PyQt6 import QtWidgets, QtCore


def get_resource_path(relative_path):
    return os.path.join(os.path.dirname(__file__), relative_path)


class CopilotAgentWidget(QtWidgets.QWidget):
    def __init__(self, ssh_backend=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agente Copilot SSH")

        self.layout = QtWidgets.QVBoxLayout(self)

        # Selector de modo
        self.agent_mode = "ASK"
        self.mode_selector = QtWidgets.QComboBox()
        self.mode_selector.addItems(["Ask", "Agent"])
        self.mode_selector.setCurrentText("Ask")
        self.mode_selector.setFixedWidth(100)
        self.mode_selector.currentTextChanged.connect(self._on_mode_changed)

        # Botón de nuevo chat
        self.new_chat_button = QtWidgets.QPushButton("Nuevo chat")
        self.new_chat_button.setFixedWidth(100)
        self.new_chat_button.clicked.connect(self._reset_conversation)

        # Encabezado con selector y botón
        self.top_controls = QtWidgets.QHBoxLayout()
        self.top_controls.addWidget(self.mode_selector)
        self.top_controls.addWidget(self.new_chat_button)
        self.top_controls.addStretch()
        self.layout.addLayout(self.top_controls)

        # Área de chat
        self.chat_area = QtWidgets.QTextEdit()
        self.chat_area.document().setDefaultStyleSheet("""
  pre {
    white-space: pre-wrap;       /* permite quiebre de línea */
    word-wrap: break-word;       /* quiebra palabras largas */
  }
""")
        self.chat_area.setLineWrapMode(QtWidgets.QTextEdit.LineWrapMode.WidgetWidth)
        self.chat_area.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.chat_area.setReadOnly(True)
        self.chat_area.setAcceptRichText(True)
        self.chat_area.setMinimumHeight(320) 
        self.chat_area.setMinimumWidth(220) 
        self.layout.addWidget(self.chat_area)

        # Entrada de usuario y botón enviar
        self.input_layout = QtWidgets.QHBoxLayout()
        self.prompt_entry = QtWidgets.QLineEdit()
        self.prompt_entry.setPlaceholderText("Escribe tu pregunta o instrucción...")
        self.input_layout.addWidget(self.prompt_entry)
        self.send_button = QtWidgets.QPushButton("Enviar")
        self.send_button.clicked.connect(self.on_send)
        self.input_layout.addWidget(self.send_button)
        self.layout.addLayout(self.input_layout)

        # Inicialización
        load_dotenv(get_resource_path('.env'))
        self.openai_client = None
        self._init_openai()
        self.ssh_backend = ssh_backend
        if self.ssh_backend:
            self.ssh_backend.send_output.connect(self._on_ssh_output)
        self.waiting_for_ssh = False

        self.system_prompt = (
            "Eres un agente inteligente integrado en una terminal embebida de Linux y también Eres un asistente experto en Linux y administración de servidores. "
            "Tu objetivo es facilitar, automatizar y enseñar el uso de Linux a los usuarios, incluso si no tienen experiencia previa. "
            "Puedes enviar comandos directamente a la terminal SSH remota y mostrar la salida en este chat. "
            "Cuando el usuario solicite una acción, aunque sea de forma poco técnica o con frases como 'dame el comando', 'ejecuta', 'haz', 'quiero', 'cómo hago', 'crea', 'muestra', 'borra', 'instala', 'actualiza', 'reinicia', etc., responde con el comando exacto en un bloque de código (sin explicaciones), para que pueda ser ejecutado automáticamente en la terminal. "
            "Si el usuario pide ayuda, puedes explicar conceptos, pero si pide ejecutar, crear, mostrar, instalar, borrar, modificar, o cualquier acción, responde solo con el comando necesario en un bloque de código. "
            "Puedes crear, modificar y leer archivos, instalar paquetes, mostrar ejemplos, explicar comandos y ayudar a resolver problemas de Linux. "
            "No incluyas advertencias ni confirmaciones, solo el comando o la explicación según corresponda. "
            "Si el usuario no es específico, deduce la intención y responde con el comando más útil para la tarea en un bloque de código. "
            "Recuerda: tu prioridad es enseñar y automatizar el uso de Linux de la forma más sencilla posible para el usuario."
        )
        self._reset_conversation()
        self._load_styles()

    def _init_openai(self):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            self.chat_area.append("<span style='color:red'>[Error] No se encontró la variable OPENAI_API_KEY en el archivo .env.</span>")
            return
        self.openai_client = openai.OpenAI(api_key=api_key)

    def _reset_conversation(self):
        self.conversation_history = [{"role": "system", "content": self.system_prompt}]
        self.chat_area.clear()
        self._send_system_prompt()

    def _send_system_prompt(self):
        try:
            self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": self.system_prompt}]
            )
        except Exception as e:
            self.chat_area.append(f"<span style='color:red'>[Error al inicializar contexto: {str(e)}]</span>")

    def _on_mode_changed(self, text):
        self.agent_mode = text.upper()
        self._reset_conversation()

    def on_send(self):
        prompt = self.prompt_entry.text().strip()
        if not prompt or not self.openai_client:
            return
        self.chat_area.append(f"<b>Tú:</b> {html.escape(prompt)}<br>")
        self.prompt_entry.clear()

        if self.agent_mode == "AGENT":
            prompt_for_ai = f"Dame solo el comando exacto en bash para esto, en un bloque de código, sin explicación: {prompt}"
        else:
            prompt_for_ai = (
                f"Explica de forma clara, profesional y concisa como un experto en Linux y administración de servidores. "
                f"Si corresponde, incluye ejemplos de comandos, pero no seas excesivamente extenso. Pregunta: {prompt}"
            )

        self.conversation_history.append({"role": "user", "content": prompt_for_ai})
        QtCore.QTimer.singleShot(100, lambda: self._ask_openai())

    def _ask_openai(self):
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
        try:
            html_text = markdown.markdown(md_text, extensions=["fenced_code"])
            return html_text
        except Exception as e:
            return f"<pre>Error al renderizar Markdown: {html.escape(str(e))}</pre>"

    def _extract_code(self, content):
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
        if self.waiting_for_ssh:
            self.chat_area.append(f"<b>SSH:</b><br><pre>{html.escape(data)}</pre><br>")
            self.waiting_for_ssh = False
            QtCore.QTimer.singleShot(100, lambda: self._explain_ssh_output(data))

    def _explain_ssh_output(self, ssh_output):
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
        """Carga los estilos desde styles/copilot.qss"""
        try:
            qss_path = os.path.join(os.path.dirname(__file__), "styles", "copilot.qss")
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f"Error al cargar estilos del Copilot: {e}")
