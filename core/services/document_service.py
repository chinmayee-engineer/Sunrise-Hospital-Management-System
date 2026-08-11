"""Medical document upload/store/categorize (spec 28)."""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from core.database.db import execute, next_numeric_id, query_all, query_one
from core.services.audit_service import log_action
from core.utils.ids import next_id
from core.utils.paths import DOCUMENTS_DIR

DOCUMENT_TYPES = ["Prescription", "X-Ray", "Scan", "Lab Report", "Medical Certificate",
                   "Discharge Summary", "Insurance Document", "Other"]

_TYPE_FOLDER = {
    "X-Ray": "scans", "Scan": "scans", "Lab Report": "lab_reports",
    "Prescription": "prescriptions", "Medical Certificate": "certificates",
    "Discharge Summary": "certificates", "Insurance Document": "other", "Other": "other",
}


def upload_document(patient_id: str, document_type: str, title: str, source_file_path: str,
                     uploaded_by: str | None = None, actor_role: str | None = None) -> str:
    document_id = next_id("document", next_numeric_id("medical_documents", "document_id"))
    folder = DOCUMENTS_DIR / _TYPE_FOLDER.get(document_type, "other")
    folder.mkdir(parents=True, exist_ok=True)
    source = Path(source_file_path)
    destination = folder / f"{document_id}_{source.name}"
    shutil.copy2(source, destination)
    now = datetime.now().isoformat(timespec="seconds")
    execute(
        """INSERT INTO medical_documents (document_id, patient_id, uploaded_by, document_type, title,
              file_path, is_archived, uploaded_at) VALUES (?, ?, ?, ?, ?, ?, 0, ?)""",
        (document_id, patient_id, uploaded_by, document_type, title, str(destination), now),
    )
    log_action(uploaded_by, actor_role, "Document Uploaded", document_id, f"{document_type}: {title}")
    return document_id


def list_for_patient(patient_id: str, include_archived: bool = False) -> list[dict]:
    sql = "SELECT * FROM medical_documents WHERE patient_id = ?"
    params = [patient_id]
    if not include_archived:
        sql += " AND is_archived = 0"
    sql += " ORDER BY uploaded_at DESC"
    return query_all(sql, tuple(params))


def archive_document(document_id: str) -> None:
    execute("UPDATE medical_documents SET is_archived=1 WHERE document_id=?", (document_id,))


def get_document(document_id: str) -> dict | None:
    return query_one("SELECT * FROM medical_documents WHERE document_id = ?", (document_id,))
