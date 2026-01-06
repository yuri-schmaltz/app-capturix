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
        screens = QGuiApplication.screens()
        if not screens:
            logger.error("Nenhuma tela detectada.")
            raise CaptureError("Não foi possível detectar telas.")

        # 1. Calcular a geometria total (união de todas as telas)
        total_rect = QRect()
        for screen in screens:
            total_rect = total_rect.united(screen.geometry())

        if total_rect.isNull():
            raise CaptureError("Geometria total das telas é inválida.")

        # 2. Criar o pixmap gigante ("Canvas Virtual")
        full_pixmap = QPixmap(total_rect.size())
        full_pixmap.fill(Qt.black)  # Fundo padrão caso haja buracos

        # 3. Pintar cada tela na posição correta
        # Precisamos de um Painter para compor
        from PySide6.QtGui import QPainter
        from PySide6.QtCore import QPoint

        painter = QPainter(full_pixmap)
        
        # O total_rect pode começar em coordenadas negativas (ex: tela secundária à esquerda)
        # Precisamos transladar tudo para (0,0) do pixmap
        offset_x = -total_rect.x()
        offset_y = -total_rect.y()

        for screen in screens:
            # Captura a tela individual
            screen_pix = screen.grabWindow(0)
            geom = screen.geometry()
            
            # Posição no canvas virtual
            target_x = geom.x() + offset_x
            target_y = geom.y() + offset_y
            
            painter.drawPixmap(target_x, target_y, screen_pix)

        painter.end()

        # Nota: O CapturaService/Backend pode precisar expor o offset 
        # se quisermos mapear de volta para coordenadas globais, 
        # mas para 'Screenshot' simples, perder a coordenada absoluta global geralmente é OK,
        # desde que a imagem relativa esteja certa.
        
        return full_pixmap

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
