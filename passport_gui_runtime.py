from __future__ import annotations

import importlib
import logging
from logging.handlers import RotatingFileHandler
import os
import platform
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


APP_NAME = "PassportGUI"
APP_DIR_ENV = "PASSPORT_GUI_APP_DIR"


@dataclass(frozen=True)
class RuntimePaths:
    base_dir: Path
    history_file: Path
    project_dirs_file: Path
    report_log_file: Path
    tech_log_file: Path


LEGACY_FILENAMES = {
    "history_file": ".passport_gui_history.json",
    "project_dirs_file": ".passport_project_dirs.json",
    "report_log_file": ".passport_report_log.csv",
}


def _windows_local_appdata() -> Optional[Path]:
    value = os.environ.get("LOCALAPPDATA")
    return Path(value) if value else None


def _windows_appdata() -> Optional[Path]:
    value = os.environ.get("APPDATA")
    return Path(value) if value else None


def get_app_data_dir(app_name: str = APP_NAME) -> Path:
    """Return a user-writable app data directory for source and frozen runs."""
    override = os.environ.get(APP_DIR_ENV)
    if override:
        return Path(override)

    system = platform.system().lower()

    if system == "windows":
        base = _windows_local_appdata() or _windows_appdata()
        if base:
            return base / app_name

    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / app_name

    home = Path.home()
    if system == "darwin":
        return home / "Library" / "Application Support" / app_name

    return home / ".local" / "share" / app_name


def _maybe_migrate_legacy_files(base_dir: Path) -> None:
    """Move old runtime files from cwd into base_dir if target files do not exist yet."""
    cwd = Path.cwd()
    for filename in LEGACY_FILENAMES.values():
        src = cwd / filename
        dst = base_dir / filename
        if src.exists() and not dst.exists() and src.is_file():
            try:
                shutil.move(str(src), str(dst))
            except Exception:
                # Non-fatal migration: runtime should continue even if moving fails.
                pass


def build_runtime_paths(app_name: str = APP_NAME, migrate_legacy: bool = True) -> RuntimePaths:
    base_dir = get_app_data_dir(app_name)
    base_dir.mkdir(parents=True, exist_ok=True)

    if migrate_legacy:
        _maybe_migrate_legacy_files(base_dir)

    return RuntimePaths(
        base_dir=base_dir,
        history_file=base_dir / LEGACY_FILENAMES["history_file"],
        project_dirs_file=base_dir / LEGACY_FILENAMES["project_dirs_file"],
        report_log_file=base_dir / LEGACY_FILENAMES["report_log_file"],
        tech_log_file=base_dir / "app.log",
    )


def setup_rotating_logger(log_path: Path, logger_name: str = "passport_gui") -> logging.Logger:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Keep only one rotating file handler for the target path to avoid duplicates.
    for handler in list(logger.handlers):
        if isinstance(handler, RotatingFileHandler):
            same_file = Path(getattr(handler, "baseFilename", "")).resolve() == log_path.resolve()
            if same_file:
                logger.removeHandler(handler)
                handler.close()

    handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def _check_importable_modules(modules: Iterable[str]) -> list[str]:
    missing: list[str] = []
    for module_name in modules:
        try:
            importlib.import_module(module_name)
        except Exception:
            missing.append(module_name)
    return missing


def ensure_frozen_dependencies(modules: Iterable[str] = ("docxtpl", "pypdf", "docx2pdf")) -> Optional[str]:
    """Return human-readable error if frozen executable misses bundled deps."""
    if not getattr(sys, "frozen", False):
        return None

    missing = _check_importable_modules(modules)
    if not missing:
        return None

    return (
        "В сборке отсутствуют зависимости: "
        + ", ".join(missing)
        + ". Пересоберите .exe и добавьте hidden-import для этих модулей."
    )


def docx2pdf_is_available() -> bool:
    """Best-effort availability check for DOCX->PDF conversion in runtime."""
    return not _check_importable_modules(("docx2pdf",))
