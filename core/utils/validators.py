"""Reusable, GUI-agnostic validation helpers.

Every validator returns (is_valid: bool, message: str). Nothing here
raises -- callers decide how to surface problems (inline field errors,
toast, dialog, etc). This keeps invalid data from silently entering
the database (spec section 42).
"""
from __future__ import annotations

import re
from datetime import date, datetime

PHONE_RE = re.compile(r"^[6-9]\d{9}$|^\+?\d{7,15}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PIN_RE = re.compile(r"^\d{4,10}$")


def required(value: str, field_name: str) -> tuple[bool, str]:
    if value is None or str(value).strip() == "":
        return False, f"{field_name} is required."
    return True, ""


def valid_phone(value: str) -> tuple[bool, str]:
    if not value:
        return False, "Phone number is required."
    if not PHONE_RE.match(value.strip()):
        return False, "Enter a valid phone number."
    return True, ""


def valid_email(value: str, required_field: bool = True) -> tuple[bool, str]:
    value = (value or "").strip()
    if not value:
        return (False, "Email is required.") if required_field else (True, "")
    if not EMAIL_RE.match(value):
        return False, "Enter a valid email address."
    return True, ""


def valid_pincode(value: str) -> tuple[bool, str]:
    value = (value or "").strip()
    if not value:
        return True, ""  # optional
    if not PIN_RE.match(value):
        return False, "Enter a valid PIN/ZIP code."
    return True, ""


def valid_date(value: str, field_name: str = "Date") -> tuple[bool, str]:
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True, ""
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid date (YYYY-MM-DD)."


def not_future_date(value: str, field_name: str = "Date") -> tuple[bool, str]:
    ok, msg = valid_date(value, field_name)
    if not ok:
        return ok, msg
    if datetime.strptime(value, "%Y-%m-%d").date() > date.today():
        return False, f"{field_name} cannot be in the future."
    return True, ""


def valid_number(value, field_name: str, allow_zero: bool = True, allow_negative: bool = False) -> tuple[bool, str]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False, f"{field_name} must be a number."
    if not allow_negative and number < 0:
        return False, f"{field_name} cannot be negative."
    if not allow_zero and number == 0:
        return False, f"{field_name} cannot be zero."
    return True, ""


def valid_time_range(start_time: str, end_time: str) -> tuple[bool, str]:
    try:
        start = datetime.strptime(start_time, "%H:%M")
        end = datetime.strptime(end_time, "%H:%M")
    except (ValueError, TypeError):
        return False, "Enter valid start/end times (HH:MM)."
    if end <= start:
        return False, "End time must be after start time."
    return True, ""
