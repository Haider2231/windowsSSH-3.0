from PyQt6.QtGui import QTextOption
from PyQt6 import QtWidgets, QtCore
from .widgets import AutoGrowTextEdit

class CopilotAgentWidget(QtWidgets.QWidget):
    """
    Widget UI para interactuar con el controlador CopilotController.
    """
    def closeEvent(self, event):
        # Desconectar señales del controlador
        try:
            self.controller.response_ready.disconnect(self.show_response)
        except Exception:
            pass
        # Nota: no existe señal ssh_output_ready en CopilotController actual
        try:
            self.controller.error_occurred.disconnect(self.show_error_message)
        except Exception:
            pass

        # Limpiar hilo de envío si existe
        if hasattr(self, '_send_thread') and self._send_thread is not None:
            try:
                self._send_thread.quit()
                self._send_thread.wait()
            except Exception:
                pass
            self._send_thread = None

        event.accept()

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller

        self.layout = QtWidgets.QVBoxLayout(self)

        # Selector de modo
        self.agent_mode = "ASK"
        self.mode_selector = QtWidgets.QComboBox()
        self.mode_selector.addItems(["Ask", "Agent"])
        self.mode_selector.setCurrentText("Ask")
        self.mode_selector.setFixedWidth(100)
        self.mode_selector.currentTextChanged.connect(self._on_mode_changed)

        # Botón para nuevo chat
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
        self.chat_area.setLineWrapMode(QtWidgets.QTextEdit.LineWrapMode.WidgetWidth)
        self.chat_area.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.chat_area.setReadOnly(True)
        self.chat_area.setAcceptRichText(True)
        self.chat_area.setMinimumHeight(390)
        self.chat_area.setMinimumWidth(250)
        self.layout.addWidget(self.chat_area)

        # Entrada del usuario
        self.input_layout = QtWidgets.QHBoxLayout()
        self.prompt_entry = AutoGrowTextEdit(max_visible_lines=7)
        self.prompt_entry.setObjectName("promptEntry")  # Para que aplique el mismo QSS
        self.input_layout.addWidget(self.prompt_entry)

        self.send_button = QtWidgets.QPushButton("Enviar")
        self.send_button.clicked.connect(self.on_send)
        self.input_layout.addWidget(self.send_button)
        self.layout.addLayout(self.input_layout)

        # Conectar la señal de Enter (sin Shift) ignorando el texto emitido
        self.prompt_entry.submitted.connect(lambda _text: self.on_send())

        # Conexión de señales del controlador
        self.controller.response_ready.connect(self.show_response)
        self.controller.error_occurred.connect(self.show_error_message)

        self._reset_conversation()
        self._load_styles()

    # ----------------- UI Actions -----------------

    def _reset_conversation(self):
        self.chat_area.clear()
        self.controller.set_system_prompt(self._get_system_prompt())

    def _on_mode_changed(self, text):
        self.agent_mode = text.upper()  # "ASK" o "AGENT"
        self.controller.set_mode(self.agent_mode)
        self._reset_conversation()

    def on_send(self):
        prompt = self.prompt_entry.toPlainText().strip()
        if not prompt:
            return
        self.chat_area.append(f"<b>Tú:</b> {prompt}<br>")
        self.prompt_entry.clear()
        try:
            self.controller.send_prompt(prompt)
        except Exception as e:
            self.chat_area.append(f"<span style='color:red;'><b>Error:</b> {str(e)}</span><br>")
            QtWidgets.QMessageBox.critical(self, "Error Copilot", str(e))

    # ----------------- Slots (señales del controller) -----------------

    def show_response(self, html):
        """Muestra respuesta del asistente en el chat (HTML ya renderizado)."""
        self.chat_area.append(f"<b>Copilot:</b><br>{html}<br>")

    def show_ssh_output(self, data):
        """
        NO reflejar salida SSH en el chat NUNCA.
        La terminal ya la muestra en su propio widget/vista.
        """
        return  # Intencionalmente vacío

    def show_error_message(self, message):
        self.chat_area.append(f"<span style='color:red;'><b>Error:</b> {message}</span><br>")

    # ----------------- System Prompts -----------------

    def _get_system_prompt(self):
        identidad_regla = (
            "REGLA DE IDENTIDAD:\n"
            "Si el usuario pregunta o hace referencia a quién eres (p. ej. '¿quién eres?', "
            "'qué eres', 'tu identidad', 'quién es el agente'), responde EXACTAMENTE:\n"
            "\"Soy un agente en consola diseñado para apoyar el aprendizaje en el uso de Linux.\"\n"
            "No añadas texto adicional, disculpas ni explicaciones cuando apliques esta regla.\n"
        )

        if self.agent_mode == "AGENT":
            return (
                identidad_regla +
                "ACTÚA COMO UN EJECUTOR DE COMANDOS.\n"
                "Instrucciones estrictas de formato (DEBES CUMPLIRLAS):\n"
                "1. Devuelve ÚNICAMENTE un bloque de código fenced con triple backticks.\n"
                "2. No añadas texto antes ni después del bloque. Nada de explicaciones.\n"
                "3. Dentro del bloque, la PRIMERA línea debe ser exactamente el comando Bash a ejecutar.\n"
                "4. No incluyas prefijos como $, #, ni comentarios.\n"
                "5. Si necesitas varios comandos, sepáralos en líneas sucesivas (una por línea) SIN comentarios.\n"
                "6. No uses backticks dentro del bloque salvo los de apertura/cierre.\n"
                "Ejemplos válidos:```\nls -la\n```  o  ```\nmkdir informes\ncd informes\n```\n"
                "Ejemplo inválido (NO HACER): Texto fuera del bloque o explicaciones."
            )
        else:
            # ASK: responder pedagógicamente, sin comandos forzados
            return (
                identidad_regla +
                "MODO ASK (EXPLICACIÓN). Responde con claridad y de forma pedagógica.\n"
                "SI, Y SOLO SI, el usuario pide pasos/acciones o un comando ayudaría, "
                "incluye al final un bloque de código con triple backticks bash como sugerencia.\n"
                "Si la pregunta es conceptual (p.ej. '¿qué es Linux?'), NO incluyas ningún bloque de código.\n"
                "Nunca asumas credenciales ni ejecutes nada: el código en ASK es MERA SUGERENCIA."
            )

    # ----------------- Estilos -----------------

    def _load_styles(self):
        try:
            from resources import load_qss
            self.setStyleSheet(load_qss("styles/copilot.qss"))
        except Exception as e:
            print(f"Error al cargar estilos del Copilot: {e}")
