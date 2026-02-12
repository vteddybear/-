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
                paths = r.build_runtime_paths("MyApp", migrate_legacy=False)
                self.assertTrue(paths.base_dir.exists())
                self.assertEqual(paths.base_dir, Path(td) / "MyApp")
                self.assertEqual(paths.history_file.name, ".passport_gui_history.json")

    def test_env_override_for_app_dir(self):
        with tempfile.TemporaryDirectory() as td:
            with patch.dict(os.environ, {r.APP_DIR_ENV: td}, clear=False):
                self.assertEqual(r.get_app_data_dir("IgnoredName"), Path(td))

    def test_windows_prefers_localappdata(self):
        with tempfile.TemporaryDirectory() as td:
            with patch("passport_gui_runtime.platform.system", return_value="Windows"):
                with patch.dict(os.environ, {"LOCALAPPDATA": td}, clear=False):
                    self.assertEqual(r.get_app_data_dir("App"), Path(td) / "App")

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

    def test_docx2pdf_available_bool(self):
        self.assertIsInstance(r.docx2pdf_is_available(), bool)


if __name__ == "__main__":
    unittest.main()
