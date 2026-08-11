"""User accounts, roles and authentication."""
from __future__ import annotations

from datetime import datetime

from core.database.db import execute, next_numeric_id, query_all, query_one
from core.security.auth import Session, hash_password, verify_password
from core.services.audit_service import log_action
from core.utils.ids import next_id

DEFAULT_ROLES = [
    ("Administrator", "Full access to every module."),
    ("Doctor", "Patients, consultations, prescriptions, lab requests, appointments, medical records."),
    ("Receptionist", "Patient registration, appointments, queue, billing."),
    ("Nurse", "Assigned patients, vital signs, queue, patient information."),
    ("LabStaff", "Lab requests, results, reports."),
    ("Pharmacist", "Prescriptions, medicine records."),
    ("Patient", "Patient-facing self-service application."),
]


def ensure_roles() -> None:
    for name, description in DEFAULT_ROLES:
        existing = query_one("SELECT role_id FROM roles WHERE role_name = ?", (name,))
        if not existing:
            execute("INSERT INTO roles (role_name, description) VALUES (?, ?)", (name, description))


def get_role_id(role_name: str) -> int:
    row = query_one("SELECT role_id FROM roles WHERE role_name = ?", (role_name,))
    if not row:
        raise ValueError(f"Unknown role: {role_name}")
    return row["role_id"]


def create_user(username: str, password: str, full_name: str, role_name: str,
                 email: str = "", phone: str = "", linked_patient_id: str | None = None,
                 linked_doctor_id: str | None = None) -> str:
    if query_one("SELECT user_id FROM users WHERE username = ?", (username,)):
        raise ValueError("Username already exists.")
    user_id = next_id("user", next_numeric_id("users", "user_id"))
    password_hash, salt = hash_password(password)
    execute(
        """INSERT INTO users (user_id, username, password_hash, password_salt, full_name, role_id,
              linked_patient_id, linked_doctor_id, email, phone, is_active, must_change_password, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0, ?)""",
        (user_id, username, password_hash, salt, full_name, get_role_id(role_name),
         linked_patient_id, linked_doctor_id, email, phone, datetime.now().isoformat(timespec="seconds")),
    )
    log_action(user_id, role_name, "User Created", user_id, f"Account '{username}' created.")
    return user_id


def authenticate(username: str, password: str) -> Session | None:
    row = query_one(
        """SELECT u.*, r.role_name FROM users u
           JOIN roles r ON r.role_id = u.role_id
           WHERE u.username = ? AND u.is_active = 1""",
        (username,),
    )
    if not row:
        return None
    if not verify_password(password, row["password_hash"], row["password_salt"]):
        log_action(row["user_id"], row["role_name"], "Login Failed", row["user_id"], "Incorrect password.")
        return None
    execute("UPDATE users SET last_login_at = ? WHERE user_id = ?",
            (datetime.now().isoformat(timespec="seconds"), row["user_id"]))
    log_action(row["user_id"], row["role_name"], "Login", row["user_id"], "Successful login.")
    import time
    now = time.time()
    return Session(
        user_id=row["user_id"], username=row["username"], full_name=row["full_name"],
        role_name=row["role_name"], linked_patient_id=row["linked_patient_id"],
        linked_doctor_id=row["linked_doctor_id"], login_time=now, last_activity=now,
    )


def list_users() -> list[dict]:
    return query_all(
        """SELECT u.*, r.role_name FROM users u JOIN roles r ON r.role_id = u.role_id ORDER BY u.created_at DESC"""
    )


def set_active(user_id: str, is_active: bool, actor: Session | None) -> None:
    execute("UPDATE users SET is_active = ? WHERE user_id = ?", (1 if is_active else 0, user_id))
    log_action(actor.user_id if actor else None, actor.role_name if actor else None,
               "User Activated" if is_active else "User Deactivated", user_id, "")


def change_password(user_id: str, new_password: str) -> None:
    password_hash, salt = hash_password(new_password)
    execute("UPDATE users SET password_hash = ?, password_salt = ?, must_change_password = 0 WHERE user_id = ?",
            (password_hash, salt, user_id))
