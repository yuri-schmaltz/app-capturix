from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Optional

from PySide6.QtCore import QRect

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
                pix = self.backend.capture_region(rect)
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
