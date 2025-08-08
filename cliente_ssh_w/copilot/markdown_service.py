import markdown
import re

class MarkdownService:
    def render(self, md):
        """Convierte texto Markdown a HTML."""
        return markdown.markdown(md, extensions=["fenced_code"])

    def extract_code(self, md):
        """Extrae el primer bloque de código triple-backtick del Markdown."""
        match = re.search(r"```(?:\w*\n)?(.*?)```", md, re.DOTALL)
        return match.group(1).strip() if match else None
