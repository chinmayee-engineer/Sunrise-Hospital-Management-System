"""Prescriptions list for staff (Doctors/Pharmacist/Administrator) with
PDF generation (spec section 26)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QHeaderView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from core.security.auth import Session
from core.services import prescription_service
from shared_ui.widgets import EmptyState, SearchBox, info_message, secondary_button, section_heading


class PrescriptionsView(QWidget):
    def __init__(self, session: Session, main_window):
        super().__init__()
        self.session = session
        self.main_window = main_window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)
        layout.addWidget(section_heading("Prescriptions"))

        self.search_box = SearchBox("Search by patient name")
        self.search_box.textChanged.connect(self.refresh)
        layout.addWidget(self.search_box)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Prescription ID", "Date", "Patient", "Doctor", "Diagnosis", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

    def refresh(self, **kwargs) -> None:
        doctor_id = self.session.linked_doctor_id
        rows = prescription_service.list_for_doctor(doctor_id) if doctor_id else self._all_prescriptions()
        term = self.search_box.text().strip().lower()
        if term:
            rows = [r for r in rows if term in r.get("patient_name", "").lower()]
        self.table.setRowCount(0)
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            for col, value in enumerate([row["prescription_id"], row["prescription_date"],
                                          row.get("patient_name", ""), f"Dr. {row.get('doctor_name','')}" if 'doctor_name' in row else "",
                                          row.get("diagnosis") or "-"]):
                self.table.setItem(r, col, QTableWidgetItem(value))
            actions = QWidget()
            layout = QHBoxLayout(actions)
            layout.setContentsMargins(2, 2, 2, 2)
            pdf_btn = secondary_button("Generate PDF")
            pdf_btn.clicked.connect(lambda checked, rid=row["prescription_id"]: self._generate_pdf(rid))
            layout.addWidget(pdf_btn)
            self.table.setCellWidget(r, 5, actions)

    def _all_prescriptions(self) -> list[dict]:
        from core.database.db import query_all
        return query_all(
            """SELECT rx.*, p.full_name AS patient_name, d.full_name AS doctor_name FROM prescriptions rx
               JOIN patients p ON p.patient_id = rx.patient_id
               JOIN doctors d ON d.doctor_id = rx.doctor_id ORDER BY rx.prescription_date DESC LIMIT 300""")

    def _generate_pdf(self, prescription_id: str) -> None:
        from core.reports.pdf_reports import generate_prescription_pdf
        full = prescription_service.get_prescription(prescription_id)
        path = generate_prescription_pdf(full)
        info_message(self, "PDF Generated", f"✓ Prescription PDF saved to:\n{path}")
