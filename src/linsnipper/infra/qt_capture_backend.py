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
        # Em Linux moderno (Wayland) e até X11, grabWindow(id) é instável ou proibido.
        # Melhor falhar explicitamente do que retornar screenshot da tela toda enganosamente.
        msg = "Captura de janela (Window Mode) não é suportada nativamente pelo backend Qt neste ambiente."
        logger.warning(msg)
        raise NotImplementedError(msg)
