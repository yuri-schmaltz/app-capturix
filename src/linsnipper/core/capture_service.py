from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from PySide6.QtCore import QEventLoop, QRect, QTimer

from .models import CaptureRequest, CaptureResult, CaptureMode
from .interfaces import BaseCaptureBackend
from ..errors import CaptureError

logger = logging.getLogger(__name__)


class CaptureService:
    def __init__(self, backend: BaseCaptureBackend):
        self.backend = backend

    def perform_capture(
        self,
        request: CaptureRequest,
        selection_rect: Optional[QRect] = None,
        *,
        before_capture=None,
        on_finished=None,
        on_error=None,
    ) -> Optional[CaptureResult]:
        """
        selection_rect: normalmente vem do overlay (retângulo selecionado).
        Em modo FULLSCREEN, é ignorado.

        Para integrações com UI, use ``on_finished``/``on_error`` para executar de
        forma assíncrona (a captura real será disparada por um ``QTimer`` após o
        delay configurado em ``request``).
        """
        logger.debug("Iniciando captura: %s", request)

        def _run_capture():
            try:
                return self._execute_capture(request, selection_rect, before_capture)
            except CaptureError as exc:
                logger.exception("Falha na captura (erro conhecido).")
                raise
            except Exception as exc:  # pragma: no cover - proteção extra
                logger.exception("Erro inesperado ao capturar.")
                raise CaptureError(f"Erro inesperado na captura: {exc}") from exc

        def _capture_and_handle():
            try:
                result = _run_capture()
            except CaptureError as exc:
                if on_error:
                    on_error(exc)
                else:
                    raise
                return
            if on_finished:
                on_finished(result)
            return result

        delay_ms = max(0, int(request.delay_seconds * 1000))

        if on_finished or on_error:
            QTimer.singleShot(delay_ms, _capture_and_handle)
            return None

        if delay_ms:
            loop = QEventLoop()
            outcome: dict[str, CaptureResult | Exception] = {}

            def _sync_capture():
                try:
                    outcome["result"] = _run_capture()
                except Exception as exc:  # capture_error já normalizado
                    outcome["error"] = exc
                finally:
                    loop.quit()

            QTimer.singleShot(delay_ms, _sync_capture)
            loop.exec()

            if "error" in outcome:
                raise outcome["error"]
            return outcome.get("result")

        return _run_capture()

    def _execute_capture(
        self,
        request: CaptureRequest,
        selection_rect: Optional[QRect],
        before_capture,
    ) -> CaptureResult:
        if before_capture is not None:
            before_capture()

        mode = request.mode

        if mode == CaptureMode.FULLSCREEN:
            pix = self.backend.capture_fullscreen()
        elif mode in (CaptureMode.RECTANGLE, CaptureMode.FREEFORM):
            rect = request.region or selection_rect
            if rect is None:
                raise CaptureError("Nenhuma região fornecida para captura de área.")
            pix = self.backend.capture_region(rect)
        elif mode == CaptureMode.WINDOW:
            pix = self.backend.capture_window(request.window_id)
        else:
            raise CaptureError(f"Modo de captura não suportado: {mode}")

        return CaptureResult(
            pixmap=pix,
            mode=mode,
            created_at=datetime.now(),
            backend_name=self.backend.name,
        )

    def _apply_mask(self, pixmap: QPixmap, mask_path: QPainterPath) -> QPixmap:
        """Aplica uma máscara vetorial ao pixmap, preservando transparência."""

        result = QPixmap(pixmap.size())
        result.fill(Qt.transparent)

        painter = QPainter(result)
        painter.setClipPath(mask_path)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()

        return result

    def _validate_masked_capture(self, pixmap: QPixmap, mask_path: QPainterPath) -> bool:
        """
        Confirma que pixels fora do traçado permanecem transparentes.

        Essa verificação é leve e visa detectar regressões ao aplicar máscaras
        não-retangulares na captura.
        """

        mask_image = QImage(pixmap.size(), QImage.Format_RGBA8888)
        mask_image.fill(0)

        painter = QPainter(mask_image)
        painter.fillPath(mask_path, Qt.white)
        painter.end()

        image = pixmap.toImage().convertToFormat(QImage.Format_RGBA8888)
        width = image.width()
        height = image.height()

        for y in range(height):
            for x in range(width):
                mask_alpha = mask_image.pixelColor(x, y).alpha()
                pixel_alpha = image.pixelColor(x, y).alpha()
                if mask_alpha == 0 and pixel_alpha != 0:
                    logger.warning(
                        "Pixels fora da máscara não ficaram transparentes (x=%s, y=%s).",
                        x,
                        y,
                    )
                    return False

        logger.debug("Validação de máscara concluída com sucesso.")
        return True
