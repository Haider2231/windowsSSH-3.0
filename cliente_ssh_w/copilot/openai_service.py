import openai
import os

class OpenAIServiceError(Exception):
    pass

class OpenAIService:
    def __init__(self, api_key, default_model=None, timeout=None):
        self.client = openai.OpenAI(api_key=api_key)
        self.default_model = default_model or os.getenv("OPENAI_DEFAULT_MODEL", "gpt-3.5-turbo")
        self.timeout = timeout or float(os.getenv("OPENAI_TIMEOUT", "30"))


    def chat(self, messages, model=None, timeout=None):
        """Envía mensajes al modelo especificado y retorna la respuesta. Maneja errores y permite timeout/modelo por defecto."""
        model = model or self.default_model
        timeout = timeout or self.timeout
        try:
            return self.client.chat.completions.create(model=model, messages=messages, timeout=timeout)
        except Exception as e:
            # Aquí podrías loguear el error con logging en vez de print
            print(f"Error en OpenAIService.chat: {e}")
            raise OpenAIServiceError(f"Error al comunicarse con OpenAI: {e}")
