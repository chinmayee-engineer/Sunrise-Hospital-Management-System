"""
Central, application-relative path resolution.

All paths in the system are derived from the project root so the
application keeps working after being copied/moved to another
Windows computer, and after being packaged into a standalone .exe
(PyInstaller sets sys._MEIPASS / uses the executable's folder).

Never hardcode absolute, user-specific, or machine-specific paths
anywhere else in the codebase -- always import from here.
"""
from __future__ import annotations

import sys
from pathlib import Path


def get_project_root() -> Path:
    """Return the root folder of the project (folder that contains
    core/, hospital_app/, patient_app/, data/, ...).

    Works both when running from source and when frozen with
    PyInstaller (in which case data folders live next to the .exe,
    not inside the temporary _MEIPASS extraction folder).
    """
    if getattr(sys, "frozen", False):
        # Running as a bundled .exe -> use the folder containing the exe
        return Path(sys.executable).resolve().parent
    # Running from source: core/utils/paths.py -> project root is 2 up
    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = get_project_root()

DATA_DIR = PROJECT_ROOT / "data"
DOCUMENTS_DIR = PROJECT_ROOT / "documents"
REPORTS_DIR = PROJECT_ROOT / "reports"
BACKUPS_DIR = PROJECT_ROOT / "backups"
EXPORTS_DIR = PROJECT_ROOT / "exports"
LOGS_DIR = PROJECT_ROOT / "logs"
RESOURCES_DIR = PROJECT_ROOT / "resources"

DATABASE_PATH = DATA_DIR / "hospital.db"


def ensure_directories() -> None:
    """Create every directory the application needs on first run."""
    for directory in (
        DATA_DIR,
        DOCUMENTS_DIR,
        REPORTS_DIR,
        BACKUPS_DIR,
        EXPORTS_DIR,
        LOGS_DIR,
        RESOURCES_DIR,
        DOCUMENTS_DIR / "prescriptions",
        DOCUMENTS_DIR / "lab_reports",
        DOCUMENTS_DIR / "scans",
        DOCUMENTS_DIR / "certificates",
        DOCUMENTS_DIR / "other",
        REPORTS_DIR / "invoices",
        REPORTS_DIR / "receipts",
        REPORTS_DIR / "summaries",
    ):
        directory.mkdir(parents=True, exist_ok=True)
