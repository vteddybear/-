from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
import os
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


APP_NAME = "PassportGUI"


@dataclass(frozen=True)
class RuntimePaths:
    base_dir: Path
    history_file: Path
    project_dirs_file: Path
    report_log_file: Path
    tech_log_file: Path


def _windows_local_appdata() -> Optional[Path]:
    value = os.environ.get("LOCALAPPDATA")
    return Path(value) if value else None


def _windows_appdata() -> Optional[Path]:
    value = os.environ.get("APPDATA")
    return Path(value) if value else None


def get_app_data_dir(app_name: str = APP_NAME) -> Path:
    """Return a user-writable app data directory for source and frozen runs."""
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


def build_runtime_paths(app_name: str = APP_NAME) -> RuntimePaths:
    base_dir = get_app_data_dir(app_name)
    base_dir.mkdir(parents=True, exist_ok=True)
    return RuntimePaths(
        base_dir=base_dir,
        history_file=base_dir / ".passport_gui_history.json",
        project_dirs_file=base_dir / ".passport_project_dirs.json",
        report_log_file=base_dir / ".passport_report_log.csv",
        tech_log_file=base_dir / "app.log",
    )


def setup_rotating_logger(log_path: Path, logger_name: str = "passport_gui") -> logging.Logger:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def ensure_frozen_dependencies() -> Optional[str]:
    """Return human-readable error if frozen executable misses bundled deps."""
    if not getattr(sys, "frozen", False):
        return None

    missing: list[str] = []
    try:
        import docxtpl  # noqa: F401
    except Exception:
        missing.append("docxtpl")

    try:
        import pypdf  # noqa: F401
    except Exception:
        missing.append("pypdf")

    try:
        import docx2pdf  # noqa: F401
    except Exception:
        missing.append("docx2pdf")

    if not missing:
        return None

    return (
        "В сборке отсутствуют зависимости: "
        + ", ".join(missing)
        + ". Пересоберите .exe и добавьте hidden-import для этих модулей."
    )


def docx2pdf_is_available() -> bool:
    """Best-effort availability check for DOCX->PDF conversion in runtime."""
    try:
        from docx2pdf import convert  # noqa: F401
    except Exception:
        return False
    return True
