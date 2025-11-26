from __future__ import annotations

import logging
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow,
    QToolBar,
    QAction,
    QFileDialog,
    QMessageBox,
    QStatusBar,
    QWidget,
    QHBoxLayout,
)
from PySide6.QtGui import QKeySequence, QGuiApplication
from PySide6.QtCore import Qt

from ..config import AppConfig
from ..core.capture_service import CaptureService
from .drawing_canvas import DrawingCanvas, Tool

logger = logging.getLogger(__name__)


class EditorWindow(QMainWindow):
    """
    Janela de edição da captura:
      - Mostra o DrawingCanvas
      - Toolbar com caneta, marcador, borracha
      - Undo/Redo (delegado ao canvas)
      - Salvar / Salvar como
      - Copiar para área de transferência
    """

    def __init__(
        self,
        config: AppConfig,
        capture_service: CaptureService,
        initial_pixmap=None,
        parent=None,
    ):
        super().__init__(parent)
        self.config = config
        self.capture_service = capture_service

        self.setWindowTitle("LinSnipper - Editor")
        self.resize(900, 700)

        # Canvas central
        self.canvas = DrawingCanvas(pixmap=initial_pixmap)
        central = QWidget(self)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.setCentralWidget(central)

        self._create_toolbar()
        self.setStatusBar(QStatusBar(self))

    # ------------- Toolbar -------------

    def _create_toolbar(self):
        toolbar = QToolBar("Ferramentas", self)
        toolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        # Ferramentas de desenho
        act_pen = QAction("Caneta", self)
        act_pen.triggered.connect(lambda: self._set_tool(Tool.PEN))
        toolbar.addAction(act_pen)

        act_high = QAction("Marcador", self)
        act_high.triggered.connect(lambda: self._set_tool(Tool.HIGHLIGHTER))
        toolbar.addAction(act_high)

        act_eraser = QAction("Borracha", self)
        act_eraser.triggered.connect(lambda: self._set_tool(Tool.ERASER))
        toolbar.addAction(act_eraser)

        toolbar.addSeparator()

        # Copiar e salvar
        act_copy = QAction("Copiar", self)
        act_copy.setShortcut(QKeySequence.Copy)
        act_copy.triggered.connect(self._copy_to_clipboard)
        toolbar.addAction(act_copy)

        act_save = QAction("Salvar", self)
        act_save.setShortcut(QKeySequence.Save)
        act_save.triggered.connect(self._save)
        toolbar.addAction(act_save)

        act_saveas = QAction("Salvar como…", self)
        act_saveas.triggered.connect(self._save_as)
        toolbar.addAction(act_saveas)

        toolbar.addSeparator()

        # Undo / Redo
        act_undo = QAction("Desfazer", self)
        act_undo.setShortcut(QKeySequence.Undo)
        act_undo.triggered.connect(self._undo)
        toolbar.addAction(act_undo)

        act_redo = QAction("Refazer", self)
        act_redo.setShortcut(QKeySequence.Redo)
        act_redo.triggered.connect(self._redo)
        toolbar.addAction(act_redo)

    # ------------- Ações -------------

    def _set_tool(self, tool: Tool):
        self.canvas.set_tool(tool)
        self.statusBar().showMessage(f"Ferramenta: {tool.name}", 2000)

    def _copy_to_clipboard(self):
        pixmap = self.canvas.get_result_pixmap()
        QGuiApplication.clipboard().setPixmap(pixmap)
        self.statusBar().showMessage("Copiado para a área de transferência", 2000)

    def _default_filename(self) -> str:
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return f"Screenshot_{stamp}.png"

    def _save(self):
        """Salva direto na pasta padrão configurada (config.screenshots_path)."""
        target_dir = self.config.screenshots_path
        filename = target_dir / self._default_filename()
        pixmap = self.canvas.get_result_pixmap()

        if not pixmap.save(str(filename)):
            logger.error("Falha ao salvar imagem em %s", filename)
            QMessageBox.warning(self, "Erro", "Falha ao salvar imagem.")
        else:
            logger.info("Imagem salva em %s", filename)
            self.statusBar().showMessage(f"Salvo em {filename}", 5000)

    def _save_as(self):
        """Diálogo de 'Salvar como...', permitindo mudar pasta e formato."""
        start_path = self.config.screenshots_path / self._default_filename()
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar captura",
            str(start_path),
            "Imagens (*.png *.jpg *.jpeg)",
        )
        if not filename:
            return

        pixmap = self.canvas.get_result_pixmap()
        if not pixmap.save(filename):
            logger.error("Falha ao salvar imagem em %s", filename)
            QMessageBox.warning(self, "Erro", "Falha ao salvar imagem.")
        else:
            logger.info("Imagem salva em %s", filename)
            self.statusBar().showMessage(f"Salvo em {filename}", 5000)

    def _undo(self):
        self.canvas.undo()

    def _redo(self):
        self.canvas.redo()
