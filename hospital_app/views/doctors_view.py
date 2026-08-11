"""Doctors module: list, search, add/edit, activate/deactivate,
schedule and leave management (spec sections 21-25)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QDateEdit, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)
from PySide6.QtCore import QDate

from core.security.auth import Session
from core.services import doctor_service
from core.theme import NAVY, TEXT_MUTED
from hospital_app.dialogs import DoctorFormDialog
from shared_ui.widgets import (
    EmptyState, SearchBox, StatusBadge, confirm, info_message, primary_button,
    secondary_button, section_heading,
)


class DoctorsView(QWidget):
    def __init__(self, session: Session, main_window):
        super().__init__()
        self.session = session
        self.main_window = main_window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        header_row = QHBoxLayout()
        header_row.addWidget(section_heading("Doctors"))
        header_row.addStretch()
        if session.has_permission(("Administrator",)):
            add_btn = primary_button("+ Add Doctor")
            add_btn.clicked.connect(self._open_add_doctor)
            header_row.addWidget(add_btn)
        layout.addLayout(header_row)

        filter_row = QHBoxLayout()
        self.search_box = SearchBox("Search by name or specialization")
        self.search_box.textChanged.connect(self.refresh)
        self.spec_filter = QComboBox()
        self.spec_filter.addItem("All Specializations")
        self.spec_filter.currentTextChanged.connect(self.refresh)
        filter_row.addWidget(self.search_box)
        filter_row.addWidget(self.spec_filter)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Doctor ID", "Doctor", "Department", "Specialization", "Experience", "Availability", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

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

        term = self.search_box.text().strip()
        spec = "" if self.spec_filter.currentText() == "All Specializations" else self.spec_filter.currentText()
        rows = doctor_service.search_doctors(term, specialization=spec, active_only=False)
        self.table.setRowCount(0)
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            for col, value in enumerate([row["doctor_id"], f"Dr. {row['full_name']}", row.get("department_name") or "-",
                                          row["specialization"], f"{row['experience_years']} yrs"]):
                self.table.setItem(r, col, QTableWidgetItem(value))
            avail = QWidget()
            avail_layout = QHBoxLayout(avail)
            avail_layout.setContentsMargins(4, 2, 4, 2)
            avail_layout.addWidget(StatusBadge("Active" if row["is_active"] else "Archived"))
            self.table.setCellWidget(r, 5, avail)

            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            edit_btn = secondary_button("Edit")
            edit_btn.clicked.connect(lambda checked, d=row: self._edit_doctor(d))
            actions_layout.addWidget(edit_btn)
            if self.session.has_permission(("Administrator",)):
                toggle_btn = secondary_button("Deactivate" if row["is_active"] else "Activate")
                toggle_btn.clicked.connect(lambda checked, d=row: self._toggle_active(d))
                actions_layout.addWidget(toggle_btn)
            self.table.setCellWidget(r, 6, actions)

    def _open_add_doctor(self) -> None:
        dialog = DoctorFormDialog(self)
        if dialog.exec() and dialog.saved_doctor_id:
            info_message(self, "Doctor Saved", "✓ Doctor added successfully.")
            self.refresh()

    def _edit_doctor(self, doctor_row: dict) -> None:
        full = doctor_service.get_doctor(doctor_row["doctor_id"])
        dialog = DoctorFormDialog(self, full)
        if dialog.exec() and dialog.saved_doctor_id:
            info_message(self, "Doctor Updated", "✓ Doctor details updated successfully.")
            self.refresh()

    def _toggle_active(self, doctor_row: dict) -> None:
        new_state = not bool(doctor_row["is_active"])
        action = "activate" if new_state else "deactivate"
        if confirm(self, "Confirm", f"Are you sure you want to {action} Dr. {doctor_row['full_name']}?"):
            doctor_service.set_active(doctor_row["doctor_id"], new_state, self.session.user_id, self.session.role_name)
            self.refresh()
