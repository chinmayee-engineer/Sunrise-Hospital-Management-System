"""Billing, invoices and payments (spec 29)."""
from __future__ import annotations

from datetime import datetime

from core.database.db import execute, next_numeric_id, query_all, query_one, transaction
from core.services.audit_service import log_action
from core.services.notification_service import create_notification
from core.utils.ids import next_id

CATEGORIES = ["Consultation", "Lab", "Diagnostic", "Procedure", "Medicine", "Other"]
PAYMENT_METHODS = ["Cash", "Card", "UPI", "Insurance", "Other"]


def create_invoice(patient_id: str, items: list[dict], appointment_id: str | None = None,
                    discount: float = 0.0, tax: float = 0.0, notes: str = "",
                    actor_user_id: str | None = None, actor_role: str | None = None) -> str:
    if not items:
        raise ValueError("An invoice needs at least one line item.")
    subtotal = 0.0
    for item in items:
        item["line_total"] = round(float(item["quantity"]) * float(item["unit_price"]), 2)
        subtotal += item["line_total"]
    total = round(subtotal - discount + tax, 2)

    invoice_id = next_id("invoice", next_numeric_id("invoices", "invoice_id"))
    now = datetime.now().isoformat(timespec="seconds")
    with transaction() as cursor:
        cursor.execute(
            """INSERT INTO invoices (invoice_id, patient_id, appointment_id, invoice_date, subtotal, discount,
                  tax, total, amount_paid, status, notes, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 'Pending', ?, ?, ?)""",
            (invoice_id, patient_id, appointment_id, now[:10], round(subtotal, 2), discount, tax, total, notes, now, now),
        )
        for item in items:
            cursor.execute(
                """INSERT INTO invoice_items (invoice_id, description, category, quantity, unit_price, line_total)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (invoice_id, item["description"], item.get("category", "Other"), item["quantity"],
                 item["unit_price"], item["line_total"]),
            )
    create_notification("Payment", "New invoice generated", f"Invoice {invoice_id} for {total:.2f} is due.",
                         patient_id=patient_id)
    log_action(actor_user_id, actor_role, "Invoice Created", invoice_id, f"Total {total:.2f}")
    return invoice_id


def get_invoice(invoice_id: str) -> dict | None:
    header = query_one(
        """SELECT inv.*, p.full_name AS patient_name, p.phone AS patient_phone, p.address FROM invoices inv
           JOIN patients p ON p.patient_id = inv.patient_id WHERE inv.invoice_id = ?""",
        (invoice_id,),
    )
    if not header:
        return None
    header = dict(header)
    header["items"] = query_all("SELECT * FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
    header["payments"] = query_all("SELECT * FROM payments WHERE invoice_id = ? ORDER BY payment_date", (invoice_id,))
    return header


def record_payment(invoice_id: str, amount: float, payment_method: str = "Cash", reference_no: str = "",
                    notes: str = "", actor_user_id: str | None = None, actor_role: str | None = None) -> str:
    invoice = query_one("SELECT * FROM invoices WHERE invoice_id = ?", (invoice_id,))
    if not invoice:
        raise ValueError("Invoice not found.")
    if amount <= 0:
        raise ValueError("Payment amount must be greater than zero.")
    payment_id = next_id("payment", next_numeric_id("payments", "payment_id"))
    now = datetime.now().isoformat(timespec="seconds")
    new_paid = round(invoice["amount_paid"] + amount, 2)
    if new_paid >= invoice["total"]:
        status = "Paid"
    elif new_paid > 0:
        status = "PartiallyPaid"
    else:
        status = "Pending"
    with transaction() as cursor:
        cursor.execute(
            """INSERT INTO payments (payment_id, invoice_id, patient_id, amount, payment_method, payment_date,
                  reference_no, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (payment_id, invoice_id, invoice["patient_id"], amount, payment_method, now[:10], reference_no, notes, now),
        )
        cursor.execute("UPDATE invoices SET amount_paid=?, status=?, updated_at=? WHERE invoice_id=?",
                        (new_paid, status, now, invoice_id))
    create_notification("Payment", "Payment received", f"Payment of {amount:.2f} recorded for {invoice_id}.",
                         patient_id=invoice["patient_id"])
    log_action(actor_user_id, actor_role, "Payment Recorded", payment_id, f"{amount:.2f} on {invoice_id}")
    return payment_id


def cancel_invoice(invoice_id: str, actor_user_id=None, actor_role=None) -> None:
    execute("UPDATE invoices SET status='Cancelled', updated_at=? WHERE invoice_id=?",
            (datetime.now().isoformat(timespec="seconds"), invoice_id))
    log_action(actor_user_id, actor_role, "Invoice Cancelled", invoice_id, "")


def refund_invoice(invoice_id: str, actor_user_id=None, actor_role=None) -> None:
    execute("UPDATE invoices SET status='Refunded', updated_at=? WHERE invoice_id=?",
            (datetime.now().isoformat(timespec="seconds"), invoice_id))
    log_action(actor_user_id, actor_role, "Invoice Refunded", invoice_id, "")


def list_for_patient(patient_id: str) -> list[dict]:
    return query_all("SELECT * FROM invoices WHERE patient_id = ? ORDER BY invoice_date DESC", (patient_id,))


def list_all(status: str = "", term: str = "", limit: int = 500) -> list[dict]:
    sql = """SELECT inv.*, p.full_name AS patient_name FROM invoices inv
             JOIN patients p ON p.patient_id = inv.patient_id WHERE 1=1"""
    params: list = []
    if status:
        sql += " AND inv.status = ?"
        params.append(status)
    if term:
        sql += " AND (inv.invoice_id LIKE ? OR p.full_name LIKE ?)"
        like = f"%{term}%"
        params.extend([like, like])
    sql += " ORDER BY inv.invoice_date DESC LIMIT ?"
    params.append(limit)
    return query_all(sql, tuple(params))


def payment_history_for_patient(patient_id: str) -> list[dict]:
    return query_all(
        "SELECT * FROM payments WHERE patient_id = ? ORDER BY payment_date DESC", (patient_id,)
    )
