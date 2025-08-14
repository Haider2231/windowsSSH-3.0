import markdown
import re


class MarkdownService:
    def render(self, md):
        """Convierte texto Markdown a HTML."""
        return markdown.markdown(md, extensions=["fenced_code"])

    def extract_code(self, md: str):
        """
        Extrae comandos priorizando bloques multi-línea.
        Orden:
        1) Bloque fenced ```bash|sh|zsh ...``` (devuelve TODO el bloque saneado).
        2) Bloque fenced ``` ...``` sin lenguaje permitido (omitiendo otros lenguajes comunes).
        3) Inline code `...` (posible multi-línea, saneado completo).
        4) Fallback: primera línea plausible (una sola línea saneada).
        """
        if not md:
            return None

        # 1) Bloque fenced con lenguaje de shell permitido (bash|sh|zsh|shell)
        # Requiere salto de línea tras las comillas para evitar capturar lenguajes no permitidos.
        m = re.search(r"```(?:(?:bash|sh|zsh|shell)\s*)?\n([\s\S]*?)```", md, re.IGNORECASE)
        if m:
            block = self._sanitize_block(m.group(1))
            if block:
                return block

        # 2) Alternativa: bloque fenced genérico sin declarar lenguaje, si no parece de otro lenguaje
        # Evita capturar bloques con encabezados típicos de otros lenguajes (python, json, yaml, powershell, etc.)
        m = re.search(r"```\s*\n([\s\S]*?)```", md)
        if m:
            candidate = m.group(1)
            head = candidate.lstrip()[:40].lower()
            if not re.match(r"(def\s|class\s|\{|\[|import\s|from\s|#\!|---|\{\s*\"|<\?xml|function\s)", head):
                block = self._sanitize_block(candidate)
                if block:
                    return block

        # 3) Inline code `...` (permitir salto de línea)
        m = re.search(r"`([^`]+)`", md, re.DOTALL)
        if m:
            block = self._sanitize_block(m.group(1))
            if block:
                return block

        # 4) Fallback: buscar primera línea plausible
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
            # Evitar líneas explicativas largas (heurística)
            if len(s.split()) > 12 and '|' not in s:
                continue
            return s
        return None

    def _sanitize_block(self, txt: str):
        """
        Limpia un bloque multi-línea sin destruir su estructura:
        - Elimina prefijos de prompt ($) por línea.
        - Conserva líneas vacías e indentación (útil en here-docs).
        - No elimina comentarios internos; sólo trimming básico al final de línea.
        """
        if txt is None:
            return None
        lines = []
        for l in txt.splitlines():
            if l.strip() == "":
                lines.append("")
                continue
            s = re.sub(r'^\$+\s*', '', l.rstrip())
            lines.append(s)
        out = "\n".join(lines).strip("\n")
        return out if out.strip() else None

    def _sanitize_first_line(self, txt: str):
        for l in txt.splitlines():
            l = l.strip()
            if not l:
                continue
            l = re.sub(r'^\$+\s*', '', l)
            l = re.sub(r'\s+#.*$', '', l)
            return l
        return None
