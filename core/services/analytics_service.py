"""Reports & analytics (spec 32) -- aggregation queries used by both
the on-screen dashboard charts and the PDF/Excel exporters."""
from __future__ import annotations

from core.database.db import query_all, query_one


def patient_stats() -> dict:
    total = query_one("SELECT COUNT(*) AS c FROM patients WHERE status='Active'")["c"]
    new_30d = query_one(
        "SELECT COUNT(*) AS c FROM patients WHERE registration_date >= date('now', '-30 day')")["c"]
    returning = query_one(
        """SELECT COUNT(DISTINCT patient_id) AS c FROM (
             SELECT patient_id, COUNT(*) AS visits FROM appointments GROUP BY patient_id HAVING visits > 1)""")["c"]
    gender_rows = query_all("SELECT gender, COUNT(*) AS c FROM patients WHERE status='Active' GROUP BY gender")
    return {"total_active": total, "new_last_30_days": new_30d, "returning": returning,
            "by_gender": {r["gender"]: r["c"] for r in gender_rows}}


def appointment_stats(days: int = 30) -> dict:
    total = query_one(f"SELECT COUNT(*) AS c FROM appointments WHERE appointment_date >= date('now', '-{days} day')")["c"]
    by_status = query_all(
        f"""SELECT status, COUNT(*) AS c FROM appointments WHERE appointment_date >= date('now', '-{days} day')
            GROUP BY status""")
    daily = query_all(
        f"""SELECT appointment_date AS day, COUNT(*) AS c FROM appointments
            WHERE appointment_date >= date('now', '-{days} day') GROUP BY appointment_date ORDER BY appointment_date""")
    return {"total": total, "by_status": {r["status"]: r["c"] for r in by_status}, "daily": daily}


def doctor_workload(days: int = 30) -> list[dict]:
    return query_all(
        f"""SELECT d.doctor_id, d.full_name, d.specialization,
                   COUNT(a.appointment_id) AS appointment_count,
                   SUM(CASE WHEN a.status = 'Completed' THEN 1 ELSE 0 END) AS completed_count
            FROM doctors d LEFT JOIN appointments a
              ON a.doctor_id = d.doctor_id AND a.appointment_date >= date('now', '-{days} day')
            WHERE d.is_active = 1
            GROUP BY d.doctor_id ORDER BY appointment_count DESC""")


def financial_stats(days: int = 30) -> dict:
    revenue = query_one(
        f"SELECT COALESCE(SUM(amount),0) AS total FROM payments WHERE payment_date >= date('now', '-{days} day')")["total"]
    pending = query_one(
        "SELECT COALESCE(SUM(total - amount_paid),0) AS total FROM invoices WHERE status IN ('Pending','PartiallyPaid')")["total"]
    paid_invoices = query_one("SELECT COUNT(*) AS c FROM invoices WHERE status='Paid'")["c"]
    pending_invoices = query_one("SELECT COUNT(*) AS c FROM invoices WHERE status IN ('Pending','PartiallyPaid')")["c"]
    by_category = query_all(
        f"""SELECT ii.category, SUM(ii.line_total) AS total FROM invoice_items ii
            JOIN invoices inv ON inv.invoice_id = ii.invoice_id
            WHERE inv.invoice_date >= date('now', '-{days} day') GROUP BY ii.category""")
    return {
        "revenue_last_period": revenue, "pending_amount": pending, "paid_invoices": paid_invoices,
        "pending_invoices": pending_invoices, "revenue_by_category": {r["category"]: r["total"] for r in by_category},
    }


def age_distribution() -> list[dict]:
    return query_all(
        """SELECT
             CASE
               WHEN (julianday('now') - julianday(date_of_birth)) / 365.25 < 18 THEN '0-17'
               WHEN (julianday('now') - julianday(date_of_birth)) / 365.25 < 35 THEN '18-34'
               WHEN (julianday('now') - julianday(date_of_birth)) / 365.25 < 50 THEN '35-49'
               WHEN (julianday('now') - julianday(date_of_birth)) / 365.25 < 65 THEN '50-64'
               ELSE '65+'
             END AS age_band,
             COUNT(*) AS c
           FROM patients WHERE status='Active' GROUP BY age_band""")
