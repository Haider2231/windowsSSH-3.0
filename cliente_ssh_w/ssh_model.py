import paramiko

class ModeloSSH:
    """
    Clase que gestiona la conexión SSH usando la biblioteca Paramiko.
    Proporciona métodos para conectar, desconectar y acceder al transporte SSH.
    """

    def __init__(self, host, puerto, usuario, clave):
        """
        Inicializa los parámetros de conexión SSH.

        :param host: Dirección IP o hostname del servidor.
        :param puerto: Puerto del servicio SSH.
        :param usuario: Nombre de usuario SSH.
        :param clave: Contraseña del usuario SSH.
        """
        self.host = host
        self.puerto = puerto
        self.usuario = usuario
        self.clave = clave
        self.cliente = None

    def conectar(self):
        """
        Intenta establecer una conexión SSH con los parámetros proporcionados.
        Lanza una excepción descriptiva en caso de error.
        """
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
        """
        Cierra la conexión SSH si está activa.
        Silencia errores inesperados al cerrar.
        """
        try:
            if self.cliente:
                self.cliente.close()
                self.cliente = None
        except Exception as e:
            print(f"Error al desconectar: {e}")

    def get_transport(self):
        """
        Obtiene el canal de transporte activo del cliente SSH.

        :return: Objeto de tipo paramiko.Transport
        :raises Exception: Si no hay cliente, el transporte no está disponible o no está activo.
        """
        if not self.cliente:
            raise Exception("Conexión no establecida. El cliente SSH es None.")
        transport = self.cliente.get_transport()
        if not transport:
            raise Exception("No se pudo obtener el transporte SSH. Verifica la conexión.")
        if not transport.is_active():
            raise Exception("El transporte SSH no está activo.")
        return transport
