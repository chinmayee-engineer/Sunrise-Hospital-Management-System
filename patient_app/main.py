"""Entry point for the Patient application.

Run with:  python patient_app/main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication

from core.database.db import get_connection
from core.seed.seed_data import run_seed
from core.theme import app_stylesheet
from core.utils.paths import ensure_directories
from patient_app.login_window import PatientLoginWindow


def main() -> None:
    ensure_directories()
    get_connection()
    run_seed()

    app = QApplication(sys.argv)
    app.setApplicationName("Sunrise Hospital - Patient Portal")
    app.setStyleSheet(app_stylesheet())

    login = PatientLoginWindow()
    login.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
