from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication

from .config import AppConfig
from .logging_config import setup_logging
from .infra.qt_capture_backend import QtCaptureBackend
from .core.capture_service import CaptureService
from .core.models import CaptureMode
from .errors import LinSnipperError
from .ui.editor_window import EditorWindow
from .ui.snip_overlay import SnipOverlay


logger = logging.getLogger(__name__)


def _create_qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setApplicationName("LinSnipper")
    app.setOrganizationName("LinSnipperProject")
    return app


def _create_capture_service(config: AppConfig) -> CaptureService:
    # Futuro: escolher backend com base em config.capture_backend e ambiente
    backend = QtCaptureBackend()
    return CaptureService(backend)


def run_app(log_to_console: bool = False):
    config = AppConfig.load()
    setup_logging(config, log_to_console=log_to_console)

    logger.info("Iniciando LinSnipper em modo editor.")

    app = _create_qapp()
    service = _create_capture_service(config)

    win = EditorWindow(config=config, capture_service=service)
    win.show()

    try:
        sys.exit(app.exec())
    except LinSnipperError as exc:
        logger.exception("Erro de aplicação: %s", exc)
        sys.exit(1)


def run_snip_mode(initial_mode: CaptureMode, delay: int, log_to_console: bool = False):
    config = AppConfig.load()
    setup_logging(config, log_to_console=log_to_console)

    logger.info(
        "Iniciando LinSnipper em modo snip. mode=%s delay=%s",
        initial_mode,
        delay,
    )

    app = _create_qapp()
    service = _create_capture_service(config)

    overlay = SnipOverlay(
        config=config,
        capture_service=service,
        initial_mode=initial_mode,
        delay=delay,
    )

    def on_snip_finished(result_pixmap):
        if result_pixmap is None:
            logger.info("Captura cancelada pelo usuário.")
            app.quit()
            return
        editor = EditorWindow(config=config, capture_service=service, initial_pixmap=result_pixmap)
        editor.show()

    overlay.snip_finished.connect(on_snip_finished)
    overlay.show()

    try:
        sys.exit(app.exec())
    except LinSnipperError as exc:
        logger.exception("Erro de aplicação: %s", exc)
        sys.exit(1)
