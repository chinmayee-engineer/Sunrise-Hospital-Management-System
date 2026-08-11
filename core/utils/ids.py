"""Human-friendly, sequential ID generation for every entity type.

IDs look like:  P-10001 (patient), D-1001 (doctor), A-100001 (appointment),
C-100001 (consultation), RX-100001 (prescription), LAB-100001 (lab test),
INV-100001 (invoice), PAY-100001 (payment), DOC-100001 (document),
U-1001 (user), MSG-100001 (message), N-100001 (notification).
"""
from __future__ import annotations

PREFIXES = {
    "patient": ("P-", 10001),
    "doctor": ("D-", 1001),
    "user": ("U-", 1001),
    "appointment": ("A-", 100001),
    "consultation": ("C-", 100001),
    "prescription": ("RX-", 100001),
    "lab_test": ("LAB-", 100001),
    "invoice": ("INV-", 100001),
    "payment": ("PAY-", 100001),
    "document": ("DOC-", 100001),
    "message": ("MSG-", 100001),
    "notification": ("N-", 100001),
    "department": ("DEPT-", 101),
    "token": ("T-", 1),
    "backup": ("BK-", 1001),
}


def next_id(entity: str, current_max_numeric: int | None) -> str:
    """Compute the next display ID for an entity type.

    current_max_numeric: the highest numeric suffix already used in the
    database for this entity (None if there are no rows yet).
    """
    prefix, start = PREFIXES[entity]
    if current_max_numeric is None:
        number = start
    else:
        number = max(current_max_numeric + 1, start)
    return f"{prefix}{number}"


def numeric_part(display_id: str) -> int:
    """Extract the trailing integer of a generated ID, e.g. 'P-10007' -> 10007."""
    digits = "".join(ch for ch in display_id if ch.isdigit())
    return int(digits) if digits else 0
