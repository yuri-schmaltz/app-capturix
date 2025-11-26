from __future__ import annotations

import logging
from typing import List

from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QVBoxLayout, QMessageBox
from PySide6.QtCore import Qt, QRect, QPoint, Signal
from PySide6.QtGui import QPainter, QColor, QPixmap, QGuiApplication, QPainterPath

from ..config import AppConfig
from ..core.models import CaptureMode, CaptureRequest
from ..core.capture_service import CaptureService
from ..errors import CaptureError

logger = logging.getLogger(__name__)


class SnipOverlay(QWidget):
    """
    Overlay de captura ao estilo Win+Shift+S:
      - Tela escurecida
      - Barra de modos no topo
      - Seleção retangular / livre / janela
      - Integra com CaptureService (delay, backend, logging, erros)
    """

    # Emite o QPixmap final ou None se usuário cancelar/erro
    snip_finished = Signal(object)

    def __init__(
        self,
        config: AppConfig,
        capture_service: CaptureService,
        initial_mode: CaptureMode,
        delay: int = 0,
        parent=None,
    ):
        super().__init__(parent)
        self.config = config
        self.capture_service = capture_service
        self.current_mode: CaptureMode = initial_mode
        self.delay = delay

        self.setWindowFlags(
            Qt.WindowStaysOnTopHint
            | Qt.FramelessWindowHint
            | Qt.Tool
        )
        self.setWindowState(Qt.WindowFullScreen)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._dragging = False
        self._start_pos = QPoint()
        self._end_pos = QPoint()
        self._freeform_points: List[QPoint] = []

        self.full_screenshot: QPixmap = self._try_capture_preview()

        self._build_ui()

    # ------------- Setup -------------

    def _build_ui(self):
        bar = QWidget(self)
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(8, 8, 8, 8)
        bar_layout.setSpacing(4)

        btn_rect = QPushButton("Retângulo", bar)
        btn_rect.clicked.connect(lambda: self._set_mode(CaptureMode.RECTANGLE))

        btn_free = QPushButton("Livre", bar)
        btn_free.clicked.connect(lambda: self._set_mode(CaptureMode.FREEFORM))

        btn_win = QPushButton("Janela", bar)
        btn_win.clicked.connect(lambda: self._set_mode(CaptureMode.WINDOW))

        btn_full = QPushButton("Tela cheia", bar)
        btn_full.clicked.connect(self._capture_fullscreen)

        btn_cancel = QPushButton("Cancelar", bar)
        btn_cancel.clicked.connect(self._cancel)

        for b in (btn_rect, btn_free, btn_win, btn_full, btn_cancel):
            bar_layout.addWidget(b)

        bar.setFixedHeight(48)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(bar)
        layout.addStretch()

        self._bar = bar

    def _set_mode(self, mode: CaptureMode):
        self.current_mode = mode

    def _cancel(self):
        self.snip_finished.emit(None)
        self.close()

    def _try_capture_preview(self) -> QPixmap:
        """
        Captura uma screenshot para servir de fundo do overlay.
        Se falhar, retorna um pixmap vazio e avisa o usuário,
        mas ainda permite tentar a captura real depois.
        """
        try:
            pix = self.capture_service.backend.capture_fullscreen()
            if pix.isNull():
                raise CaptureError("Pixmap nulo na captura de pré-visualização.")
            return pix
        except CaptureError as exc:
            logger.exception("Falha ao capturar pré-visualização de tela.")
            QMessageBox.warning(
                self,
                "Pré-visualização indisponível",
                "Não foi possível gerar a pré-visualização da tela.\n"
                "A captura em si ainda será tentada.\n\n"
                f"Detalhes: {exc}",
            )
            return QPixmap()

    # ------------- Captura usando o serviço -------------

    def _capture_fullscreen(self):
        request = CaptureRequest(
            mode=CaptureMode.FULLSCREEN,
            delay_seconds=self.delay,
        )
        self._perform_capture(request, selection_rect=None, selection_mask=None)

    def _perform_capture(
        self,
        request: CaptureRequest,
        selection_rect: QRect | None,
        selection_mask: QPainterPath | None,
    ):
        """
        Esconde o overlay, roda a captura via CaptureService e devolve o QPixmap.
        """
        # Esconde overlay antes da captura real pra não sair no screenshot
        self.hide()
        QGuiApplication.processEvents()

        try:
            result = self.capture_service.perform_capture(
                request,
                selection_rect=selection_rect,
                selection_mask=selection_mask,
            )
        except CaptureError as exc:
            logger.exception("Falha na captura: %s", exc)
            QMessageBox.critical(
                self,
                "Erro de captura",
                f"Falha ao capturar a tela.\n\nDetalhes: {exc}",
            )
            self.snip_finished.emit(None)
            self.close()
            return

        self.snip_finished.emit(result.pixmap)
        self.close()

    # ------------- Eventos de mouse -------------

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._start_pos = event.pos()
            self._end_pos = event.pos()
            if self.current_mode == CaptureMode.FREEFORM:
                self._freeform_points = [event.pos()]
            self.update()

    def mouseMoveEvent(self, event):
        if not (self._dragging and (event.buttons() & Qt.LeftButton)):
            return
        self._end_pos = event.pos()
        if self.current_mode == CaptureMode.FREEFORM:
            self._freeform_points.append(event.pos())
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton or not self._dragging:
            return

        self._dragging = False

        if self.current_mode in (CaptureMode.RECTANGLE, CaptureMode.FREEFORM, CaptureMode.WINDOW):
            selection_path = self._build_selection_path()
            if selection_path is None:
                self.snip_finished.emit(None)
                self.close()
                return

            selection_rect = selection_path.boundingRect().toAlignedRect()

            mode = self.current_mode
            # Por enquanto, tratamos WINDOW como retângulo; mais pra frente
            # dá pra integrar com APIs de janela específicas.
            if mode == CaptureMode.WINDOW:
                mode = CaptureMode.RECTANGLE

            request = CaptureRequest(
                mode=mode,
                delay_seconds=self.delay,
                mask_path=selection_path,
            )
            self._perform_capture(
                request,
                selection_rect=selection_rect,
                selection_mask=selection_path,
            )

    def _build_selection_path(self, allow_open: bool = False) -> QPainterPath | None:
        if self.current_mode in (CaptureMode.RECTANGLE, CaptureMode.WINDOW):
            rect = QRect(self._start_pos, self._end_pos).normalized()
            if rect.isNull() or rect.width() <= 0 or rect.height() <= 0:
                return None
            path = QPainterPath()
            path.addRect(rect)
            return path

        if self.current_mode == CaptureMode.FREEFORM:
            if len(self._freeform_points) < 2:
                return None

            path = QPainterPath()
            path.moveTo(self._freeform_points[0])
            for point in self._freeform_points[1:]:
                path.lineTo(point)

            if len(self._freeform_points) > 2:
                path.closeSubpath()

            if allow_open:
                return path

            if len(self._freeform_points) < 3:
                return None

            path.closeSubpath()
            bounds = path.boundingRect()
            if bounds.isNull() or bounds.width() <= 0 or bounds.height() <= 0:
                return None

            return path

        return None

    # ------------- Renderização -------------

    def paintEvent(self, event):
        painter = QPainter(self)

        # Fundo: screenshot, se existir
        if not self.full_screenshot.isNull():
            painter.drawPixmap(self.rect(), self.full_screenshot)

        # Escurece tudo
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))

        # Desenha área de seleção, se houver
        if self._dragging or (not self._start_pos.isNull() and not self._end_pos.isNull()):
            selection_path = self._build_selection_path(allow_open=True)

            if selection_path and not selection_path.isEmpty():
                painter.setCompositionMode(QPainter.CompositionMode_Clear)
                painter.fillPath(selection_path, QColor(0, 0, 0, 0))
                painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                painter.setPen(QColor(0, 120, 215))
                painter.drawPath(selection_path)

            elif self.current_mode == CaptureMode.FREEFORM and self._freeform_points:
                painter.setPen(QColor(0, 120, 215))
                for i in range(1, len(self._freeform_points)):
                    painter.drawLine(
                        self._freeform_points[i - 1],
                        self._freeform_points[i],
                    )

        painter.end()
