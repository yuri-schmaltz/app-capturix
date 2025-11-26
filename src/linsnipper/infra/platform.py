from __future__ import annotations

import os
from enum import Enum


class SessionType(Enum):
    X11 = "x11"
    WAYLAND = "wayland"
    UNKNOWN = "unknown"


def detect_session_type() -> SessionType:
    t = os.environ.get("XDG_SESSION_TYPE", "").lower()
    if t == "wayland":
        return SessionType.WAYLAND
    if t == "x11":
        return SessionType.X11
    return SessionType.UNKNOWN


def is_wayland() -> bool:
    return detect_session_type() == SessionType.WAYLAND
