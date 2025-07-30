from PyQt6.QtWebEngineCore import QWebEngineUrlSchemeHandler
from PyQt6.QtCore import QByteArray
import os

class WebEngineUrlSchemeHandler(QWebEngineUrlSchemeHandler):
    def requestStarted(self, request):
        data = QByteArray()
        try:
            with open(get_resource_path(request.requestUrl().path()[1:]), 'rb') as f:
                data = QByteArray(f.read())
        except Exception as e:
            print(f"Failed to open file: {e}")
        buf = data
        request.reply(buf)

def get_resource_path(relative_path):
    return os.path.join(os.path.dirname(__file__), relative_path)
