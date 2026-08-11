"""Lab test requests, workflow status and results (spec 27)."""
from __future__ import annotations

from datetime import datetime

from core.database.db import execute, next_numeric_id, query_all, query_one
from core.services.audit_service import log_action
from core.services.notification_service import create_notification
from core.utils.ids import next_id

STATUSES = ["Requested", "Scheduled", "SampleCollected", "Processing", "Completed", "Cancelled"]
TEST_TYPES = ["Blood Test", "Urine Test", "X-Ray", "MRI", "CT Scan", "Ultrasound", "ECG", "Other"]


def request_test(data: dict, actor_user_id: str | None = None, actor_role: str | None = None) -> str:
    for field in ("patient_id", "doctor_id", "test_type", "test_name"):
        if not data.get(field):
            raise ValueError(f"'{field}' is required.")
    lab_test_id = next_id("lab_test", next_numeric_id("lab_tests", "lab_test_id"))
    now = datetime.now().isoformat(timespec="seconds")
    execute(
        """INSERT INTO lab_tests (lab_test_id, patient_id, doctor_id, consultation_id, test_type, test_name,
              requested_date, status, notes, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'Requested', ?, ?, ?)""",
        (lab_test_id, data["patient_id"], data["doctor_id"], data.get("consultation_id"), data["test_type"],
         data["test_name"], data.get("requested_date", now[:10]), data.get("notes", ""), now, now),
    )
    log_action(actor_user_id, actor_role, "Lab Test Requested", lab_test_id, data["test_name"])
    return lab_test_id


def update_status(lab_test_id: str, status: str, actor_user_id=None, actor_role=None) -> None:
    if status not in STATUSES:
        raise ValueError(f"Invalid lab status: {status}")
    execute("UPDATE lab_tests SET status=?, updated_at=? WHERE lab_test_id=?",
            (status, datetime.now().isoformat(timespec="seconds"), lab_test_id))
    log_action(actor_user_id, actor_role, "Lab Test Status Changed", lab_test_id, status)


def enter_result(lab_test_id: str, result_summary: str, result_file_path: str = "",
                  actor_user_id=None, actor_role=None) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    execute(
        """UPDATE lab_tests SET status='Completed', result_summary=?, result_file_path=?, result_date=?,
              updated_at=? WHERE lab_test_id=?""",
        (result_summary, result_file_path, now[:10], now, lab_test_id),
    )
    test = query_one("SELECT patient_id, test_name FROM lab_tests WHERE lab_test_id=?", (lab_test_id,))
    if test:
        create_notification("Lab", "Lab result available",
                             f"Results for {test['test_name']} are ready.", patient_id=test["patient_id"])
    log_action(actor_user_id, actor_role, "Lab Report Uploaded", lab_test_id, "Result entered.")


def get_test(lab_test_id: str) -> dict | None:
    return query_one(
        """SELECT lt.*, p.full_name AS patient_name, d.full_name AS doctor_name FROM lab_tests lt
           JOIN patients p ON p.patient_id = lt.patient_id
           JOIN doctors d ON d.doctor_id = lt.doctor_id WHERE lt.lab_test_id = ?""",
        (lab_test_id,),
    )


def list_for_patient(patient_id: str, completed_only: bool = False) -> list[dict]:
    sql = """SELECT lt.*, d.full_name AS doctor_name FROM lab_tests lt
             JOIN doctors d ON d.doctor_id = lt.doctor_id WHERE lt.patient_id = ?"""
    params = [patient_id]
    if completed_only:
        sql += " AND lt.status = 'Completed'"
    sql += " ORDER BY lt.requested_date DESC"
    return query_all(sql, tuple(params))


def list_all(status: str = "", term: str = "", limit: int = 500) -> list[dict]:
    sql = """SELECT lt.*, p.full_name AS patient_name, d.full_name AS doctor_name FROM lab_tests lt
             JOIN patients p ON p.patient_id = lt.patient_id
             JOIN doctors d ON d.doctor_id = lt.doctor_id WHERE 1=1"""
    params: list = []
    if status:
        sql += " AND lt.status = ?"
        params.append(status)
    if term:
        sql += " AND (lt.lab_test_id LIKE ? OR p.full_name LIKE ? OR lt.test_name LIKE ?)"
        like = f"%{term}%"
        params.extend([like, like, like])
    sql += " ORDER BY lt.requested_date DESC LIMIT ?"
    params.append(limit)
    return query_all(sql, tuple(params))
