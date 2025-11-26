from __future__ import annotations

import logging
import os
import sys
import tempfile
from pathlib import Path
from unittest import TestCase, mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from linsnipper.config import AppConfig
from linsnipper.logging_config import setup_logging


class SetupLoggingTests(TestCase):
    def test_log_file_contains_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_root = Path(tmpdir) / "cache"

            with mock.patch.dict(os.environ, {"XDG_CACHE_HOME": str(cache_root)}):
                config = AppConfig(screenshots_dir=str(Path(tmpdir) / "shots"), log_level="INFO")
                setup_logging(config)
                logging.info("Test message")
                logging.shutdown()

            log_file = cache_root / "linsnipper" / "linsnipper.log"
            self.assertTrue(log_file.exists())

            lines = log_file.read_text(encoding="utf-8").splitlines()
            self.assertGreater(len(lines), 0)
            self.assertRegex(
                lines[0],
                r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \[INFO\] .+ - Test message$",
            )
