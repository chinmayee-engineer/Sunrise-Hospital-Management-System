"""Doctor <-> Patient messaging (spec section 30)."""
from __future__ import annotations

from datetime import datetime

from core.database.db import execute, next_numeric_id, query_all
from core.services.notification_service import create_notification
from core.utils.ids import next_id


def send_message(patient_id: str, doctor_id: str, sender: str, body: str) -> str:
    if sender not in ("patient", "doctor"):
        raise ValueError("sender must be 'patient' or 'doctor'")
    message_id = next_id("message", next_numeric_id("messages", "message_id"))
    execute(
        """INSERT INTO messages (message_id, patient_id, doctor_id, sender, body, is_read, created_at)
           VALUES (?, ?, ?, ?, ?, 0, ?)""",
        (message_id, patient_id, doctor_id, sender, body, datetime.now().isoformat(timespec="seconds")),
    )
    if sender == "patient":
        create_notification("Message", "New message from patient", body[:120], doctor_id=doctor_id)
    else:
        create_notification("Message", "New message from your doctor", body[:120], patient_id=patient_id)
    return message_id


def conversation(patient_id: str, doctor_id: str) -> list[dict]:
    return query_all(
        """SELECT * FROM messages WHERE patient_id = ? AND doctor_id = ? ORDER BY created_at ASC""",
        (patient_id, doctor_id),
    )


def conversations_for_patient(patient_id: str) -> list[dict]:
    return query_all(
        """SELECT m.doctor_id, d.full_name AS doctor_name, d.specialization,
                  MAX(m.created_at) AS last_message_at,
                  SUM(CASE WHEN m.is_read = 0 AND m.sender = 'doctor' THEN 1 ELSE 0 END) AS unread_count
           FROM messages m JOIN doctors d ON d.doctor_id = m.doctor_id
           WHERE m.patient_id = ? GROUP BY m.doctor_id ORDER BY last_message_at DESC""",
        (patient_id,),
    )


def conversations_for_doctor(doctor_id: str) -> list[dict]:
    return query_all(
        """SELECT m.patient_id, p.full_name AS patient_name,
                  MAX(m.created_at) AS last_message_at,
                  SUM(CASE WHEN m.is_read = 0 AND m.sender = 'patient' THEN 1 ELSE 0 END) AS unread_count
           FROM messages m JOIN patients p ON p.patient_id = m.patient_id
           WHERE m.doctor_id = ? GROUP BY m.patient_id ORDER BY last_message_at DESC""",
        (doctor_id,),
    )


def mark_conversation_read(patient_id: str, doctor_id: str, reader: str) -> None:
    other_sender = "doctor" if reader == "patient" else "patient"
    execute(
        "UPDATE messages SET is_read = 1 WHERE patient_id = ? AND doctor_id = ? AND sender = ?",
        (patient_id, doctor_id, other_sender),
    )
