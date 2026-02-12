import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import passport_gui_runtime as r


class RuntimeTests(unittest.TestCase):
    def test_build_runtime_paths(self):
        with tempfile.TemporaryDirectory() as td:
            with patch.dict(os.environ, {"XDG_DATA_HOME": td}, clear=False):
                paths = r.build_runtime_paths("MyApp")
                self.assertTrue(paths.base_dir.exists())
                self.assertEqual(paths.base_dir, Path(td) / "MyApp")
                self.assertEqual(paths.history_file.name, ".passport_gui_history.json")

    def test_logger_writes_file(self):
        with tempfile.TemporaryDirectory() as td:
            log_path = Path(td) / "app.log"
            logger = r.setup_rotating_logger(log_path, "tlogger")
            logger.info("hello")
            self.assertTrue(log_path.exists())
            self.assertIn("hello", log_path.read_text(encoding="utf-8"))

    def test_ensure_frozen_dependencies_non_frozen(self):
        with patch("passport_gui_runtime.sys", wraps=r.sys) as mocked_sys:
            mocked_sys.frozen = False
            self.assertIsNone(r.ensure_frozen_dependencies())


if __name__ == "__main__":
    unittest.main()
