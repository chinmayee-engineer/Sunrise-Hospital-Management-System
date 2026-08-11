"""Find a Doctor: search/filter + book appointment (spec sections 7-8)."""
from __future__ import annotations

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox, QDateEdit, QDialog, QFormLayout, QHBoxLayout, QLabel, QTextEdit, QVBoxLayout, QWidget,
)

from core.security.auth import Session
from core.services import appointment_service, doctor_service
from core.theme import NAVY, TEAL, TEXT_MUTED
from shared_ui.widgets import (
    EmptyState, SearchBox, add_card_shadow, error_message, info_message, primary_button,
    secondary_button, section_heading,
)


class PatientBookingDialog(QDialog):
    def __init__(self, parent, session: Session, doctor: dict):
        super().__init__(parent)
        self.session = session
        self.doctor = doctor
        self.setWindowTitle(f"Book Appointment - Dr. {doctor['full_name']}")
        self.resize(400, 380)
        self.booked_id: str | None = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<b>Dr. {doctor['full_name']}</b> — {doctor['specialization']}"))
        layout.addWidget(QLabel(f"Consultation Fee: ₹{doctor['consultation_fee']:.0f}"))

        form = QFormLayout()
        self.date_edit = QDateEdit(calendarPopup=True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.currentDate().addDays(1))
        self.date_edit.setMinimumDate(QDate.currentDate())
        self.date_edit.dateChanged.connect(self._refresh_slots)
        form.addRow("Preferred Date", self.date_edit)
        self.slot_combo = QComboBox()
        form.addRow("Available Slot", self.slot_combo)
        self.reason = QTextEdit()
        self.reason.setMaximumHeight(60)
        self.reason.setPlaceholderText("Reason for visit...")
        form.addRow("Reason", self.reason)
        layout.addLayout(form)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #DC2626;")
        layout.addWidget(self.error_label)

        btn_row = QHBoxLayout()
        cancel_btn = secondary_button("Cancel")
        book_btn = primary_button("Confirm Appointment")
        cancel_btn.clicked.connect(self.reject)
        book_btn.clicked.connect(self._confirm)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(book_btn)
        layout.addLayout(btn_row)

        self._refresh_slots()

    def _refresh_slots(self) -> None:
        self.slot_combo.clear()
        day = self.date_edit.date().toString("yyyy-MM-dd")
        slots = doctor_service.available_slots(self.doctor["doctor_id"], day)
        self.slot_combo.addItems(slots if slots else ["No slots available"])

    def _confirm(self) -> None:
        if self.slot_combo.currentText() == "No slots available":
            self.error_label.setText("Please choose a date with available slots.")
            return
        day = self.date_edit.date().toString("yyyy-MM-dd")
        time_str = self.slot_combo.currentText()
        try:
            self.booked_id = appointment_service.book_appointment(
                self.session.linked_patient_id, self.doctor["doctor_id"], day, time_str,
                self.reason.toPlainText().strip(), self.session.user_id, self.session.role_name)
            self.accept()
        except ValueError as exc:
            self.error_label.setText(str(exc))


class FindDoctorView(QWidget):
    def __init__(self, session: Session, main_window):
        super().__init__()
        self.session = session
        self.main_window = main_window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)
        layout.addWidget(section_heading("Find a Doctor"))

        filter_row = QHBoxLayout()
        self.search_box = SearchBox("Search by doctor name")
        self.search_box.textChanged.connect(self.refresh)
        self.spec_filter = QComboBox()
        self.spec_filter.addItem("All Specializations")
        self.spec_filter.currentTextChanged.connect(self.refresh)
        filter_row.addWidget(self.search_box)
        filter_row.addWidget(self.spec_filter)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        self.results_container = QVBoxLayout()
        layout.addLayout(self.results_container)
        layout.addStretch()

    def refresh(self, **kwargs) -> None:
        specs = doctor_service.list_specializations()
        current = self.spec_filter.currentText()
        self.spec_filter.blockSignals(True)
        self.spec_filter.clear()
        self.spec_filter.addItem("All Specializations")
        self.spec_filter.addItems(specs)
        if current in specs:
            self.spec_filter.setCurrentText(current)
        self.spec_filter.blockSignals(False)

        while self.results_container.count():
            item = self.results_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        term = self.search_box.text().strip()
        spec = "" if self.spec_filter.currentText() == "All Specializations" else self.spec_filter.currentText()
        doctors = doctor_service.search_doctors(term, specialization=spec, active_only=True)
        if not doctors:
            self.results_container.addWidget(EmptyState("🔍", "No doctors found", "Try a different search."))
            return
        for d in doctors:
            self.results_container.addWidget(self._doctor_card(d))

    def _doctor_card(self, doctor: dict) -> QWidget:
        card = QWidget()
        card.setProperty("class", "card")
        add_card_shadow(card)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)

        info = QVBoxLayout()
        info.addWidget(QLabel(f"<b style='font-size:15px; color:{NAVY};'>Dr. {doctor['full_name']}</b>"))
        info.addWidget(QLabel(f"{doctor['specialization']}  •  {doctor.get('department_name') or ''}"))
        info.addWidget(QLabel(f"{doctor.get('qualification') or ''}"))
        info.addWidget(QLabel(f"Experience: {doctor['experience_years']} years  •  "
                               f"Fee: ₹{doctor['consultation_fee']:.0f}"))
        info.addWidget(QLabel(f"Available: {doctor.get('working_days') or '-'}  "
                               f"({doctor.get('start_time','')} - {doctor.get('end_time','')})"))
        layout.addLayout(info, stretch=1)

        book_btn = primary_button("Book Appointment")
        book_btn.clicked.connect(lambda checked, d=doctor: self._book(d))
        layout.addWidget(book_btn, alignment=Qt.AlignVCenter)
        return card

    def _book(self, doctor: dict) -> None:
        dialog = PatientBookingDialog(self, self.session, doctor)
        if dialog.exec() and dialog.booked_id:
            info_message(self, "Appointment Booked", "✓ Your appointment has been confirmed.")
            self.main_window.navigate_to("dashboard")
