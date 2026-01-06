import pytest
from PySide6.QtGui import QPixmap, QColor, QPainter, QMouseEvent
from PySide6.QtCore import Qt, QPoint, QEvent
from PySide6.QtWidgets import QApplication

from linsnipper.ui.drawing_canvas import DrawingCanvas, Tool

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

def test_layered_canvas_integrity(qapp):
    """
    Test that the layered canvas keeps the base image separate from annotations.
    """
    # 1. Setup Black Background
    bg = QPixmap(100, 100)
    bg.fill(Qt.black)
    
    canvas = DrawingCanvas(pixmap=bg)
    
    # Verify Initialization
    assert not canvas.annotation_pixmap.isNull()
    img_anno = canvas.annotation_pixmap.toImage()
    # Should be fully transparent
    assert img_anno.pixelColor(50, 50).alpha() == 0

    # 2. Simulate Drawing on Annotation Layer
    # We cheat and draw directly on annotation_pixmap for testing, 
    # to simulate what mouseMoveEvent does without mocking events.
    painter = QPainter(canvas.annotation_pixmap)
    painter.setPen(Qt.red)
    painter.drawLine(0, 0, 100, 100)
    painter.end()
    
    # 3. Validation
    # A) Result should show Red line on Black BG
    res = canvas.get_result_pixmap().toImage()
    assert res.pixelColor(50, 50) == QColor(Qt.red)
    assert res.pixelColor(0, 99) == QColor(Qt.black) # Unaffected area
    
    # B) Base Pixmap should still be Black (Untouched)
    base_img = canvas.base_pixmap.toImage()
    assert base_img.pixelColor(50, 50) == QColor(Qt.black)

def test_eraser_restores_background(qapp):
    """
    Test that the eraser tool makes the annotation layer transparent,
    revealing the background.
    """
    bg = QPixmap(100, 100)
    bg.fill(Qt.blue)
    canvas = DrawingCanvas(pixmap=bg)
    
    # 1. Draw Red area on Annotation
    painter = QPainter(canvas.annotation_pixmap)
    painter.fillRect(0, 0, 100, 100, Qt.red)
    painter.end()
    
    # Check it covered the blue
    assert canvas.get_result_pixmap().toImage().pixelColor(50, 50) == QColor(Qt.red)
    
    # 2. Erase a hole in the middle
    # Simulate Eraser logic: CompMode=Clear
    painter = QPainter(canvas.annotation_pixmap)
    painter.setCompositionMode(QPainter.CompositionMode_Clear)
    painter.setBrush(Qt.black)
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(QPoint(50, 50), 10, 10)
    painter.end()
    
    # 3. Check Result
    # The hole should reveal the BLUE background
    res_img = canvas.get_result_pixmap().toImage()
    color_at_hole = res_img.pixelColor(50, 50)
    
    # Tolerance for antialiasing? It should be exact if we hit center.
    assert color_at_hole == QColor(Qt.blue)
    
    # Check outside hole is still red
    assert res_img.pixelColor(10, 10) == QColor(Qt.red)
