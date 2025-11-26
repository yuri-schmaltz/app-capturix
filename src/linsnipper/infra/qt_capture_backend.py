from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtGui import QGuiApplication, QPixmap
from PySide6.QtCore import QRect

from ..core.interfaces import BaseCaptureBackend
from ..errors import CaptureError

logger = logging.getLogger(__name__)


class QtCaptureBackend(BaseCaptureBackend):
    name = "qt"

    def _primary_screen(self):
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            logger.error("Nenhuma tela primária detectada.")
            raise CaptureError("Não foi possível detectar a tela para captura.")
        return screen

    def capture_fullscreen(self) -> QPixmap:
        screen = self._primary_screen()
        pixmap = screen.grabWindow(0)
        if pixmap.isNull():
            logger.error("QScreen.grabWindow(0) retornou pixmap nulo.")
            raise CaptureError("Falha ao capturar tela cheia.")
        return pixmap

    def capture_region(self, rect: QRect) -> QPixmap:
        if rect.isNull() or rect.width() <= 0 or rect.height() <= 0:
            raise CaptureError("Retângulo de captura inválido.")

        full = self.capture_fullscreen()
        bounded = rect.intersected(full.rect())
        if bounded.isNull():
            logger.warning("Retângulo de captura não intersecta com a tela.")
            raise CaptureError("Área selecionada está fora da tela.")
        return full.copy(bounded)

    def capture_window(self, window_id: Optional[int] = None) -> QPixmap:
        # Implementação básica: usa fullscreen e a UI recorta a janela.
        # Futuro: integração com X11 (xwininfo) ou Wayland portal.
        logger.debug("capture_window chamado com window_id=%s (modo simples).", window_id)
        return self.capture_fullscreen()
