# model.py
import paramiko

class ModeloSSH:
    def __init__(self, host, puerto, usuario, clave):
        self.host = host
        self.puerto = puerto
        self.usuario = usuario
        self.clave = clave
        self.cliente = None

    def conectar(self):
        try:
            self.cliente = paramiko.SSHClient()
            self.cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.cliente.connect(self.host, port=self.puerto, username=self.usuario, password=self.clave)
        except paramiko.AuthenticationException:
            raise Exception("Autenticación fallida. Verifica tus credenciales.")
        except paramiko.SSHException as e:
            raise Exception(f"Error en la conexión SSH: {e}")
        except Exception as e:
            raise Exception(f"Error inesperado al conectar: {e}")

    def desconectar(self):
        try:
            if self.cliente:
                self.cliente.close()
                self.cliente = None
        except Exception as e:
            print(f"Error al desconectar: {e}")

    def get_transport(self):
        if not self.cliente:
            raise Exception("Conexión no establecida. El cliente SSH es None.")
        transport = self.cliente.get_transport()
        if not transport:
            raise Exception("No se pudo obtener el transporte SSH. Verifica la conexión.")
        if not transport.is_active():
            raise Exception("El transporte SSH no está activo.")
        return transport
