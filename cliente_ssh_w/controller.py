# controller.py
from ssh_model import ModeloSSH

class Controlador:
    def __init__(self, host, puerto, usuario, clave):
        self.modelo = ModeloSSH(host, puerto, usuario, clave)

    def conectar(self):
        try:
            self.modelo.conectar()
            transport = self.modelo.get_transport()
            if not transport:
                raise Exception("El transporte SSH es None después de conectar.")
            return transport
        except Exception as e:
            raise Exception(f"Error en el controlador al conectar: {e}")

    def desconectar(self):
        self.modelo.desconectar()
