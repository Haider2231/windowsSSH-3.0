import markdown
import re


class MarkdownService:
    def render(self, md):
        """Convierte texto Markdown a HTML."""
        return markdown.markdown(md, extensions=["fenced_code"])

    def extract_code(self, md: str):
        """
        Extrae un comando desde la respuesta del modelo aplicando varias capas:
        1) Bloque fenced triple backticks (```), aceptando opcionalmente bash|sh|zsh como lenguaje.
        2) Inline code con backticks simples.
        3) Fallback: primera línea no vacía que parezca un comando (ignora títulos y prompts '$').

        Devuelve sólo la primera línea limpia (sin comentarios finales ni prefijos de prompt).
        """
        if not md:
            return None

        # 1) Bloque fenced con posible lenguaje
        m = re.search(r"```(?:bash|sh|zsh)?\s*(.*?)```", md, re.DOTALL | re.IGNORECASE)
        if m:
            cmd = self._sanitize_first_line(m.group(1))
            if cmd:
                return cmd

        # 2) Inline code `...`
        m = re.search(r"`([^`]+)`", md)
        if m:
            cmd = self._sanitize_first_line(m.group(1))
            if cmd:
                return cmd

        # 3) Fallback: buscar primera línea plausible
        for line in md.splitlines():
            s = line.strip()
            if not s:
                continue
            # Quitar prefijo de prompt común
            s = re.sub(r'^\$+\s*', '', s)
            # Quitar comentarios al final (# ...)
            s = re.sub(r'\s+#.*$', '', s)
            # Evitar encabezados tipo "Algo:" o markdown
            if not s or s.endswith(":"):
                continue
            # Evitar líneas explicativas largas (heurística: espacios > 5 sin pipes)
            if len(s.split()) > 12:
                continue
            return s
        return None

    def _sanitize_first_line(self, txt: str):
        for l in txt.splitlines():
            l = l.strip()
            if not l:
                continue
            l = re.sub(r'^\$+\s*', '', l)
            l = re.sub(r'\s+#.*$', '', l)
            return l
        return None
