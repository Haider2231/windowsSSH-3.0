import os
import openai
import html
from dotenv import load_dotenv
from PyQt6 import QtWidgets, QtCore, QtGui

class CopilotAgentWidget(QtWidgets.QWidget):
    def __init__(self, ssh_backend=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agente Copilot SSH")
        self.setStyleSheet("""
            QWidget { font-family: 'Segoe UI'; font-size: 14px; }
            QLineEdit, QTextEdit { border-radius: 4px; border: 1px solid #ccc; padding: 6px; }
            QPushButton { background-color: #0078d7; color: white; border-radius: 5px; padding: 6px 12px; }
            QPushButton:hover { background-color: #005fa1; }
        """)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.chat_area = QtWidgets.QTextEdit()
        self.chat_area.setReadOnly(True)
        self.layout.addWidget(self.chat_area)
        
        self.input_layout = QtWidgets.QHBoxLayout()
        self.prompt_entry = QtWidgets.QLineEdit()
        self.prompt_entry.setPlaceholderText("Escribe tu pregunta o instrucción...")
        self.input_layout.addWidget(self.prompt_entry)
        self.send_button = QtWidgets.QPushButton("Enviar")
        self.send_button.clicked.connect(self.on_send)
        self.input_layout.addWidget(self.send_button)
        self.layout.addLayout(self.input_layout)

        load_dotenv()
        self.openai_client = None
        self._init_openai()
        self.ssh_backend = ssh_backend
        if self.ssh_backend:
            self.ssh_backend.send_output.connect(self._on_ssh_output)
        self.waiting_for_ssh = False

        # Prompt de sistema para dar contexto al agente
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
        self.conversation_history = [
            {"role": "system", "content": self.system_prompt}
        ]
        self._send_system_prompt()

    def _init_openai(self):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            self.chat_area.append("<span style='color:red'>[Error] No se encontró la variable OPENAI_API_KEY en el archivo .env.</span>")
            return
        self.openai_client = openai.OpenAI(api_key=api_key)

    def _send_system_prompt(self):
        # Enviar el contexto al modelo al iniciar
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": self.system_prompt}]
            )
            # No mostramos la respuesta, solo inicializamos el contexto
        except Exception as e:
            self.chat_area.append(f"<span style='color:red'>[Error al inicializar contexto: {str(e)}]</span>")

    def on_send(self):
        prompt = self.prompt_entry.text().strip()
        if not prompt or not self.openai_client:
            return
        self.chat_area.append(f"<b>Tú:</b> {prompt}")
        self.prompt_entry.clear()
        # Detectar intención de acción y mejorar el prompt
        action_words = [
            'listame', 'muéstrame', 'muestrame', 'crea', 'borra', 'elimina', 'instala', 'actualiza', 'reinicia',
            'ejecuta', 'quiero', 'cómo hago', 'como hago', 'haz', 'genera', 'copia', 'mueve', 'renombra', 'descarga', 'sube', 'edita', 'cambia', 'asigna', 'quita', 'agrega', 'agregame', 'dame el comando', 'dame solo el comando', 'dame el script', 'dame el código', 'dame el comando exacto', 'dame el comando en bash', 'dame el comando en un bloque de código'
        ]
        prompt_lower = prompt.lower()
        if any(word in prompt_lower for word in action_words):
            prompt = (
                f"{prompt}. Dame solo el comando exacto en bash para esto, en un bloque de código, sin explicación."
            )
        # Agregar el mensaje del usuario al historial
        self.conversation_history.append({"role": "user", "content": prompt})
        QtCore.QTimer.singleShot(100, lambda: self._ask_openai())

    def _ask_openai(self):
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=self.conversation_history
            )
            content = response.choices[0].message.content.strip()
            # Agregar la respuesta al historial
            self.conversation_history.append({"role": "assistant", "content": content})
            code = self._extract_code(content)
            if code and self.ssh_backend:
                self.chat_area.append(f"<b>Copilot:</b> <pre>{html.escape(code)}</pre>")
                self._send_ssh_command(code)
            else:
                self.chat_area.append(f"<b>Copilot:</b> {content}")
        except Exception as e:
            self.chat_area.append(f"<span style='color:red'>[Error] {str(e)}</span>")

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
        # Enviar el código como comando al backend SSH
        if self.ssh_backend:
            self.waiting_for_ssh = True
            self.last_command = code  # Guardar el último comando enviado
            # Asegura que el comando termine con un salto de línea
            if not code.endswith("\n"):
                code += "\n"
            self.ssh_backend.write_data(code)
            self.chat_area.append("<i>Enviando comando al servidor SSH...</i>")
        else:
            self.chat_area.append("<span style='color:red'>[Error] No hay conexión SSH activa.</span>")

    def _on_ssh_output(self, data):
        if self.waiting_for_ssh:
            import html
            self.chat_area.append(f"<b>SSH:</b> <pre>{html.escape(data)}</pre>")
            self.waiting_for_ssh = False
            # Enviar la salida de la terminal a OpenAI para explicación
            QtCore.QTimer.singleShot(100, lambda: self._explain_ssh_output(data))

    def _explain_ssh_output(self, ssh_output):
        # Enviar la salida de la terminal a OpenAI para que la explique
        try:
            # Agregar la salida de la terminal como mensaje de usuario
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
            self.chat_area.append(f"<b>Copilot (explicación):</b> {content}")
        except Exception as e:
            self.chat_area.append(f"<span style='color:red'>[Error explicando salida SSH: {str(e)}]</span>")
