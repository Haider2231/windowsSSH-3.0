from PyQt6.QtCore import QObject, pyqtSignal

class CopilotController(QObject):
    def set_mode(self, mode: str):
        self.mode = mode.upper() if isinstance(mode, str) else "ASK"
    response_ready = pyqtSignal(str)
    ssh_output_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, openai_service, markdown_service, ssh_service=None, model="gpt-3.5-turbo"):
        super().__init__()
        self.openai = openai_service
        self.md = markdown_service
        self.ssh = ssh_service
        self.model = model
        self.history = []
        self.system_prompt = ""
        self._init_ssh_output_connection()

    def _init_ssh_output_connection(self):
        # Conectar a la señal correcta del backend (send_output). Se mantiene compatibilidad si hubiera 'output_ready'.
        if self.ssh:
            if hasattr(self.ssh, 'send_output'):
                try:
                    self.ssh.send_output.connect(self.handle_ssh_output)
                except Exception:
                    pass
            elif hasattr(self.ssh, 'output_ready'):
                try:
                    self.ssh.output_ready.connect(self.handle_ssh_output)
                except Exception:
                    pass

    def set_system_prompt(self, prompt):
        self.system_prompt = prompt
        self.reset_history()
        # Asegurar modo por defecto si no está definido
        if not hasattr(self, 'mode'):
            self.mode = 'ASK'

    def reset_history(self):
        self.history = [{"role": "system", "content": self.system_prompt}]

    def send_prompt(self, prompt):
        # Solo el controlador maneja el hilo de OpenAI
        from PyQt6.QtCore import QThread, pyqtSignal, QObject
        self.history.append({"role": "user", "content": prompt})

        class OpenAIWorker(QObject):
            finished = pyqtSignal(object)
            error = pyqtSignal(str)

            def __init__(self, openai, history, model):
                super().__init__()
                self.openai = openai
                self.history = history
                self.model = model

            def run(self):
                try:
                    # CORREGIDO: orden correcto de parámetros
                    response = self.openai.chat(self.history, self.model)
                    self.finished.emit(response)
                except Exception as e:
                    self.error.emit(str(e))

        self._thread = QThread()
        self._worker = OpenAIWorker(self.openai, self.history.copy(), self.model)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_openai_response)
        self._worker.error.connect(self._on_openai_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _on_openai_response(self, response):
        try:
            content = response.choices[0].message.content.strip()
            self.history.append({"role": "assistant", "content": content})
            html_content = self.md.render(content)
            self.response_ready.emit(html_content)
            code = self.md.extract_code(content)
            # Solo enviar comandos si el modo es AGENT
            if code and self.ssh and getattr(self, 'mode', 'ASK') == "AGENT":
                try:
                    self.ssh.send_command(code)
                except Exception as e:
                    self.error_occurred.emit(f"Error enviando comando SSH: {e}")
        except Exception as e:
            self.error_occurred.emit(f"Error procesando respuesta: {e}")

    def _on_openai_error(self, error_msg):
        self.error_occurred.emit(f"Error en OpenAI: {error_msg}")

    def handle_ssh_output(self, data):
        self.ssh_output_ready.emit(data)
