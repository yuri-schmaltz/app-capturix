from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional
from datetime import datetime

from PySide6.QtCore import QRect
from PySide6.QtGui import QPixmap


class CaptureMode(Enum):
    RECTANGLE = auto()
    FREEFORM = auto()
    WINDOW = auto()
    FULLSCREEN = auto()


@dataclass
class CaptureRequest:
    mode: CaptureMode
    delay_seconds: int = 0
    region: Optional[QRect] = None
    window_id: Optional[int] = None


@dataclass
class CaptureResult:
    pixmap: QPixmap
    mode: CaptureMode
    created_at: datetime
    backend_name: str
