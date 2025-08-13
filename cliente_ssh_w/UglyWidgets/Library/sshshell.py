from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from .sshshellreader import ShellReaderThread
import time
import paramiko



class Backend(QObject):
    def send_command(self, command):
        """Envía un comando al canal SSH usando write_data."""
        self.write_data(command + '\n')
    send_output = pyqtSignal(str)
    buffer = ""
    # Add port to the constructor parameters
    def __init__(self, host, port, username, password, parrent_widget, parent=None):
        super().__init__(parent)
        self.parrent_widget = parrent_widget
        self.client = paramiko.SSHClient()
        self.client.load_system_host_keys()  # Load known host keys from the system
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Automatically add unknown hosts
        host = str(host).strip()
        port = int(port)
        username = str(username).strip()
        password = str(password).strip()
        # Connect to the remote server
        try:
            self.client.connect(hostname=host, port=port, username=username, password=password, look_for_keys=False, timeout=30)
        except paramiko.AuthenticationException as e:
            raise Exception(f"Autenticación fallida: {e}")
        except paramiko.SSHException as e:
            raise Exception(f"Error SSH: {e}")
        except Exception as e:
            raise Exception(f"Error de conexión: {e}")

        # setup paramiko channel
        try:
            self.channel = self.client.invoke_shell("xterm")
            self.channel.set_combine_stderr(True)
            print("Invoked Shell!")
        except Exception as e:
            print(e)
            print(f"Shell not supported, falling back to pty...")
            transport = self.client.get_transport()
            options = transport.get_security_options()
            print(options)

            self.channel = transport.open_session()
            self.channel.get_pty()  # Request a pseudo-terminal
            # self.channel.invoke_shell()
            self.channel.set_combine_stderr(True)
        self.reader_thread = ShellReaderThread(self.channel)
        self.reader_thread.data_ready.connect(self.send_output)
        self.reader_thread.start()
    def close(self):
        try:
            if hasattr(self, 'reader_thread') and self.reader_thread.isRunning():
                self.reader_thread.stop()
                self.reader_thread.wait()
        except Exception as e:
            # Propaga la excepción para que la GUI la capture
            raise

    @pyqtSlot(str)
    def write_data(self, data):
        """Envía datos al canal con pequeños reintentos si aún no está listo."""
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                if self.channel.send_ready():
                    try:
                        self.channel.send(data)
                        return
                    except paramiko.SSHException as e:
                        print(f"Error while writing to channel: {e}")
                        return
                # Si no está listo, pequeña espera y reintenta
                time.sleep(0.05)
            except Exception as e:
                print(e)
                break

    @pyqtSlot(str)
    def set_pty_size(self, data):
        try:
            if self.channel.send_ready():
                try:
                    cols = data.split("::")[0]
                    cols = int(cols.split(":")[1])
                    rows = data.split("::")[1]
                    rows = int(rows.split(":")[1])
                    self.channel.resize_pty(width=cols, height=rows)
                    print(f"backend pty resize -> cols:{cols} rows:{rows}")
                except paramiko.SSHException as e:
                    print(f"Error setting backend pty term size: {e}")
        except Exception as e:
            print(e)

    def __del__(self):
        self.client.close()