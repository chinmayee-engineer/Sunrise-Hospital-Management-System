"""Professional PDF generation for prescriptions, invoices, receipts and
medical summaries (spec 33), using reportlab."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER

from core.utils.paths import REPORTS_DIR

NAVY = colors.HexColor("#0B3D66")
TEAL = colors.HexColor("#0F8B8D")
LIGHT_GRAY = colors.HexColor("#F3F5F7")
HOSPITAL_NAME = "Sunrise Multispecialty Hospital"
HOSPITAL_ADDRESS = "12 MG Road, Bengaluru, Karnataka, 560001"
HOSPITAL_PHONE = "+91 80 4000 1234  |  info@sunrisehospital.example"

_styles = getSampleStyleSheet()
_styles.add(ParagraphStyle(name="HospitalTitle", fontSize=18, textColor=NAVY, fontName="Helvetica-Bold"))
_styles.add(ParagraphStyle(name="DocTitle", fontSize=14, textColor=TEAL, fontName="Helvetica-Bold",
                            spaceBefore=6, spaceAfter=6))
_styles.add(ParagraphStyle(name="Small", fontSize=9, textColor=colors.HexColor("#555555")))
_styles.add(ParagraphStyle(name="RightSmall", fontSize=9, alignment=TA_RIGHT, textColor=colors.HexColor("#555555")))
_styles.add(ParagraphStyle(name="SectionHeading", fontSize=11, textColor=NAVY, fontName="Helvetica-Bold",
                            spaceBefore=10, spaceAfter=4))
_styles.add(ParagraphStyle(name="CenterSmall", fontSize=9, alignment=TA_CENTER, textColor=colors.HexColor("#777777")))


def _header(doc_title: str, doc_id: str) -> list:
    elements = [
        Paragraph(f"🏥 {HOSPITAL_NAME}", _styles["HospitalTitle"]),
        Paragraph(HOSPITAL_ADDRESS, _styles["Small"]),
        Paragraph(HOSPITAL_PHONE, _styles["Small"]),
        Spacer(1, 6),
        HRFlowable(width="100%", thickness=1.2, color=NAVY),
        Spacer(1, 8),
        Paragraph(doc_title, _styles["DocTitle"]),
        Paragraph(f"Document ID: {doc_id}   |   Generated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}",
                   _styles["Small"]),
        Spacer(1, 10),
    ]
    return elements


def _footer_note(text: str = "This is a system-generated document.") -> list:
    return [Spacer(1, 14), HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCCC")),
            Spacer(1, 4), Paragraph(text, _styles["CenterSmall"])]


def generate_prescription_pdf(prescription: dict) -> Path:
    output_path = REPORTS_DIR / "summaries" / f"{prescription['prescription_id']}.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(output_path), pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm)
    elements = _header("Prescription", prescription["prescription_id"])

    info_table = Table([
        ["Patient", prescription["patient_name"], "Date", prescription["prescription_date"]],
        ["Doctor", f"Dr. {prescription['doctor_name']}", "Specialization", prescription.get("specialization", "")],
        ["Diagnosis", prescription.get("diagnosis", "-"), "Follow-up", prescription.get("follow_up_date", "-")],
    ], colWidths=[70, 170, 70, 170])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TEXTCOLOR", (0, 0), (0, -1), NAVY),
        ("TEXTCOLOR", (2, 0), (2, -1), NAVY),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Medicines", _styles["SectionHeading"]))

    rows = [["#", "Medicine", "Dosage", "Frequency", "Duration", "Instructions"]]
    for i, item in enumerate(prescription.get("items", []), start=1):
        rows.append([str(i), item["medicine_name"], item.get("dosage", "-"), item.get("frequency", "-"),
                     item.get("duration", "-"), item.get("instructions", "-") or item.get("before_after_food", "-")])
    med_table = Table(rows, colWidths=[18, 110, 65, 85, 65, 100])
    med_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(med_table)

    if prescription.get("instructions"):
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("General Instructions", _styles["SectionHeading"]))
        elements.append(Paragraph(prescription["instructions"], _styles["Small"]))

    elements += _footer_note("Please follow the dosage as prescribed. Contact the hospital for any concerns.")
    doc.build(elements)
    return output_path


def generate_invoice_pdf(invoice: dict) -> Path:
    output_path = REPORTS_DIR / "invoices" / f"{invoice['invoice_id']}.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(output_path), pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm)
    elements = _header("Invoice", invoice["invoice_id"])

    info_table = Table([
        ["Bill To", invoice["patient_name"], "Invoice Date", invoice["invoice_date"]],
        ["Phone", invoice.get("patient_phone", "-"), "Status", invoice["status"]],
    ], colWidths=[70, 170, 70, 170])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 10))

    rows = [["Description", "Category", "Qty", "Unit Price", "Total"]]
    for item in invoice.get("items", []):
        rows.append([item["description"], item.get("category", "-"), f"{item['quantity']:g}",
                     f"{item['unit_price']:.2f}", f"{item['line_total']:.2f}"])
    item_table = Table(rows, colWidths=[170, 90, 40, 80, 80])
    item_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
    ]))
    elements.append(item_table)
    elements.append(Spacer(1, 8))

    totals = Table([
        ["Subtotal", f"{invoice['subtotal']:.2f}"],
        ["Discount", f"-{invoice['discount']:.2f}"],
        ["Tax", f"{invoice['tax']:.2f}"],
        ["Total", f"{invoice['total']:.2f}"],
        ["Amount Paid", f"{invoice['amount_paid']:.2f}"],
        ["Balance Due", f"{(invoice['total'] - invoice['amount_paid']):.2f}"],
    ], colWidths=[420, 80])
    totals.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
        ("LINEABOVE", (0, 3), (-1, 3), 0.6, NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(totals)
    elements += _footer_note("Thank you for choosing " + HOSPITAL_NAME + ".")
    doc.build(elements)
    return output_path


def generate_receipt_pdf(invoice: dict, payment: dict) -> Path:
    output_path = REPORTS_DIR / "receipts" / f"{payment['payment_id']}.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(output_path), pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm)
    elements = _header("Payment Receipt", payment["payment_id"])
    table = Table([
        ["Received From", invoice["patient_name"]],
        ["Against Invoice", invoice["invoice_id"]],
        ["Amount", f"{payment['amount']:.2f}"],
        ["Payment Method", payment["payment_method"]],
        ["Payment Date", payment["payment_date"]],
        ["Reference No.", payment.get("reference_no") or "-"],
    ], colWidths=[150, 320])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#DDDDDD")),
    ]))
    elements.append(table)
    elements += _footer_note("This receipt confirms payment towards the above invoice.")
    doc.build(elements)
    return output_path


def generate_patient_summary_pdf(patient: dict, consultations: list[dict], prescriptions: list[dict],
                                  lab_tests: list[dict]) -> Path:
    output_path = REPORTS_DIR / "summaries" / f"{patient['patient_id']}_summary.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(output_path), pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm)
    elements = _header("Patient Medical Summary", patient["patient_id"])

    info = Table([
        ["Name", patient["full_name"], "Gender", patient["gender"]],
        ["DOB", patient["date_of_birth"], "Blood Group", patient.get("blood_group", "-")],
        ["Phone", patient["phone"], "Allergies", patient.get("allergies", "-") or "None recorded"],
    ], colWidths=[70, 170, 70, 170])
    info.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"), ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(info)

    elements.append(Paragraph("Consultation History", _styles["SectionHeading"]))
    rows = [["Date", "Doctor", "Diagnosis", "Follow-up"]]
    for c in consultations[:15]:
        rows.append([c["consultation_date"], f"Dr. {c['doctor_name']}", c.get("diagnosis", "-") or "-",
                     c.get("follow_up_date", "-") or "-"])
    if len(rows) == 1:
        rows.append(["-", "-", "No consultations recorded", "-"])
    t = Table(rows, colWidths=[70, 130, 200, 78])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
    ]))
    elements.append(t)

    elements.append(Paragraph("Prescriptions", _styles["SectionHeading"]))
    rows = [["Date", "Doctor", "Prescription ID"]]
    for p in prescriptions[:15]:
        rows.append([p["prescription_date"], f"Dr. {p['doctor_name']}", p["prescription_id"]])
    if len(rows) == 1:
        rows.append(["-", "-", "No prescriptions recorded"])
    t2 = Table(rows, colWidths=[70, 200, 208])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TEAL), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
    ]))
    elements.append(t2)

    elements.append(Paragraph("Lab Tests", _styles["SectionHeading"]))
    rows = [["Date", "Test", "Status"]]
    for l in lab_tests[:15]:
        rows.append([l["requested_date"], l["test_name"], l["status"]])
    if len(rows) == 1:
        rows.append(["-", "No lab tests recorded", "-"])
    t3 = Table(rows, colWidths=[70, 268, 140])
    t3.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
    ]))
    elements.append(t3)

    elements += _footer_note("Confidential medical record. For authorized use only.")
    doc.build(elements)
    return output_path
