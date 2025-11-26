from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path

from .config import AppConfig


def _log_dir() -> Path:
    cache_dir = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    d = cache_dir / "linsnipper"
    d.mkdir(parents=True, exist_ok=True)
    return d


def setup_logging(config: AppConfig, log_to_console: bool = False) -> None:
    log_dir = _log_dir()
    log_file = log_dir / "linsnipper.log"

    level = getattr(logging, config.log_level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)

    # Limpa handlers antigos pra evitar duplicação
    root.handlers.clear()

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%(Y)s-%(m)s-%(d)s %(H)s:%(M)s:%(S)s",
    )

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    if log_to_console:
        console = logging.StreamHandler()
        console.setFormatter(fmt)
        root.addHandler(console)

    logging.getLogger(__name__).debug("Logging configurado. Arquivo: %s", log_file)
