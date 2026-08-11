"""Appointments module for staff: search/filter, book, reschedule,
cancel, check-in (spec section 8)."""
from __future__ import annotations

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QComboBox, QDateEdit, QHBoxLayout, QHeaderView, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from core.security.auth import Session
from core.services import appointment_service, doctor_service
from hospital_app.booking_dialog import BookAppointmentDialog
from shared_ui.widgets import (
    SearchBox, StatusBadge, confirm, error_message, info_message, primary_button,
    secondary_button, section_heading,
)


class AppointmentsView(QWidget):
    STATUS_OPTIONS = ["All", "Scheduled", "CheckedIn", "InConsultation", "Completed", "Cancelled", "NoShow"]

    def __init__(self, session: Session, main_window):
        super().__init__()
        self.session = session
        self.main_window = main_window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        header_row = QHBoxLayout()
        header_row.addWidget(section_heading("Appointments"))
        header_row.addStretch()
        book_btn = primary_button("+ Book Appointment")
        book_btn.clicked.connect(self._open_booking)
        header_row.addWidget(book_btn)
        layout.addLayout(header_row)

        filter_row = QHBoxLayout()
        self.search_box = SearchBox("Search patient, doctor or appointment ID")
        self.search_box.textChanged.connect(self.refresh)
        self.status_filter = QComboBox()
        self.status_filter.addItems(self.STATUS_OPTIONS)
        self.status_filter.currentTextChanged.connect(self.refresh)
        self.date_filter = QDateEdit(calendarPopup=True)
        self.date_filter.setDisplayFormat("yyyy-MM-dd")
        self.date_filter.setDate(QDate.currentDate())
        self.date_filter.dateChanged.connect(self.refresh)
        self.any_date_btn = secondary_button("Any Date")
        self.any_date_btn.setCheckable(True)
        self.any_date_btn.clicked.connect(self.refresh)
        filter_row.addWidget(self.search_box)
        filter_row.addWidget(self.status_filter)
        filter_row.addWidget(self.date_filter)
        filter_row.addWidget(self.any_date_btn)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Appt ID", "Patient", "Doctor", "Date", "Time", "Status", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

    def refresh(self, **kwargs) -> None:
        term = self.search_box.text().strip()
        status = "" if self.status_filter.currentText() == "All" else self.status_filter.currentText()
        day = "" if self.any_date_btn.isChecked() else self.date_filter.date().toString("yyyy-MM-dd")
        rows = appointment_service.list_all(day=day, status=status, term=term)
        self.table.setRowCount(0)
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            for col, value in enumerate([row["appointment_id"], row["patient_name"], f"Dr. {row['doctor_name']}",
                                          row["appointment_date"], row["appointment_time"]]):
                self.table.setItem(r, col, QTableWidgetItem(value))
            status_container = QWidget()
            status_layout = QHBoxLayout(status_container)
            status_layout.setContentsMargins(4, 2, 4, 2)
            status_layout.addWidget(StatusBadge(row["status"]))
            self.table.setCellWidget(r, 5, status_container)

            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            if row["status"] in ("Scheduled", "CheckedIn"):
                checkin_btn = secondary_button("Check-In")
                checkin_btn.clicked.connect(lambda checked, a=row: self._checkin(a))
                actions_layout.addWidget(checkin_btn)
                cancel_btn = secondary_button("Cancel")
                cancel_btn.clicked.connect(lambda checked, a=row: self._cancel(a))
                actions_layout.addWidget(cancel_btn)
            self.table.setCellWidget(r, 6, actions)

    def _open_booking(self) -> None:
        dialog = BookAppointmentDialog(self)
        if dialog.exec() and dialog.booked_appointment_id:
            info_message(self, "Appointment Booked", "✓ Appointment booked successfully.")
            self.refresh()

    def _checkin(self, appt: dict) -> None:
        appointment_service.update_status(appt["appointment_id"], "CheckedIn",
                                           self.session.user_id, self.session.role_name)
        self.refresh()

    def _cancel(self, appt: dict) -> None:
        if confirm(self, "Cancel Appointment", f"Cancel appointment for {appt['patient_name']}?"):
            appointment_service.cancel_appointment(appt["appointment_id"], "Cancelled by staff.",
                                                     self.session.user_id, self.session.role_name)
            info_message(self, "Cancelled", "✓ Appointment cancelled.")
            self.refresh()
