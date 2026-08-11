"""Appointment booking, rescheduling, cancellation and the token/queue
system (spec sections 8-9)."""
from __future__ import annotations

from datetime import datetime

from core.database.db import execute, next_numeric_id, query_all, query_one
from core.services.audit_service import log_action
from core.services.doctor_service import available_slots
from core.services.notification_service import create_notification
from core.utils.ids import next_id


def _next_token(doctor_id: str, day: str) -> int:
    row = query_one(
        "SELECT MAX(token_number) AS mx FROM appointments WHERE doctor_id = ? AND appointment_date = ?",
        (doctor_id, day),
    )
    return (row["mx"] or 0) + 1 if row else 1


def book_appointment(patient_id: str, doctor_id: str, day: str, time_str: str, reason: str = "",
                      actor_user_id: str | None = None, actor_role: str | None = None) -> str:
    if time_str not in available_slots(doctor_id, day):
        raise ValueError("That slot is no longer available. Please choose another time.")
    existing = query_one(
        """SELECT appointment_id FROM appointments WHERE doctor_id=? AND appointment_date=? AND appointment_time=?
           AND status NOT IN ('Cancelled','NoShow')""",
        (doctor_id, day, time_str),
    )
    if existing:
        raise ValueError("This slot was just booked by someone else. Please choose another time.")

    appointment_id = next_id("appointment", next_numeric_id("appointments", "appointment_id"))
    token = _next_token(doctor_id, day)
    now = datetime.now().isoformat(timespec="seconds")
    execute(
        """INSERT INTO appointments (appointment_id, patient_id, doctor_id, appointment_date, appointment_time,
              reason, status, token_number, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, 'Scheduled', ?, ?, ?)""",
        (appointment_id, patient_id, doctor_id, day, time_str, reason, token, now, now),
    )
    doctor = query_one("SELECT full_name FROM doctors WHERE doctor_id=?", (doctor_id,))
    create_notification("Appointment", "Appointment confirmed",
                         f"Your appointment with Dr. {doctor['full_name']} on {day} at {time_str} "
                         f"(Token {token}) is confirmed.", patient_id=patient_id)
    create_notification("Appointment", "New appointment booked",
                         f"New booking on {day} at {time_str}, token {token}.", doctor_id=doctor_id)
    log_action(actor_user_id, actor_role, "Appointment Created", appointment_id,
               f"Booked {day} {time_str} with {doctor_id}.")
    return appointment_id


def reschedule_appointment(appointment_id: str, new_day: str, new_time: str,
                            actor_user_id: str | None = None, actor_role: str | None = None) -> None:
    appt = get_appointment(appointment_id)
    if not appt:
        raise ValueError("Appointment not found.")
    if appt["status"] in ("Completed", "Cancelled"):
        raise ValueError(f"Cannot reschedule a {appt['status'].lower()} appointment.")
    if new_time not in available_slots(appt["doctor_id"], new_day):
        raise ValueError("That slot is not available. Please choose another time.")
    token = _next_token(appt["doctor_id"], new_day)
    execute(
        """UPDATE appointments SET appointment_date=?, appointment_time=?, token_number=?, status='Scheduled',
              updated_at=? WHERE appointment_id=?""",
        (new_day, new_time, token, datetime.now().isoformat(timespec="seconds"), appointment_id),
    )
    create_notification("Appointment", "Appointment rescheduled",
                         f"Your appointment is now on {new_day} at {new_time} (Token {token}).",
                         patient_id=appt["patient_id"])
    log_action(actor_user_id, actor_role, "Appointment Rescheduled", appointment_id, f"-> {new_day} {new_time}")


def cancel_appointment(appointment_id: str, reason: str = "", actor_user_id: str | None = None,
                        actor_role: str | None = None) -> None:
    appt = get_appointment(appointment_id)
    if not appt:
        raise ValueError("Appointment not found.")
    execute("UPDATE appointments SET status='Cancelled', updated_at=? WHERE appointment_id=?",
            (datetime.now().isoformat(timespec="seconds"), appointment_id))
    create_notification("Appointment", "Appointment cancelled", reason or "Your appointment was cancelled.",
                         patient_id=appt["patient_id"])
    create_notification("Appointment", "Appointment cancelled",
                         f"Appointment {appointment_id} was cancelled.", doctor_id=appt["doctor_id"])
    log_action(actor_user_id, actor_role, "Appointment Cancelled", appointment_id, reason)


def update_status(appointment_id: str, status: str, actor_user_id=None, actor_role=None) -> None:
    valid = {"Scheduled", "CheckedIn", "InConsultation", "Completed", "Cancelled", "NoShow"}
    if status not in valid:
        raise ValueError(f"Invalid status: {status}")
    execute("UPDATE appointments SET status=?, updated_at=? WHERE appointment_id=?",
            (status, datetime.now().isoformat(timespec="seconds"), appointment_id))
    log_action(actor_user_id, actor_role, "Appointment Status Changed", appointment_id, status)


