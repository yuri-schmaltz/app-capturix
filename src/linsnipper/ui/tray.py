from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QObject, Signal

class TrayIcon(QObject):
    """
    Manages the System Tray Icon.
    Signals:
        request_snip: User clicked "Snip Now" or activated tray.
        request_editor: User clicked "Open Editor".
        request_quit: User clicked "Quit".
    """
    request_snip = Signal()
    request_editor = Signal()
    request_quit = Signal()

    request_quit = Signal()

    def __init__(self, app=None):
        super().__init__()
        self.tray = QSystemTrayIcon(app)
        
        # Load local icon
        import os
        current_dir = os.path.dirname(__file__)
        icon_path = os.path.join(current_dir, "assets", "icon.png")
        
        if os.path.exists(icon_path):
            self.tray.setIcon(QIcon(icon_path))
        else:
            # Fallback
            self.tray.setIcon(QIcon.fromTheme("camera-photo"))
        
        self._setup_menu()
        self.tray.activated.connect(self._on_activated)
        self.tray.show()

    def _setup_menu(self):
        menu = QMenu()
        
        action_snip = QAction("Snip Now", self)
        action_snip.triggered.connect(self.request_snip.emit)
        menu.addAction(action_snip)
        
        action_editor = QAction("Open Editor", self)
        action_editor.triggered.connect(self.request_editor.emit)
        menu.addAction(action_editor)
        
        menu.addSeparator()
        
        action_quit = QAction("Quit", self)
        action_quit.triggered.connect(self.request_quit.emit)
        menu.addAction(action_quit)
        
        self.tray.setContextMenu(menu)

    def _on_activated(self, reason):
        # On click (Trigger), trigger snip by default
        if reason == QSystemTrayIcon.Trigger:
            self.request_snip.emit()
