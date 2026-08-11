"""Consultations and the medical timeline (spec sections 15-20, 46)."""
from __future__ import annotations

from datetime import datetime

from core.database.db import execute, next_numeric_id, query_all, query_one
from core.services.appointment_service import update_status
from core.services.audit_service import log_action
from core.utils.ids import next_id


def create_consultation(data: dict, actor_user_id: str | None = None, actor_role: str | None = None) -> str:
    for field in ("patient_id", "doctor_id"):
        if not data.get(field):
            raise ValueError(f"'{field}' is required.")
    consultation_id = next_id("consultation", next_numeric_id("consultations", "consultation_id"))
    now = datetime.now().isoformat(timespec="seconds")

    weight = data.get("weight_kg")
    height = data.get("height_cm")
    bmi = None
    try:
        if weight and height:
            height_m = float(height) / 100
            bmi = round(float(weight) / (height_m ** 2), 1)
    except (TypeError, ValueError, ZeroDivisionError):
        bmi = None

    execute(
        """INSERT INTO consultations (
            consultation_id, appointment_id, patient_id, doctor_id, consultation_date, chief_complaint,
            symptoms, temperature, blood_pressure, heart_rate, respiratory_rate, oxygen_saturation,
            weight_kg, height_cm, bmi, physical_examination, diagnosis, treatment, doctor_notes,
            follow_up_date, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Completed', ?)""",
        (
            consultation_id, data.get("appointment_id"), data["patient_id"], data["doctor_id"],
            data.get("consultation_date", now[:10]), data.get("chief_complaint", ""), data.get("symptoms", ""),
            data.get("temperature"), data.get("blood_pressure", ""), data.get("heart_rate"),
            data.get("respiratory_rate"), data.get("oxygen_saturation"), weight, height, bmi,
            data.get("physical_examination", ""), data.get("diagnosis", ""), data.get("treatment", ""),
            data.get("doctor_notes", ""), data.get("follow_up_date", ""), now,
        ),
    )
    if data.get("appointment_id"):
        update_status(data["appointment_id"], "Completed", actor_user_id, actor_role)
    log_action(actor_user_id, actor_role, "Consultation Created", consultation_id,
               f"Consultation for {data['patient_id']} by {data['doctor_id']}.")
    return consultation_id


def get_consultation(consultation_id: str) -> dict | None:
    return query_one(
        """SELECT c.*, p.full_name AS patient_name, d.full_name AS doctor_name FROM consultations c
           JOIN patients p ON p.patient_id = c.patient_id
           JOIN doctors d ON d.doctor_id = c.doctor_id WHERE c.consultation_id = ?""",
        (consultation_id,),
    )


def history_for_patient(patient_id: str) -> list[dict]:
    return query_all(
        """SELECT c.*, d.full_name AS doctor_name, d.specialization FROM consultations c
           JOIN doctors d ON d.doctor_id = c.doctor_id
           WHERE c.patient_id = ? ORDER BY c.consultation_date DESC, c.created_at DESC""",
        (patient_id,),
    )


def last_consultation(patient_id: str) -> dict | None:
    rows = history_for_patient(patient_id)
    return rows[0] if rows else None


def history_for_doctor(doctor_id: str, limit: int = 200) -> list[dict]:
    return query_all(
        """SELECT c.*, p.full_name AS patient_name FROM consultations c
           JOIN patients p ON p.patient_id = c.patient_id
           WHERE c.doctor_id = ? ORDER BY c.consultation_date DESC LIMIT ?""",
        (doctor_id, limit),
    )


def previous_vitals(patient_id: str, exclude_consultation_id: str = "") -> dict | None:
    rows = [r for r in history_for_patient(patient_id) if r["consultation_id"] != exclude_consultation_id]
    return rows[0] if rows else None


# --------------------------------------------------------------- timeline

def medical_timeline(patient_id: str) -> list[dict]:
    """Merge appointments, consultations, prescriptions and lab tests
    into one chronological, clickable timeline (spec 15)."""
    events: list[dict] = []

    for row in query_all(
        """SELECT a.appointment_id AS ref_id, a.appointment_date AS event_date, d.full_name AS doctor_name,
                  a.status FROM appointments a JOIN doctors d ON d.doctor_id = a.doctor_id
           WHERE a.patient_id = ?""", (patient_id,)):
        events.append({"date": row["event_date"], "type": "Appointment", "ref_id": row["ref_id"],
                        "summary": f"Dr. {row['doctor_name']} - {row['status']}"})

    for row in history_for_patient(patient_id):
        events.append({"date": row["consultation_date"], "type": "Consultation", "ref_id": row["consultation_id"],
                        "summary": row["diagnosis"] or row["chief_complaint"] or "Consultation"})

    for row in query_all(
        """SELECT prescription_id AS ref_id, prescription_date AS event_date FROM prescriptions
           WHERE patient_id = ?""", (patient_id,)):
        items = query_all("SELECT medicine_name FROM prescription_items WHERE prescription_id = ?", (row["ref_id"],))
        summary = ", ".join(i["medicine_name"] for i in items[:2]) or "Prescription issued"
        events.append({"date": row["event_date"], "type": "Prescription", "ref_id": row["ref_id"], "summary": summary})

    for row in query_all(
        """SELECT lab_test_id AS ref_id, requested_date AS event_date, test_name, status FROM lab_tests
           WHERE patient_id = ?""", (patient_id,)):
        events.append({"date": row["event_date"], "type": "Lab Test", "ref_id": row["ref_id"],
                        "summary": f"{row['test_name']} ({row['status']})"})

    events.sort(key=lambda e: e["date"], reverse=True)
    return events
