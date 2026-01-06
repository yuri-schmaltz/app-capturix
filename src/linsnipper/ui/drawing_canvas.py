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
    Canvas de desenho com suporte a camadas (Fundo + Anotações).
    Isso permite que a borracha apague apenas as anotações, preservando o fundo.
    """

    stroke_finished = Signal()

    def __init__(self, parent=None, pixmap: Optional[QPixmap] = None):
        super().__init__(parent)

        if pixmap and not pixmap.isNull():
            self.base_pixmap = pixmap
        else:
            self.base_pixmap = QPixmap(800, 600)
            self.base_pixmap.fill(Qt.white)

        # Camada de anotação (transparente)
        self.annotation_pixmap = QPixmap(self.base_pixmap.size())
        self.annotation_pixmap.fill(Qt.transparent)

        self.current_tool: Tool = Tool.PEN
        self.pen_color = QColor(220, 20, 60)
        self.highlight_color = QColor(255, 255, 0, 120)
        self.eraser_size = 20
        self.pen_width = 3
        self.highlight_width = 15

        self._last_pos = QPoint()

        # Undo stack armazena apenas a camada de anotação
        self._undo_stack: UndoStack[QPixmap] = UndoStack(max_depth=50)
        self._undo_stack.push(self.annotation_pixmap.copy())

        self.setMinimumSize(self.base_pixmap.size())

    # ------------- API pública -------------

    def set_pixmap(self, pixmap: QPixmap):
        if pixmap.isNull():
            return
        self.base_pixmap = pixmap
        # Redimensiona anotação se necessário
        if self.annotation_pixmap.size() != self.base_pixmap.size():
            self.annotation_pixmap = QPixmap(self.base_pixmap.size())
        
        self.annotation_pixmap.fill(Qt.transparent)
        
        self._undo_stack.clear()
        self._undo_stack.push(self.annotation_pixmap.copy())
        
        self.setMinimumSize(self.base_pixmap.size())
        self.update()

    def set_tool(self, tool: Tool):
        self.current_tool = tool

    def get_result_pixmap(self) -> QPixmap:
        """Combina fundo e anotações para salvar/copiar."""
        result = self.base_pixmap.copy()
        painter = QPainter(result)
        painter.drawPixmap(0, 0, self.annotation_pixmap)
        painter.end()
        return result

    def undo(self):
        prev = self._undo_stack.undo(self.annotation_pixmap.copy())
        if prev is not None:
            self.annotation_pixmap = prev
            self.update()

    def redo(self):
        nxt = self._undo_stack.redo(self.annotation_pixmap.copy())
        if nxt is not None:
            self.annotation_pixmap = nxt
            self.update()

    # ------------- Eventos de mouse -------------

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            # Salva estado ANTES do novo traço
            self._undo_stack.push(self.annotation_pixmap.copy())
            self._last_pos = event.pos()

    def mouseMoveEvent(self, event: QMouseEvent):
        if not (event.buttons() & Qt.LeftButton):
            return

        painter = QPainter(self.annotation_pixmap)

        if self.current_tool == Tool.PEN:
            pen = QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(self._last_pos, event.pos())

        elif self.current_tool == Tool.HIGHLIGHTER:
            # Highlighter precisa de composição especial para não "lavar" a cor de baixo se passar por cima
            # Mas na camada transparente, SourceOver padrão funciona bem, apenas somando a cor.
            # Se quisermos efeito de marca-texto real sobre o fundo, precisaríamos de CompositionMode_Multiply 
            # na hora de compor com o fundo, mas aqui estamos desenhando na camada de anotação.
            pen = QPen(self.highlight_color, self.highlight_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(self._last_pos, event.pos())

        elif self.current_tool == Tool.ERASER:
            # O segredo: Apagar na camada de anotação = Tornar transparente
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.setPen(Qt.NoPen)
            painter.setBrush(Qt.black) # Cor não importa, pois Mode_Clear zera o pixel
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
        # 1. Desenha o fundo (screenshot)
        painter.drawPixmap(0, 0, self.base_pixmap)
        # 2. Desenha as anotações por cima
        painter.drawPixmap(0, 0, self.annotation_pixmap)
        painter.end()

    def sizeHint(self):
        return self.base_pixmap.size()
