"""Doctor management, search and scheduling (spec sections 21-25)."""
from __future__ import annotations

from datetime import datetime, timedelta

from core.database.db import execute, next_numeric_id, query_all, query_one
from core.services.audit_service import log_action
from core.services.department_service import ensure_department
from core.utils.ids import next_id

REQUIRED_FIELDS = ["full_name", "specialization"]

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def create_doctor(data: dict, actor_user_id: str | None = None, actor_role: str | None = None) -> str:
    for field in REQUIRED_FIELDS:
        if not data.get(field):
            raise ValueError(f"'{field}' is required to add a doctor.")
    department_id = data.get("department_id")
    if not department_id and data.get("department"):
        department_id = ensure_department(data["department"])
    doctor_id = next_id("doctor", next_numeric_id("doctors", "doctor_id"))
    now = datetime.now().isoformat(timespec="seconds")
    execute(
        """INSERT INTO doctors (doctor_id, full_name, gender, date_of_birth, phone, email, qualification,
              specialization, department_id, experience_years, consultation_fee, description, working_days,
              start_time, end_time, break_start, break_end, slot_duration_minutes, is_active, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)""",
        (
            doctor_id, data["full_name"], data.get("gender", ""), data.get("date_of_birth", ""),
            data.get("phone", ""), data.get("email", ""), data.get("qualification", ""),
            data["specialization"], department_id, int(data.get("experience_years", 0) or 0),
            float(data.get("consultation_fee", 0) or 0), data.get("description", ""),
            data.get("working_days", "Mon,Tue,Wed,Thu,Fri"), data.get("start_time", "09:00"),
            data.get("end_time", "17:00"), data.get("break_start", "13:00"), data.get("break_end", "14:00"),
            int(data.get("slot_duration_minutes", 15) or 15), now, now,
        ),
    )
    log_action(actor_user_id, actor_role, "Doctor Created", doctor_id, f"Added doctor {data['full_name']}.")
    return doctor_id


def update_doctor(doctor_id: str, data: dict, actor_user_id: str | None = None, actor_role: str | None = None) -> None:
    existing = get_doctor(doctor_id)
    if not existing:
        raise ValueError("Doctor not found.")
    merged = {**existing, **data}
    execute(
        """UPDATE doctors SET full_name=?, gender=?, date_of_birth=?, phone=?, email=?, qualification=?,
              specialization=?, experience_years=?, consultation_fee=?, description=?, working_days=?,
              start_time=?, end_time=?, break_start=?, break_end=?, slot_duration_minutes=?, is_active=?,
              updated_at=? WHERE doctor_id=?""",
        (
            merged["full_name"], merged["gender"], merged["date_of_birth"], merged["phone"], merged["email"],
            merged["qualification"], merged["specialization"], int(merged["experience_years"] or 0),
            float(merged["consultation_fee"] or 0), merged["description"], merged["working_days"],
            merged["start_time"], merged["end_time"], merged["break_start"], merged["break_end"],
            int(merged["slot_duration_minutes"] or 15), int(merged["is_active"]),
            datetime.now().isoformat(timespec="seconds"), doctor_id,
        ),
    )
    log_action(actor_user_id, actor_role, "Doctor Modified", doctor_id, "Doctor record updated.")


def set_active(doctor_id: str, is_active: bool, actor_user_id=None, actor_role=None) -> None:
    execute("UPDATE doctors SET is_active=?, updated_at=? WHERE doctor_id=?",
            (1 if is_active else 0, datetime.now().isoformat(timespec="seconds"), doctor_id))
    log_action(actor_user_id, actor_role, "Doctor Activated" if is_active else "Doctor Deactivated", doctor_id, "")


def get_doctor(doctor_id: str) -> dict | None:
    row = query_one(
        """SELECT d.*, dept.name AS department_name FROM doctors d
           LEFT JOIN departments dept ON dept.department_id = d.department_id
           WHERE d.doctor_id = ?""",
        (doctor_id,),
    )
    return row


def search_doctors(term: str = "", department: str = "", specialization: str = "",
                    active_only: bool = True, limit: int = 500) -> list[dict]:
    sql = """SELECT d.*, dept.name AS department_name FROM doctors d
             LEFT JOIN departments dept ON dept.department_id = d.department_id WHERE 1=1"""
    params: list = []
    if active_only:
        sql += " AND d.is_active = 1"
    if department:
        sql += " AND dept.name = ?"
        params.append(department)
    if specialization:
        sql += " AND d.specialization = ?"
        params.append(specialization)
    if term:
        sql += " AND (d.doctor_id LIKE ? OR d.full_name LIKE ? OR d.specialization LIKE ?)"
        like = f"%{term}%"
        params.extend([like, like, like])
    sql += " ORDER BY d.full_name ASC LIMIT ?"
    params.append(limit)
    return query_all(sql, tuple(params))


def list_specializations() -> list[str]:
    rows = query_all("SELECT DISTINCT specialization FROM doctors ORDER BY specialization")
    return [r["specialization"] for r in rows]


# ---------------------------------------------------------------- scheduling

def add_leave(doctor_id: str, leave_date: str, reason: str = "") -> None:
    execute("INSERT INTO doctor_leaves (doctor_id, leave_date, reason) VALUES (?, ?, ?)",
            (doctor_id, leave_date, reason))


def leaves_for_doctor(doctor_id: str) -> list[dict]:
    return query_all("SELECT * FROM doctor_leaves WHERE doctor_id = ? ORDER BY leave_date DESC", (doctor_id,))


def is_on_leave(doctor_id: str, day: str) -> bool:
    return query_one("SELECT 1 FROM doctor_leaves WHERE doctor_id = ? AND leave_date = ?", (doctor_id, day)) is not None


def available_slots(doctor_id: str, day: str) -> list[str]:
    """Return free HH:MM slots for a doctor on a given date, honouring
    working days, working hours, break time, leave and existing bookings."""
    doctor = get_doctor(doctor_id)
    if not doctor or not doctor["is_active"]:
        return []
    weekday = DAY_NAMES[datetime.strptime(day, "%Y-%m-%d").weekday()]
    working_days = [d.strip() for d in (doctor["working_days"] or "").split(",") if d.strip()]
    if working_days and weekday not in working_days:
        return []
    if is_on_leave(doctor_id, day):
        return []

    fmt = "%H:%M"
    start = datetime.strptime(doctor["start_time"] or "09:00", fmt)
    end = datetime.strptime(doctor["end_time"] or "17:00", fmt)
    break_start = datetime.strptime(doctor["break_start"], fmt) if doctor["break_start"] else None
    break_end = datetime.strptime(doctor["break_end"], fmt) if doctor["break_end"] else None
    step = timedelta(minutes=doctor["slot_duration_minutes"] or 15)

    booked_rows = query_all(
        """SELECT appointment_time FROM appointments
           WHERE doctor_id = ? AND appointment_date = ? AND status NOT IN ('Cancelled', 'NoShow')""",
        (doctor_id, day),
    )
    booked = {r["appointment_time"] for r in booked_rows}

    now = datetime.now()
    is_today = day == now.strftime("%Y-%m-%d")

    slots = []
    cursor = start
    while cursor + step <= end:
        if break_start and break_end and break_start <= cursor < break_end:
            cursor += step
            continue
        slot_str = cursor.strftime(fmt)
        if slot_str not in booked:
            if not is_today or cursor.time() > now.time():
                slots.append(slot_str)
        cursor += step
    return slots
