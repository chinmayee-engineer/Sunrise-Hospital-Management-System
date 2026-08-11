"""Shared appointment booking / rescheduling dialog used by staff
(and reused conceptually by the patient app's own booking flow)."""
from __future__ import annotations

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox, QDateEdit, QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QTextEdit, QVBoxLayout,
)

from core.services import appointment_service, doctor_service, patient_service
from shared_ui.widgets import error_message, primary_button, secondary_button


class BookAppointmentDialog(QDialog):
    def __init__(self, parent, patient_id: str | None = None, doctor_id: str | None = None):
        super().__init__(parent)
        self.setWindowTitle("Book Appointment")
        self.resize(440, 480)
        self.booked_appointment_id: str | None = None

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.patient_search = QLineEdit()
        self.patient_search.setPlaceholderText("Type name, ID or phone...")
        self.patient_results = QListWidget()
        self.patient_results.setMaximumHeight(90)
        self.patient_search.textChanged.connect(self._search_patients)
        self.patient_results.itemClicked.connect(self._select_patient)
        self.selected_patient_id = patient_id
        self.selected_patient_label = QLabel("No patient selected" if not patient_id else patient_id)
        form.addRow("Patient", self.patient_search)
        form.addRow("", self.patient_results)
        form.addRow("Selected Patient", self.selected_patient_label)

        self.doctor_combo = QComboBox()
        self.doctors = doctor_service.search_doctors(active_only=True)
        for d in self.doctors:
            self.doctor_combo.addItem(f"Dr. {d['full_name']} ({d['specialization']})", d["doctor_id"])
        if doctor_id:
            idx = next((i for i, d in enumerate(self.doctors) if d["doctor_id"] == doctor_id), -1)
            if idx >= 0:
                self.doctor_combo.setCurrentIndex(idx)
        self.doctor_combo.currentIndexChanged.connect(self._refresh_slots)
        form.addRow("Doctor", self.doctor_combo)

        self.date_edit = QDateEdit(calendarPopup=True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.currentDate().addDays(1))
        self.date_edit.setMinimumDate(QDate.currentDate())
        self.date_edit.dateChanged.connect(self._refresh_slots)
        form.addRow("Date", self.date_edit)

        self.slot_combo = QComboBox()
        form.addRow("Available Slot", self.slot_combo)

        self.reason_input = QTextEdit()
        self.reason_input.setMaximumHeight(60)
        form.addRow("Reason", self.reason_input)

        layout.addLayout(form)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #DC2626;")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)

        btn_row = QHBoxLayout()
        cancel_btn = secondary_button("Cancel")
        confirm_btn = primary_button("Confirm Appointment")
        cancel_btn.clicked.connect(self.reject)
        confirm_btn.clicked.connect(self._confirm)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(confirm_btn)
        layout.addLayout(btn_row)

        self._refresh_slots()

    def _search_patients(self, text: str) -> None:
        self.patient_results.clear()
        if len(text.strip()) < 2:
            return
        for p in patient_service.search_patients(text.strip(), limit=8):
            item_text = f"{p['patient_id']} — {p['full_name']} ({p['phone']})"
            self.patient_results.addItem(item_text)
            self.patient_results.item(self.patient_results.count() - 1).setData(1000, p["patient_id"])

    def _select_patient(self, item) -> None:
        self.selected_patient_id = item.data(1000)
        self.selected_patient_label.setText(item.text())

    def _refresh_slots(self) -> None:
        self.slot_combo.clear()
        if self.doctor_combo.count() == 0:
            return
        doctor_id = self.doctor_combo.currentData()
        day = self.date_edit.date().toString("yyyy-MM-dd")
        slots = doctor_service.available_slots(doctor_id, day)
        if not slots:
            self.slot_combo.addItem("No slots available")
        else:
            self.slot_combo.addItems(slots)

    def _confirm(self) -> None:
        if not self.selected_patient_id:
            self.error_label.setText("Please select a patient.")
            return
        if self.doctor_combo.count() == 0 or self.slot_combo.currentText() == "No slots available":
            self.error_label.setText("Please choose a date with available slots.")
            return
        doctor_id = self.doctor_combo.currentData()
        day = self.date_edit.date().toString("yyyy-MM-dd")
        time_str = self.slot_combo.currentText()
        from core.security.auth import get_current_session
        session = get_current_session()
        try:
            self.booked_appointment_id = appointment_service.book_appointment(
                self.selected_patient_id, doctor_id, day, time_str, self.reason_input.toPlainText().strip(),
                session.user_id if session else None, session.role_name if session else None,
            )
            self.accept()
        except ValueError as exc:
            self.error_label.setText(str(exc))