def get_appointment(appointment_id: str) -> dict | None:
    return query_one(
        """SELECT a.*, p.full_name AS patient_name, d.full_name AS doctor_name, d.specialization
           FROM appointments a
           JOIN patients p ON p.patient_id = a.patient_id
           JOIN doctors d ON d.doctor_id = a.doctor_id
           WHERE a.appointment_id = ?""",
        (appointment_id,),
    )


def list_for_patient(patient_id: str, upcoming_only: bool = False) -> list[dict]:
    sql = """SELECT a.*, d.full_name AS doctor_name, d.specialization FROM appointments a
             JOIN doctors d ON d.doctor_id = a.doctor_id WHERE a.patient_id = ?"""
    params = [patient_id]
    if upcoming_only:
        sql += " AND a.status IN ('Scheduled','CheckedIn') AND a.appointment_date >= date('now')"
    sql += " ORDER BY a.appointment_date DESC, a.appointment_time DESC"
    return query_all(sql, tuple(params))


def list_for_doctor(doctor_id: str, day: str | None = None) -> list[dict]:
    sql = """SELECT a.*, p.full_name AS patient_name, p.phone AS patient_phone FROM appointments a
             JOIN patients p ON p.patient_id = a.patient_id WHERE a.doctor_id = ?"""
    params = [doctor_id]
    if day:
        sql += " AND a.appointment_date = ?"
        params.append(day)
    sql += " ORDER BY a.appointment_date DESC, a.appointment_time ASC"
    return query_all(sql, tuple(params))


def list_all(day: str = "", status: str = "", term: str = "", limit: int = 500) -> list[dict]:
    sql = """SELECT a.*, p.full_name AS patient_name, d.full_name AS doctor_name FROM appointments a
             JOIN patients p ON p.patient_id = a.patient_id
             JOIN doctors d ON d.doctor_id = a.doctor_id WHERE 1=1"""
    params: list = []
    if day:
        sql += " AND a.appointment_date = ?"
        params.append(day)
    if status:
        sql += " AND a.status = ?"
        params.append(status)
    if term:
        sql += """ AND (a.appointment_id LIKE ? OR p.full_name LIKE ? OR d.full_name LIKE ?)"""
        like = f"%{term}%"
        params.extend([like, like, like])
    sql += " ORDER BY a.appointment_date DESC, a.appointment_time DESC LIMIT ?"
    params.append(limit)
    return query_all(sql, tuple(params))


# ------------------------------------------------------------------- queue

def queue_for_doctor(doctor_id: str, day: str | None = None) -> list[dict]:
    day = day or datetime.now().strftime("%Y-%m-%d")
    return query_all(
        """SELECT a.*, p.full_name AS patient_name FROM appointments a
           JOIN patients p ON p.patient_id = a.patient_id
           WHERE a.doctor_id = ? AND a.appointment_date = ? AND a.status != 'Cancelled'
           ORDER BY a.token_number ASC""",
        (doctor_id, day),
    )


def current_token(doctor_id: str, day: str | None = None) -> int | None:
    day = day or datetime.now().strftime("%Y-%m-%d")
    row = query_one(
        """SELECT token_number FROM appointments WHERE doctor_id=? AND appointment_date=?
           AND status = 'InConsultation' ORDER BY token_number ASC LIMIT 1""",
        (doctor_id, day),
    )
    return row["token_number"] if row else None


def call_next(doctor_id: str, day: str | None = None, actor_user_id=None, actor_role=None) -> dict | None:
    day = day or datetime.now().strftime("%Y-%m-%d")
    execute(
        """UPDATE appointments SET status='Completed', updated_at=? WHERE doctor_id=? AND appointment_date=?
           AND status='InConsultation'""",
        (datetime.now().isoformat(timespec="seconds"), doctor_id, day),
    )
    nxt = query_one(
        """SELECT * FROM appointments WHERE doctor_id=? AND appointment_date=? AND status IN ('Scheduled','CheckedIn')
           ORDER BY token_number ASC LIMIT 1""",
        (doctor_id, day),
    )
    if not nxt:
        return None
    execute("UPDATE appointments SET status='InConsultation', updated_at=? WHERE appointment_id=?",
            (datetime.now().isoformat(timespec="seconds"), nxt["appointment_id"]))
    log_action(actor_user_id, actor_role, "Queue Advanced", nxt["appointment_id"], f"Token {nxt['token_number']} called.")
    return get_appointment(nxt["appointment_id"])
