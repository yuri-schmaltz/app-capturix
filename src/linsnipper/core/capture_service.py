from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Optional

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QImage, QPainter, QPainterPath, QPixmap

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
        selection_mask: Optional[QPainterPath] = None,
    ) -> CaptureResult:
        """
        selection_rect: normalmente vem do overlay (retângulo selecionado).
        Em modo FULLSCREEN, é ignorado.
        """
        logger.debug("Iniciando captura: %s", request)

        if request.delay_seconds > 0:
            logger.debug("Aguardando delay de %s segundos.", request.delay_seconds)
            time.sleep(request.delay_seconds)

        mode = request.mode

        try:
            if mode == CaptureMode.FULLSCREEN:
                pix = self.backend.capture_fullscreen()
            elif mode in (CaptureMode.RECTANGLE, CaptureMode.FREEFORM):
                rect = request.region or selection_rect
                if rect is None:
                    raise CaptureError("Nenhuma região fornecida para captura de área.")
                mask = request.mask_path or selection_mask
                pix = self.backend.capture_region(rect)
                if mask is not None and not mask.isEmpty():
                    local_mask = mask.translated(-rect.topLeft())
                    pix = self._apply_mask(pix, local_mask)
                    self._validate_masked_capture(pix, local_mask)
            elif mode == CaptureMode.WINDOW:
                pix = self.backend.capture_window(request.window_id)
            else:
                raise CaptureError(f"Modo de captura não suportado: {mode}")
        except CaptureError:
            logger.exception("Falha na captura (erro conhecido).")
            raise
        except Exception as exc:
            logger.exception("Erro inesperado ao capturar.")
            raise CaptureError(f"Erro inesperado na captura: {exc}") from exc

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
