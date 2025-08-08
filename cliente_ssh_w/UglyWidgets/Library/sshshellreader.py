from PyQt6.QtCore import pyqtSignal, QThread


class ShellReaderThread(QThread):
    data_ready = pyqtSignal(str)

    def __init__(self, channel):
        super().__init__()
        self.channel = channel
        self._stopped = False

    def run(self):
        while not self.isInterruptionRequested() and not self.channel.closed:
            try:
                # Detección de cierre de canal (Paramiko)
                if self.channel.exit_status_ready() and not self.channel.recv_ready():
                    print("SSH channel exit status ready and no more data.")
                    break
                if self.channel.recv_ready():
                    data = self.channel.recv(1024)
                    if data:
                        text = data.decode(errors='ignore')
                        self.data_ready.emit(text)
                else:
                    QThread.msleep(10)  # cede CPU 10 ms
            except Exception as e:
                print(f"Error while reading from channel: {e}")
        print("ShellReaderThread terminado.")

    def stop(self):
        self.requestInterruption()
        self._stopped = True
