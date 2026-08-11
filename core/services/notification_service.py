"""In-app notifications (spec section 31)."""
from __future__ import annotations

from datetime import datetime

from core.database.db import execute, next_numeric_id, query_all
from core.utils.ids import next_id


def create_notification(category: str, title: str, body: str = "",
                         user_id: str | None = None, patient_id: str | None = None,
                         doctor_id: str | None = None) -> str:
    notification_id = next_id("notification", next_numeric_id("notifications", "notification_id"))
    execute(
        """INSERT INTO notifications (notification_id, user_id, patient_id, doctor_id, category, title, body,
              is_read, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)""",
        (notification_id, user_id, patient_id, doctor_id, category, title, body,
         datetime.now().isoformat(timespec="seconds")),
    )
    return notification_id


def for_patient(patient_id: str, unread_only: bool = False, limit: int = 100) -> list[dict]:
    sql = "SELECT * FROM notifications WHERE patient_id = ?"
    params: list = [patient_id]
    if unread_only:
        sql += " AND is_read = 0"
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    return query_all(sql, tuple(params))


def for_doctor(doctor_id: str, unread_only: bool = False, limit: int = 100) -> list[dict]:
    sql = "SELECT * FROM notifications WHERE doctor_id = ?"
    params: list = [doctor_id]
    if unread_only:
        sql += " AND is_read = 0"
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    return query_all(sql, tuple(params))


def unread_count_patient(patient_id: str) -> int:
    return len(for_patient(patient_id, unread_only=True))


def unread_count_doctor(doctor_id: str) -> int:
    return len(for_doctor(doctor_id, unread_only=True))


def mark_read(notification_id: str) -> None:
    execute("UPDATE notifications SET is_read = 1 WHERE notification_id = ?", (notification_id,))


def mark_all_read_patient(patient_id: str) -> None:
    execute("UPDATE notifications SET is_read = 1 WHERE patient_id = ?", (patient_id,))


def mark_all_read_doctor(doctor_id: str) -> None:
    execute("UPDATE notifications SET is_read = 1 WHERE doctor_id = ?", (doctor_id,))
