from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication

from .config import AppConfig
from .logging_config import setup_logging
from .infra.qt_capture_backend import QtCaptureBackend
from .core.capture_service import CaptureService
from .core.models import CaptureMode
from .core.single_instance import SingleInstance, send_message_to_instance
from .errors import LinSnipperError
from .ui.editor_window import EditorWindow
from .ui.snip_overlay import SnipOverlay
from .ui.tray import TrayIcon

logger = logging.getLogger(__name__)


class LinSnipperController:
    """
    Central controller for the resident application.
    Manages: Tray Icon, IPC Server, Windows (Overlay/Editor).
    """
    def __init__(self, app: QApplication, config: AppConfig):
        self.app = app
        self.config = config
        self.capture_service = self._create_capture_service()
        
        # UI Components
        self.tray = None
        self.overlay = None
        self.editor = None
        
        # IPC
        self.ipc_server = SingleInstance()
        self.ipc_server.message_received.connect(self._on_ipc_message)

    def _create_capture_service(self) -> CaptureService:
        backend = QtCaptureBackend()
        return CaptureService(backend)

    def start(self):
        """Starts the background service (Tray + IPC)."""
        # Try to start IPC server
        if not self.ipc_server.start():
            logger.error("Falha ao iniciar servidor IPC. Outra instância pode estar travada.")
            # We could choose to exit or run anyway. For now, assume single instance enforcement via client check.
        
        # Create Tray
        self.tray = TrayIcon(self.app)
        self.tray.request_snip.connect(lambda: self.start_snip(CaptureMode.RECT, 0))
        self.tray.request_editor.connect(self.open_editor)
        self.tray.request_quit.connect(self.quit)
        
        # Keep application alive even if windows close
        self.app.setQuitOnLastWindowClosed(False)
        logger.info("LinSnipper Background Service iniciado.")

    def _on_ipc_message(self, message: str):
        logger.info(f"IPC Message Received: {message}")
        cmd, *args = message.split(":")
        
        if cmd == "SNIP":
            self.start_snip(CaptureMode.RECT, 0) # Default for shortuct
        elif cmd == "EDITOR":
            self.open_editor()
        elif cmd == "QUIT":
            self.quit()

    def start_snip(self, mode: CaptureMode, delay: int):
        if self.overlay:
            self.overlay.close()
            
        self.overlay = SnipOverlay(
            config=self.config,
            capture_service=self.capture_service,
            initial_mode=mode,
            delay=delay,
        )
        self.overlay.snip_finished.connect(self._on_snip_finished)
        self.overlay.show()

    def _on_snip_finished(self, result_pixmap):
        if result_pixmap is None:
            logger.info("Captura cancelada.")
            return

        # Open Editor with result
        self.open_editor(result_pixmap)

    def open_editor(self, pixmap=None):
        # If we want multiple editors, we can just instantiate new ones.
        # For a simple app, maybe single editor window? Let's allow multiple for now or just one.
        # Current pattern: Create new window.
        self.editor = EditorWindow(config=self.config, capture_service=self.capture_service, initial_pixmap=pixmap)
        self.editor.show()
        self.editor.activateWindow()
        self.editor.raise_()

    def quit(self):
        self.app.quit()


def _create_qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setApplicationName("LinSnipper")
    app.setOrganizationName("LinSnipperProject")
    return app


def run_app_background():
    """Main Entry Point for the Daemon/Tray mode."""
    # 1. Check if instance running
    if send_message_to_instance("linsnipper_ipc", "EDITOR"):
        print("LinSnipper já está rodando. Abrindo editor...")
        sys.exit(0)

    # 2. Start new instance
    config = AppConfig.load()
    setup_logging(config, log_to_console=False)
    
    app = _create_qapp()
    controller = LinSnipperController(app, config)
    controller.start()
    
    sys.exit(app.exec())


def run_snip_mode(initial_mode: CaptureMode, delay: int, log_to_console: bool = False):
    """
    Entry point for CLI --snip.
    If background service exists -> Send Trigger.
    If not -> Run standalone snip (one-off) OR start background service? 
    Let's keep one-off behavior for --snip if no daemon, to be consistent with scripts.
    OR we can make it auto-start the daemon.
    
    Decision: "linsnipper --snip" should be fast.
    - If daemon running -> IPC Trigger
    - If not -> One-off capture (legacy behavior)
    """
    
    # 1. Try IPC
    if send_message_to_instance("linsnipper_ipc", "SNIP"):
        logger.info("Comando enviado para instância em background.")
        sys.exit(0)

    # 2. Fallback: Standalone Snipping (Old behavior)
    # Copied logic from old run_snip_mode, but minimized
    config = AppConfig.load()
    setup_logging(config, log_to_console=log_to_console)
    logger.info("Modo Standalone: Snip")

    app = _create_qapp()
    backend = QtCaptureBackend()
    service = CaptureService(backend)

    overlay = SnipOverlay(config, service, initial_mode, delay)
    
    def on_finished(pix):
        if pix:
            editor = EditorWindow(config, service, initial_pixmap=pix)
            editor.show()
        else:
            app.quit()
            
    overlay.snip_finished.connect(on_finished)
    overlay.show()
    
    sys.exit(app.exec())


def run_app(log_to_console: bool = False):
    """
    Entry point for CLI (no args) -> Editor Mode.
    Now acts as "Launcher" for the Background Service.
    """
    run_app_background()
