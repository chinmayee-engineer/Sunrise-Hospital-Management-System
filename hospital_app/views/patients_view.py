"""Patients module: searchable list + full profile with tabs
(spec sections 10, 14-18)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QHeaderView, QLabel, QPushButton, QStackedWidget,
    QTableWidget, QTableWidgetItem, QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)

from core.security.auth import Session
from core.services import (
    billing_service, consultation_service, document_service, lab_service,
    patient_service, prescription_service,
)
from core.services.appointment_service import list_for_patient
from core.theme import NAVY, TEAL, TEXT_MUTED
from hospital_app.dialogs import PatientFormDialog
from shared_ui.widgets import (
    EmptyState, SearchBox, StatusBadge, error_message, info_message,
    primary_button, secondary_button, section_heading,
)


class PatientsView(QWidget):
    def __init__(self, session: Session, main_window):
        super().__init__()
        self.session = session
        self.main_window = main_window

        self.stack = QStackedWidget()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.stack)

        self.list_page = self._build_list_page()
        self.profile_page = QWidget()  # rebuilt each time a profile opens
        self.stack.addWidget(self.list_page)
        self.stack.addWidget(self.profile_page)

    # ------------------------------------------------------------ list page
    def _build_list_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        header_row = QHBoxLayout()
        header_row.addWidget(section_heading("Patients"))
        header_row.addStretch()
        add_btn = primary_button("+ Add New Patient")
        add_btn.clicked.connect(self._open_add_patient)
        header_row.addWidget(add_btn)
        layout.addLayout(header_row)

        filter_row = QHBoxLayout()
        self.search_box = SearchBox("Search by ID, name, phone or email")
        self.search_box.textChanged.connect(self.refresh)
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Active", "Archived", "All"])
        self.status_filter.currentTextChanged.connect(self.refresh)
        filter_row.addWidget(self.search_box)
        filter_row.addWidget(self.status_filter)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Patient ID", "Name", "Age", "Gender", "Phone", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.cellDoubleClicked.connect(self._row_double_clicked)
        layout.addWidget(self.table)

        self.empty_container = QVBoxLayout()
        layout.addLayout(self.empty_container)
        return page

    def refresh(self, open_patient_id: str | None = None, **kwargs) -> None:
        if open_patient_id:
            self.open_profile(open_patient_id)
            return
        self.stack.setCurrentWidget(self.list_page)
        term = self.search_box.text().strip()
        status = "" if self.status_filter.currentText() == "All" else self.status_filter.currentText()
        rows = patient_service.search_patients(term, status)
        self.table.setRowCount(0)
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            age = patient_service.calculate_age(row["date_of_birth"])
            for col, value in enumerate([row["patient_id"], row["full_name"], str(age), row["gender"], row["phone"]]):
                self.table.setItem(r, col, QTableWidgetItem(value))
            badge_container = QWidget()
            badge_layout = QHBoxLayout(badge_container)
            badge_layout.setContentsMargins(4, 2, 4, 2)
            badge_layout.addWidget(StatusBadge(row["status"]))
            badge_layout.addStretch()
            self.table.setCellWidget(r, 5, badge_container)
            self.table.item(r, 0).setData(Qt.UserRole, row["patient_id"])
        if not rows:
            pass  # table itself will just look empty; header still communicates state

    def _row_double_clicked(self, row: int, _col: int) -> None:
        patient_id = self.table.item(row, 0).data(Qt.UserRole)
        self.open_profile(patient_id)

    def _open_add_patient(self) -> None:
        dialog = PatientFormDialog(self)
        if dialog.exec() and dialog.saved_patient_id:
            info_message(self, "Patient Saved", "✓ Patient added successfully.")
            self.refresh()
        elif dialog.saved_patient_id:
            self.open_profile(dialog.saved_patient_id)

    # --------------------------------------------------------- profile page
    def open_profile(self, patient_id: str) -> None:
        patient = patient_service.get_patient(patient_id)
        if not patient:
            error_message(self, "Not Found", "This patient record could not be found.")
            return
        patient_service.log_patient_viewed(patient_id, self.session.user_id, self.session.role_name)

        self.stack.removeWidget(self.profile_page)
        self.profile_page.deleteLater()
        self.profile_page = self._build_profile_page(patient)
        self.stack.addWidget(self.profile_page)
        self.stack.setCurrentWidget(self.profile_page)

    def _build_profile_page(self, patient: dict) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(12)

        back_btn = secondary_button("← Back to Patients")
        back_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.list_page))
        layout.addWidget(back_btn, alignment=Qt.AlignLeft)

        age = patient_service.calculate_age(patient["date_of_birth"])
        header = QLabel(
            f"<span style='color:{TEXT_MUTED}; font-size:11px;'>PATIENT {patient['patient_id']}</span><br>"
            f"<span style='font-size:20px; font-weight:700; color:{NAVY};'>{patient['full_name']}</span><br>"
            f"<span style='color:{TEXT_MUTED};'>{patient['gender']} • {age} Years • Blood Group: "
            f"{patient.get('blood_group') or 'Unknown'}</span><br>"
            f"<span style='color:#DC2626;'>Allergies: {patient.get('allergies') or 'None recorded'}</span>"
        )
        layout.addWidget(header)

        edit_btn = secondary_button("Edit Patient")
        edit_btn.clicked.connect(lambda: self._edit_patient(patient))
        archive_btn = secondary_button("Archive Patient")
        archive_btn.clicked.connect(lambda: self._archive_patient(patient))
        action_row = QHBoxLayout()
        action_row.addWidget(edit_btn)
        action_row.addWidget(archive_btn)
        action_row.addStretch()
        layout.addLayout(action_row)

        tabs = QTabWidget()
        tabs.addTab(self._overview_tab(patient), "Overview")
        tabs.addTab(self._medical_history_tab(patient), "Medical History")
        tabs.addTab(self._consultations_tab(patient), "Consultations")
        tabs.addTab(self._prescriptions_tab(patient), "Prescriptions")
        tabs.addTab(self._lab_tab(patient), "Lab Reports")
        tabs.addTab(self._documents_tab(patient), "Documents")
        tabs.addTab(self._appointments_tab(patient), "Appointments")
        tabs.addTab(self._billing_tab(patient), "Billing")
        tabs.addTab(self._timeline_tab(patient), "Timeline")
        layout.addWidget(tabs)
        return page

    def _edit_patient(self, patient: dict) -> None:
        dialog = PatientFormDialog(self, patient)
        if dialog.exec() and dialog.saved_patient_id:
            info_message(self, "Patient Updated", "✓ Patient details updated successfully.")
            self.open_profile(patient["patient_id"])

    def _archive_patient(self, patient: dict) -> None:
        from shared_ui.widgets import confirm
        if confirm(self, "Archive Patient", f"Archive {patient['full_name']}'s record?"):
            patient_service.archive_patient(patient["patient_id"], self.session.user_id, self.session.role_name)
            info_message(self, "Archived", "✓ Patient archived successfully.")
            self.stack.setCurrentWidget(self.list_page)
            self.refresh()

    def _overview_tab(self, patient: dict) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        info = "\n".join([
            f"Phone: {patient['phone']}", f"Email: {patient.get('email') or '-'}",
            f"Address: {patient.get('address') or '-'}, {patient.get('city') or ''} {patient.get('state') or ''} "
            f"{patient.get('pin_code') or ''}".strip(),
            f"Date of Birth: {patient['date_of_birth']}", f"Registered: {patient['registration_date']}",
            "", "Emergency Contact:",
            f"  {patient.get('emergency_contact_name') or '-'} ({patient.get('emergency_relationship') or '-'}) "
            f"- {patient.get('emergency_phone') or '-'}",
        ])
        label = QLabel(info)
        label.setWordWrap(True)
        layout.addWidget(label)
        layout.addStretch()
        return widget

    def _medical_history_tab(self, patient: dict) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        text = "\n\n".join([
            f"Existing Conditions: {patient.get('existing_conditions') or 'None recorded'}",
            f"Chronic Conditions: {patient.get('chronic_conditions') or 'None recorded'}",
            f"Previous Surgeries: {patient.get('previous_surgeries') or 'None recorded'}",
            f"Allergies: {patient.get('allergies') or 'None recorded'}",
            f"Medical History Notes: {patient.get('medical_history') or 'None recorded'}",
            f"Important Notes: {patient.get('important_notes') or 'None recorded'}",
        ])
        label = QLabel(text)
        label.setWordWrap(True)
        layout.addWidget(label)
        layout.addStretch()
        return widget

    def _consultations_tab(self, patient: dict) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        rows = consultation_service.history_for_patient(patient["patient_id"])
        if not rows:
            layout.addWidget(EmptyState("🩺", "No consultations yet", "New consultations will appear here."))
        for c in rows:
            box = QLabel(
                f"<b>{c['consultation_date']}</b> — Dr. {c['doctor_name']} ({c.get('specialization','')})<br>"
                f"Reason: {c.get('chief_complaint') or '-'}<br>Diagnosis: {c.get('diagnosis') or '-'}<br>"
                f"Symptoms: {c.get('symptoms') or '-'}<br>"
                f"Vitals: BP {c.get('blood_pressure') or '-'}, Temp {c.get('temperature') or '-'}°F, "
                f"HR {c.get('heart_rate') or '-'}<br>Treatment: {c.get('treatment') or '-'}<br>"
                f"Follow-up: {c.get('follow_up_date') or '-'}"
            )
            box.setWordWrap(True)
            box.setStyleSheet("background: white; border: 1px solid #E3E7EC; border-radius: 8px; padding: 10px;")
            layout.addWidget(box)
        layout.addStretch()
        return widget

    def _prescriptions_tab(self, patient: dict) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        rows = prescription_service.list_for_patient(patient["patient_id"])
        if not rows:
            layout.addWidget(EmptyState("💊", "No prescriptions yet", ""))
        for rx in rows:
            full = prescription_service.get_prescription(rx["prescription_id"])
            meds = ", ".join(f"{m['medicine_name']} ({m['dosage']})" for m in full["items"])
            box = QLabel(f"<b>{rx['prescription_date']}</b> — Dr. {rx['doctor_name']}<br>"
                         f"Diagnosis: {rx.get('diagnosis') or '-'}<br>Medicines: {meds}")
            box.setWordWrap(True)
            box.setStyleSheet("background: white; border: 1px solid #E3E7EC; border-radius: 8px; padding: 10px;")
            layout.addWidget(box)

            pdf_btn = secondary_button("Generate PDF")
            pdf_btn.clicked.connect(lambda checked, p=full: self._generate_rx_pdf(p))
            layout.addWidget(pdf_btn, alignment=Qt.AlignLeft)
        layout.addStretch()
        return widget

    def _generate_rx_pdf(self, prescription: dict) -> None:
        from core.reports.pdf_reports import generate_prescription_pdf
        path = generate_prescription_pdf(prescription)
        info_message(self, "PDF Generated", f"✓ Prescription PDF saved to:\n{path}")

    def _lab_tab(self, patient: dict) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        rows = lab_service.list_for_patient(patient["patient_id"])
        if not rows:
            layout.addWidget(EmptyState("🧪", "No lab tests yet", ""))
        for lab in rows:
            box = QLabel(f"<b>{lab['test_name']}</b> ({lab['test_type']}) — requested {lab['requested_date']}<br>"
                         f"Status: {lab['status']}<br>Result: {lab.get('result_summary') or 'Pending'}")
            box.setWordWrap(True)
            box.setStyleSheet("background: white; border: 1px solid #E3E7EC; border-radius: 8px; padding: 10px;")
            layout.addWidget(box)
        layout.addStretch()
        return widget

    def _documents_tab(self, patient: dict) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        rows = document_service.list_for_patient(patient["patient_id"])
        if not rows:
            layout.addWidget(EmptyState("📄", "No documents uploaded", ""))
        for doc in rows:
            box = QLabel(f"<b>{doc['title']}</b> ({doc['document_type']}) — {doc['uploaded_at'][:10]}")
            box.setStyleSheet("background: white; border: 1px solid #E3E7EC; border-radius: 8px; padding: 10px;")
            layout.addWidget(box)
        layout.addStretch()
        return widget

    def _appointments_tab(self, patient: dict) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        rows = list_for_patient(patient["patient_id"])
        if not rows:
            layout.addWidget(EmptyState("📅", "No appointments yet", ""))
        for appt in rows:
            row = QHBoxLayout()
            label = QLabel(f"{appt['appointment_date']} {appt['appointment_time']} — Dr. {appt['doctor_name']} "
                           f"(Token {appt['token_number']})")
            row.addWidget(label)
            row.addStretch()
            row.addWidget(StatusBadge(appt["status"]))
            container = QWidget()
            container.setLayout(row)
            layout.addWidget(container)
        layout.addStretch()
        return widget

    def _billing_tab(self, patient: dict) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        rows = billing_service.list_for_patient(patient["patient_id"])
        if not rows:
            layout.addWidget(EmptyState("💰", "No invoices yet", ""))
        for inv in rows:
            row = QHBoxLayout()
            label = QLabel(f"{inv['invoice_id']} — {inv['invoice_date']} — Total ₹{inv['total']:.2f} "
                           f"(Paid ₹{inv['amount_paid']:.2f})")
            row.addWidget(label)
            row.addStretch()
            row.addWidget(StatusBadge(inv["status"]))
            container = QWidget()
            container.setLayout(row)
            layout.addWidget(container)
        layout.addStretch()
        return widget

    def _timeline_tab(self, patient: dict) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        events = consultation_service.medical_timeline(patient["patient_id"])
        if not events:
            layout.addWidget(EmptyState("🕒", "No medical timeline yet", ""))
        current_date = None
        for event in events:
            if event["date"] != current_date:
                current_date = event["date"]
                date_label = QLabel(f"<b>{current_date}</b>")
                date_label.setStyleSheet(f"color: {NAVY}; margin-top: 8px;")
                layout.addWidget(date_label)
            row = QLabel(f"├── {event['type']}: {event['summary']}")
            row.setStyleSheet(f"color: {TEAL}; margin-left: 10px;")
            layout.addWidget(row)
        layout.addStretch()
        return widget
