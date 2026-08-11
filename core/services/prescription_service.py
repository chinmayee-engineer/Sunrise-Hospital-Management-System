"""Digital prescriptions with multiple medicine line items (spec 26)."""
from __future__ import annotations

from datetime import datetime

from core.database.db import execute, next_numeric_id, query_all, query_one, transaction
from core.services.audit_service import log_action
from core.services.notification_service import create_notification
from core.utils.ids import next_id


def create_prescription(data: dict, medicines: list[dict], actor_user_id: str | None = None,
                         actor_role: str | None = None) -> str:
    for field in ("patient_id", "doctor_id"):
        if not data.get(field):
            raise ValueError(f"'{field}' is required.")
    if not medicines:
        raise ValueError("A prescription needs at least one medicine.")

    prescription_id = next_id("prescription", next_numeric_id("prescriptions", "prescription_id"))
    now = datetime.now().isoformat(timespec="seconds")
    with transaction() as cursor:
        cursor.execute(
            """INSERT INTO prescriptions (prescription_id, consultation_id, patient_id, doctor_id,
                  prescription_date, diagnosis, symptoms, instructions, follow_up_date, notes, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                prescription_id, data.get("consultation_id"), data["patient_id"], data["doctor_id"],
                data.get("prescription_date", now[:10]), data.get("diagnosis", ""), data.get("symptoms", ""),
                data.get("instructions", ""), data.get("follow_up_date", ""), data.get("notes", ""), now,
            ),
        )
        for medicine in medicines:
            cursor.execute(
                """INSERT INTO prescription_items (prescription_id, medicine_name, dosage, frequency, duration,
                      before_after_food, instructions) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    prescription_id, medicine["medicine_name"], medicine.get("dosage", ""),
                    medicine.get("frequency", ""), medicine.get("duration", ""),
                    medicine.get("before_after_food", ""), medicine.get("instructions", ""),
                ),
            )
    create_notification("Prescription", "New prescription issued",
                         f"Prescription {prescription_id} is now available.", patient_id=data["patient_id"])
    log_action(actor_user_id, actor_role, "Prescription Created", prescription_id,
               f"{len(medicines)} medicine(s) for {data['patient_id']}.")
    return prescription_id


def get_prescription(prescription_id: str) -> dict | None:
    header = query_one(
        """SELECT rx.*, p.full_name AS patient_name, d.full_name AS doctor_name, d.qualification,
                  d.specialization FROM prescriptions rx
           JOIN patients p ON p.patient_id = rx.patient_id
           JOIN doctors d ON d.doctor_id = rx.doctor_id WHERE rx.prescription_id = ?""",
        (prescription_id,),
    )
    if not header:
        return None
    header = dict(header)
    header["items"] = query_all("SELECT * FROM prescription_items WHERE prescription_id = ?", (prescription_id,))
    return header


def list_for_patient(patient_id: str) -> list[dict]:
    return query_all(
        """SELECT rx.*, d.full_name AS doctor_name FROM prescriptions rx
           JOIN doctors d ON d.doctor_id = rx.doctor_id
           WHERE rx.patient_id = ? ORDER BY rx.prescription_date DESC""",
        (patient_id,),
    )


def list_for_doctor(doctor_id: str, limit: int = 200) -> list[dict]:
    return query_all(
        """SELECT rx.*, p.full_name AS patient_name FROM prescriptions rx
           JOIN patients p ON p.patient_id = rx.patient_id
           WHERE rx.doctor_id = ? ORDER BY rx.prescription_date DESC LIMIT ?""",
        (doctor_id, limit),
    )
