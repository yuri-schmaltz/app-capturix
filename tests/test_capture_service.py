import os
import os
import time
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import QEventLoop
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QPixmap

    from linsnipper.core.capture_service import CaptureService
    from linsnipper.core.interfaces import BaseCaptureBackend
    from linsnipper.core.models import CaptureMode, CaptureRequest
    from linsnipper.errors import CaptureError

    QT_AVAILABLE = True
except ImportError as exc:  # pragma: no cover - ambiente sem dependências gráficas
    QT_AVAILABLE = False
    QT_IMPORT_ERROR = exc


if QT_AVAILABLE:

    class _FakeBackend(BaseCaptureBackend):
        name = "fake"

        def __init__(self):
            self.calls = []

        def _pixmap(self):
            return QPixmap(2, 2)

        def capture_fullscreen(self):
            self.calls.append(("fullscreen", None))
            return self._pixmap()

        def capture_region(self, rect):
            self.calls.append(("region", rect))
            return self._pixmap()

        def capture_window(self, window_id=None):
            self.calls.append(("window", window_id))
            return self._pixmap()


    class TestCaptureServiceTimer(unittest.TestCase):
        def setUp(self):
            self.app = QApplication.instance() or QApplication([])
            self.backend = _FakeBackend()
            self.service = CaptureService(self.backend)

        def test_capture_runs_after_delay_with_event_loop(self):
            request = CaptureRequest(mode=CaptureMode.FULLSCREEN, delay_seconds=0.1)
            loop = QEventLoop()
            durations = []

            start = time.monotonic()

            def _on_finished(result):
                durations.append(time.monotonic() - start)
                loop.quit()

            self.service.perform_capture(request, on_finished=_on_finished)
            loop.exec()

            self.assertGreaterEqual(durations[0], 0.09)
            self.assertEqual(self.backend.calls, [("fullscreen", None)])

        def test_before_capture_runs_prior_to_backend(self):
            request = CaptureRequest(mode=CaptureMode.FULLSCREEN, delay_seconds=0)
            loop = QEventLoop()
            order = []

            def _before():
                order.append("before")

            def _on_finished(_result):
                order.append("capture")
                loop.quit()

            self.service.perform_capture(
                request,
                before_capture=_before,
                on_finished=_on_finished,
            )
            loop.exec()

            self.assertEqual(order, ["before", "capture"])

        def test_window_mode_wraps_not_implemented_error(self):
            """Test that CaptureService catches NotImplementedError and raises CaptureError."""
            
            # Monkey-patch backend to Simulate real backend behavior
            def _raise(*args, **kwargs):
                raise NotImplementedError("Not supported")
            
            self.backend.capture_window = _raise
            
            request = CaptureRequest(mode=CaptureMode.WINDOW, delay_seconds=0)
            
            # Use perform_capture synchronous via direct call? 
            # perform_capture returns result if delay=0 AND no callbacks?
            # Check implementation:
            # if delay_ms=0 and no callbacks -> _run_capture() -> returns result.
            
            with self.assertRaises(CaptureError):
                self.service.perform_capture(request)
else:

    class TestCaptureServiceTimer(unittest.TestCase):
        def test_qt_unavailable(self):
            self.skipTest("Qt/PySide6 indisponível no ambiente de teste")


if __name__ == "__main__":
    unittest.main()
