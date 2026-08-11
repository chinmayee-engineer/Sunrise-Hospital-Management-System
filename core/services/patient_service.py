"""Patient registration, search, profile and duplicate protection
(spec sections 10-14, 40)."""
from __future__ import annotations

from datetime import datetime

from core.database.db import execute, next_numeric_id, query_all, query_one
from core.services.audit_service import log_action
from core.utils.ids import next_id

REQUIRED_FIELDS = ["full_name", "date_of_birth", "gender", "phone"]


def find_possible_duplicates(phone: str, email: str, full_name: str, date_of_birth: str) -> list[dict]:
    """Return existing patients that look like the same person, so the
    UI can warn before silently creating a duplicate (spec 13)."""
    candidates: dict[str, dict] = {}
    if phone:
        for row in query_all("SELECT * FROM patients WHERE phone = ?", (phone,)):
            candidates[row["patient_id"]] = row
    if email:
        for row in query_all("SELECT * FROM patients WHERE email = ? AND email != ''", (email,)):
            candidates[row["patient_id"]] = row
    if full_name and date_of_birth:
        for row in query_all(
            "SELECT * FROM patients WHERE LOWER(full_name) = LOWER(?) AND date_of_birth = ?",
            (full_name, date_of_birth),
        ):
            candidates[row["patient_id"]] = row
    return list(candidates.values())


def create_patient(data: dict, actor_user_id: str | None = None, actor_role: str | None = None) -> str:
    for field in REQUIRED_FIELDS:
        if not data.get(field):
            raise ValueError(f"'{field}' is required to create a patient.")
    patient_id = next_id("patient", next_numeric_id("patients", "patient_id"))
    now = datetime.now().isoformat(timespec="seconds")
    execute(
        """INSERT INTO patients (
            patient_id, full_name, date_of_birth, gender, blood_group, phone, email, address, city, state,
            pin_code, emergency_contact_name, emergency_relationship, emergency_phone, allergies,
            existing_conditions, previous_surgeries, chronic_conditions, medical_history, important_notes,
            status, registration_date, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Active', ?, ?, ?)""",
        (
            patient_id, data["full_name"], data["date_of_birth"], data["gender"], data.get("blood_group", ""),
            data["phone"], data.get("email", ""), data.get("address", ""), data.get("city", ""),
            data.get("state", ""), data.get("pin_code", ""), data.get("emergency_contact_name", ""),
            data.get("emergency_relationship", ""), data.get("emergency_phone", ""), data.get("allergies", ""),
            data.get("existing_conditions", ""), data.get("previous_surgeries", ""),
            data.get("chronic_conditions", ""), data.get("medical_history", ""), data.get("important_notes", ""),
            data.get("registration_date", now[:10]), now, now,
        ),
    )
    log_action(actor_user_id, actor_role, "Patient Created", patient_id, f"Registered patient {data['full_name']}.")
    return patient_id


def update_patient(patient_id: str, data: dict, actor_user_id: str | None = None, actor_role: str | None = None) -> None:
    existing = get_patient(patient_id)
    if not existing:
        raise ValueError("Patient not found.")
    merged = {**existing, **data}
    execute(
        """UPDATE patients SET full_name=?, date_of_birth=?, gender=?, blood_group=?, phone=?, email=?,
              address=?, city=?, state=?, pin_code=?, emergency_contact_name=?, emergency_relationship=?,
              emergency_phone=?, allergies=?, existing_conditions=?, previous_surgeries=?, chronic_conditions=?,
              medical_history=?, important_notes=?, status=?, updated_at=? WHERE patient_id=?""",
        (
            merged["full_name"], merged["date_of_birth"], merged["gender"], merged["blood_group"],
            merged["phone"], merged["email"], merged["address"], merged["city"], merged["state"],
            merged["pin_code"], merged["emergency_contact_name"], merged["emergency_relationship"],
            merged["emergency_phone"], merged["allergies"], merged["existing_conditions"],
            merged["previous_surgeries"], merged["chronic_conditions"], merged["medical_history"],
            merged["important_notes"], merged["status"], datetime.now().isoformat(timespec="seconds"), patient_id,
        ),
    )
    log_action(actor_user_id, actor_role, "Patient Modified", patient_id, "Patient record updated.")


def archive_patient(patient_id: str, actor_user_id: str | None = None, actor_role: str | None = None) -> None:
    execute("UPDATE patients SET status='Archived', updated_at=? WHERE patient_id=?",
            (datetime.now().isoformat(timespec="seconds"), patient_id))
    log_action(actor_user_id, actor_role, "Patient Archived", patient_id, "")


def get_patient(patient_id: str) -> dict | None:
    return query_one("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))


def log_patient_viewed(patient_id: str, actor_user_id: str | None, actor_role: str | None) -> None:
    log_action(actor_user_id, actor_role, "Patient Record Viewed", patient_id, "")


def search_patients(term: str = "", status: str = "", limit: int = 500) -> list[dict]:
    sql = "SELECT * FROM patients WHERE 1=1"
    params: list = []
    if status:
        sql += " AND status = ?"
        params.append(status)
    if term:
        sql += " AND (patient_id LIKE ? OR full_name LIKE ? OR phone LIKE ? OR email LIKE ?)"
        like = f"%{term}%"
        params.extend([like, like, like, like])
    sql += " ORDER BY full_name ASC LIMIT ?"
    params.append(limit)
    return query_all(sql, tuple(params))


def calculate_age(date_of_birth: str) -> int:
    try:
        birth = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return 0
    today = datetime.now().date()
    return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
