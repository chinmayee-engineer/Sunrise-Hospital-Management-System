"""Manual/automatic backup and restore (spec 39)."""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from core.database.db import close_connection, execute, next_numeric_id, query_all
from core.services.audit_service import log_action
from core.utils.ids import next_id
from core.utils.paths import BACKUPS_DIR, DATABASE_PATH


def create_backup(notes: str = "", actor_user_id: str | None = None, actor_role: str | None = None) -> str:
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    backup_id = next_id("backup", next_numeric_id("backups", "backup_id"))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destination = BACKUPS_DIR / f"hospital_backup_{timestamp}.db"
    shutil.copy2(DATABASE_PATH, destination)
    execute(
        "INSERT INTO backups (backup_id, file_path, created_at, created_by, notes) VALUES (?, ?, ?, ?, ?)",
        (backup_id, str(destination), datetime.now().isoformat(timespec="seconds"), actor_user_id, notes),
    )
    log_action(actor_user_id, actor_role, "Backup Created", backup_id, str(destination))
    return backup_id


def list_backups() -> list[dict]:
    return query_all("SELECT * FROM backups ORDER BY created_at DESC")


def restore_backup(file_path: str, actor_user_id: str | None = None, actor_role: str | None = None) -> None:
    """Restore requires confirmation in the UI *before* calling this --
    it overwrites the live database and cannot be undone."""
    source = Path(file_path)
    if not source.exists():
        raise ValueError("Backup file not found.")
    close_connection()
    shutil.copy2(source, DATABASE_PATH)
    log_action(actor_user_id, actor_role, "Backup Restored", file_path, "Database restored from backup.")
