"""Patient's own appointment list: view, reschedule, cancel (spec section 8)."""
from __future__ import annotations

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QComboBox, QDateEdit, QDialog, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from core.security.auth import Session
from core.services import appointment_service, doctor_service
from shared_ui.widgets import (
    EmptyState, StatusBadge, confirm, error_message, info_message, primary_button,
    secondary_button, section_heading,
)


class RescheduleDialog(QDialog):
    def __init__(self, parent, session: Session, appointment: dict):
        super().__init__(parent)
        self.session = session
        self.appointment = appointment
        self.setWindowTitle("Reschedule Appointment")
        self.resize(360, 240)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Dr. {appointment['doctor_name']}"))

        self.date_edit = QDateEdit(calendarPopup=True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.currentDate().addDays(1))
        self.date_edit.setMinimumDate(QDate.currentDate())
        self.date_edit.dateChanged.connect(self._refresh_slots)
        layout.addWidget(QLabel("New Date"))
        layout.addWidget(self.date_edit)

        self.slot_combo = QComboBox()
        layout.addWidget(QLabel("New Time"))
        layout.addWidget(self.slot_combo)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #DC2626;")
        layout.addWidget(self.error_label)

        btn_row = QHBoxLayout()
        cancel_btn = secondary_button("Cancel")
        save_btn = primary_button("Confirm")
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)
        self.saved = False
        self._refresh_slots()

    def _refresh_slots(self) -> None:
        self.slot_combo.clear()
        day = self.date_edit.date().toString("yyyy-MM-dd")
        slots = doctor_service.available_slots(self.appointment["doctor_id"], day)
        self.slot_combo.addItems(slots if slots else ["No slots available"])

    def _save(self) -> None:
        if self.slot_combo.currentText() == "No slots available":
            self.error_label.setText("Please choose a date with available slots.")
            return
        try:
            appointment_service.reschedule_appointment(
                self.appointment["appointment_id"], self.date_edit.date().toString("yyyy-MM-dd"),
                self.slot_combo.currentText(), self.session.user_id, self.session.role_name)
            self.saved = True
            self.accept()
        except ValueError as exc:
            self.error_label.setText(str(exc))


class PatientAppointmentsView(QWidget):
    def __init__(self, session: Session, main_window):
        super().__init__()
        self.session = session
        self.main_window = main_window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)
        layout.addWidget(section_heading("My Appointments"))
        self.list_container = QVBoxLayout()
        layout.addLayout(self.list_container)
        layout.addStretch()

    def refresh(self, **kwargs) -> None:
        while self.list_container.count():
            item = self.list_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        patient_id = self.session.linked_patient_id
        rows = appointment_service.list_for_patient(patient_id) if patient_id else []
        if not rows:
            self.list_container.addWidget(EmptyState("📅", "No appointments yet",
                                                        "Find a doctor to book your first visit."))
            return
        for appt in rows:
            self.list_container.addWidget(self._appointment_card(appt))

    def _appointment_card(self, appt: dict) -> QWidget:
        card = QWidget()
        card.setProperty("class", "card")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        info = QVBoxLayout()
        info.addWidget(QLabel(f"<b>Dr. {appt['doctor_name']}</b> — {appt.get('specialization','')}"))
        info.addWidget(QLabel(f"{appt['appointment_date']}  {appt['appointment_time']}  •  "
                               f"Token {appt['token_number']}"))
        if appt.get("reason"):
            info.addWidget(QLabel(f"Reason: {appt['reason']}"))
        layout.addLayout(info, stretch=1)
        layout.addWidget(StatusBadge(appt["status"]))
        if appt["status"] in ("Scheduled", "CheckedIn"):
            reschedule_btn = secondary_button("Reschedule")
            reschedule_btn.clicked.connect(lambda checked, a=appt: self._reschedule(a))
            cancel_btn = secondary_button("Cancel")
            cancel_btn.clicked.connect(lambda checked, a=appt: self._cancel(a))
            layout.addWidget(reschedule_btn)
            layout.addWidget(cancel_btn)
        return card

    def _reschedule(self, appt: dict) -> None:
        dialog = RescheduleDialog(self, self.session, appt)
        if dialog.exec() and dialog.saved:
            info_message(self, "Rescheduled", "✓ Appointment rescheduled successfully.")
            self.refresh()

    def _cancel(self, appt: dict) -> None:
        if confirm(self, "Cancel Appointment", "Are you sure you want to cancel this appointment?"):
            appointment_service.cancel_appointment(appt["appointment_id"], "Cancelled by patient.",
                                                     self.session.user_id, self.session.role_name)
            info_message(self, "Cancelled", "✓ Appointment cancelled.")
            self.refresh()
