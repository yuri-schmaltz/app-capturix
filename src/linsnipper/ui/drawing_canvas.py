from __future__ import annotations

from enum import Enum, auto
from typing import Optional

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPixmap, QPen, QColor, QMouseEvent
from PySide6.QtCore import Qt, QPoint, Signal

from ..core.undo import UndoStack


class Tool(Enum):
    PEN = auto()
    HIGHLIGHTER = auto()
    ERASER = auto()
    NONE = auto()


class DrawingCanvas(QWidget):
    """
    Canvas de desenho em cima de um QPixmap (screenshot).
    Possui suporte a:
      - Caneta
      - Marcador
      - Borracha
      - Undo/Redo via UndoStack
    """

    # Sinal opcional, disparado ao terminar um traço (mouseRelease)
    stroke_finished = Signal()

    def __init__(self, parent=None, pixmap: Optional[QPixmap] = None):
        super().__init__(parent)

        base = pixmap or QPixmap(800, 600)
        if base.isNull():
            base = QPixmap(800, 600)
            base.fill(Qt.white)

        self.base_pixmap: QPixmap = base
        self.draw_pixmap: QPixmap = self.base_pixmap.copy()

        self.current_tool: Tool = Tool.PEN
        self.pen_color = QColor(220, 20, 60)          # vermelho
        self.highlight_color = QColor(255, 255, 0, 120)  # amarelo translúcido
        self.eraser_size = 20
        self.pen_width = 3
        self.highlight_width = 15

        self._last_pos = QPoint()

        # Pilha de undo/redo baseada em pixmaps
        self._undo_stack: UndoStack[QPixmap] = UndoStack(max_depth=50)
        self._undo_stack.push(self.draw_pixmap.copy())

        self.setMinimumSize(self.base_pixmap.size())

    # ------------- API pública -------------

    def set_pixmap(self, pixmap: QPixmap):
        """Define um novo pixmap base (por exemplo, nova captura)."""
        if pixmap.isNull():
            return
        self.base_pixmap = pixmap
        self.draw_pixmap = self.base_pixmap.copy()
        self._undo_stack.clear()
        self._undo_stack.push(self.draw_pixmap.copy())
        self.setMinimumSize(self.base_pixmap.size())
        self.update()

    def set_tool(self, tool: Tool):
        self.current_tool = tool

    def get_result_pixmap(self) -> QPixmap:
        """Retorna o pixmap final (base + desenhos)."""
        return self.draw_pixmap

    def undo(self):
        prev = self._undo_stack.undo(self.draw_pixmap.copy())
        if prev is None:
            return
        self.draw_pixmap = prev
        self.update()

    def redo(self):
        nxt = self._undo_stack.redo(self.draw_pixmap.copy())
        if nxt is None:
            return
        self.draw_pixmap = nxt
        self.update()

    # ------------- Eventos de mouse -------------

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            # Guarda estado para undo antes de começar um novo traço
            self._undo_stack.push(self.draw_pixmap.copy())
            self._last_pos = event.pos()

    def mouseMoveEvent(self, event: QMouseEvent):
        if not (event.buttons() & Qt.LeftButton):
            return

        painter = QPainter(self.draw_pixmap)

        if self.current_tool == Tool.PEN:
            pen = QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(self._last_pos, event.pos())

        elif self.current_tool == Tool.HIGHLIGHTER:
            pen = QPen(self.highlight_color, self.highlight_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(self._last_pos, event.pos())

        elif self.current_tool == Tool.ERASER:
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.setPen(Qt.NoPen)
            painter.setBrush(Qt.white)
            r = self.eraser_size // 2
            painter.drawEllipse(event.pos(), r, r)

        painter.end()
        self._last_pos = event.pos()
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.stroke_finished.emit()

    # ------------- Renderização -------------

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.draw_pixmap)
        painter.end()

    def sizeHint(self):
        return self.base_pixmap.size()
