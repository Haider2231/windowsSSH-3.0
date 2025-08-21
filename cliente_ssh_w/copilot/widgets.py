# --- Componente auxiliar: AutoGrowTextEdit ---
from PyQt6 import QtWidgets, QtCore, QtGui

class AutoGrowTextEdit(QtWidgets.QTextEdit):
    submitted = QtCore.pyqtSignal(str)

    def __init__(self, parent=None, max_visible_lines=7):
        super().__init__(parent)
        self._max_visible_lines = max_visible_lines
        self._cached_doc_margin = 0

        # UX: wrap al ancho del widget y en límites de palabra
        self.setLineWrapMode(QtWidgets.QTextEdit.LineWrapMode.WidgetWidth)
        self.setWordWrapMode(QtGui.QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)

        # Placeholder compatible
        self.setPlaceholderText("Escribe tu pregunta o instrucción...")

        # Scroll: apagado hasta llegar al tope; luego AsNeeded
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Sin rich text para evitar tamaños raros por estilos de pegado
        self.setAcceptRichText(False)

        # Escuchar cambios de documento y de tamaño del widget
        self.document().documentLayout().documentSizeChanged.connect(self._recalc_height)
        self.textChanged.connect(self._recalc_height)

        # Guardar margen para cálculos
        self._cached_doc_margin = self.document().documentMargin()

        # Altura mínima: 1 línea
        self._recalc_height()

    def _line_height_px(self):
        fm = QtGui.QFontMetrics(self.font())
        return fm.lineSpacing()

    def _chrome_extra_px(self):
        # Margen del documento + paddings/bordes del viewport aproximados
        # Ajusta si tu QSS agrega más padding; suele funcionar bien así.
        frame = 2 * self.frameWidth() if self.frameShape() != QtWidgets.QFrame.Shape.NoFrame else 0
        return int(self._cached_doc_margin * 2 + frame + 4)

    def _doc_height_px(self):
        # Altura real del texto envuelto al ancho actual
        # Asegúrate de que el ancho del viewport esté actualizado
        doc_size = self.document().documentLayout().documentSize()
        return int(doc_size.height())

    def _max_height_px(self):
        return int(self._line_height_px() * self._max_visible_lines + self._chrome_extra_px())

    def _recalc_height(self):
        # Altura ideal en función del contenido
        ideal = self._doc_height_px() + self._chrome_extra_px()
        max_h = self._max_height_px()

        if ideal <= max_h:
            # Crece sin scroll
            self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.setMaximumHeight(max_h)   # Límite superior “duro”
            self.setMinimumHeight(ideal)   # Altura actual
            self.setFixedHeight(ideal)
        else:
            # Rebasó 7 líneas: fija al máximo y permite scroll
            self.setFixedHeight(max_h)
            self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def resizeEvent(self, e):
        # Recalcular al cambiar de ancho (para wrapping correcto)
        super().resizeEvent(e)
        QtCore.QTimer.singleShot(0, self._recalc_height)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        # UX de chat:
        # Enter = enviar, Shift+Enter = nueva línea
        if event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
            if event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier:
                # Inserta salto de línea normal
                return super().keyPressEvent(event)
            else:
                text = self.toPlainText().strip()
                if text:
                    self.submitted.emit(text)
                    # Borra sin mover el foco ni scrolls bruscos
                    self.clear()
                return  # Consumimos el evento
        super().keyPressEvent(event)
