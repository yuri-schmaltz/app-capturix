from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Literal

from .errors import ConfigError


CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "linsnipper"
CONFIG_FILE = CONFIG_DIR / "config.json"

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
Theme = Literal["system", "light", "dark"]
BackendChoice = Literal["auto", "qt"]  # futuro: "portal", etc.


@dataclass
class AppConfig:
    screenshots_dir: str
    default_delay: int = 0
    theme: Theme = "system"
    log_level: LogLevel = "INFO"
    capture_backend: BackendChoice = "auto"

    @classmethod
    def default(cls) -> "AppConfig":  # type: ignore[name-defined]
        pictures = Path.home() / "Pictures"
        default_dir = pictures / "Screenshots"
        return cls(
            screenshots_dir=str(default_dir),
            default_delay=0,
            theme="system",
            log_level="INFO",
            capture_backend="auto",
        )

    @classmethod
    def load(cls) -> "AppConfig":  # type: ignore[name-defined]
        if not CONFIG_FILE.exists():
            return cls.default()

        try:
            with CONFIG_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            raise ConfigError(f"Falha ao ler {CONFIG_FILE}: {exc}") from exc

        base = cls.default()
        for field_name in asdict(base).keys():
            if field_name in data:
                setattr(base, field_name, data[field_name])
        return base

    def save(self) -> None:
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with CONFIG_FILE.open("w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=2)
        except Exception as exc:
            raise ConfigError(f"Falha ao salvar config em {CONFIG_FILE}: {exc}") from exc

    @property
    def screenshots_path(self) -> Path:
        path = Path(self.screenshots_dir).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        return path
