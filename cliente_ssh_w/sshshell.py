from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from sshshellreader import ShellReaderThread

import paramiko



class Backend(QObject):
    send_output = pyqtSignal(str)
    buffer = ""
    def __init__(self, host, username, password, parrent_widget, port=22, parent=None):
        super().__init__(parent)
        self.parrent_widget = parrent_widget
        try:
            self.client = paramiko.SSHClient()
            self.client.load_system_host_keys()  # Load known host keys from the system
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Automatically add unknown hosts
            host = str(host).strip()
            username = str(username).strip()
            password = str(password).strip()
            # Usa el puerto recibido (por defecto 22 si no se pasa)
            try:
                self.client.connect(hostname=host, port=port, username=username, password=password, look_for_keys=False)
            except paramiko.AuthenticationException as e:
                print(f"Failed to authenticate: {e}")
            except paramiko.SSHException as e:
                print(f"SSH connection failed: {e}")
            except Exception as e:
                print(e)

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
                self.channel.get_pty()
                self.channel.set_combine_stderr(True)
            # self.client.
            # Cambia el hilo lector por uno más eficiente
            import threading
            def fast_reader():
                import time
                while True:
                    try:
                        if self.channel.recv_ready():
                            data = self.channel.recv(4096).decode(errors='ignore')
                            if data:
                                self.send_output.emit(data)
                        if self.channel.exit_status_ready():
                            break
                        time.sleep(0.001)  # sleep mínimo para evitar 100% CPU
                    except Exception as e:
                        print(f"Error de lectura: {e}")
                        break
            threading.Thread(target=fast_reader, daemon=True).start()
        except Exception as e:
            print(e)

    @pyqtSlot(str)
    def write_data(self, data):
        try:
            if self.channel.send_ready():
                try:
                    self.channel.send(data)
                except paramiko.SSHException as e:
                    print(f"Error while writing to channel: {e}")
        except Exception as e:
            print(e)

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