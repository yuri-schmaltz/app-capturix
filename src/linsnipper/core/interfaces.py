from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from PySide6.QtCore import QRect
from PySide6.QtGui import QPixmap


class BaseCaptureBackend(ABC):
    """Interface para backends de captura de tela."""

    name: str = "base"

    @abstractmethod
    def capture_fullscreen(self) -> QPixmap:
        """Captura todos os monitores disponíveis."""

    @abstractmethod
    def capture_region(self, rect: QRect) -> QPixmap:
        """Recorta região de uma captura (normalmente a partir de um fullscreen)."""

    @abstractmethod
    def capture_window(self, window_id: Optional[int] = None) -> QPixmap:
        """Captura uma janela específica, se suportado."""
