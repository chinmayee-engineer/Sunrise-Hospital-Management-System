"""Dialog for creating a digital prescription with multiple medicine
line items (spec section 26)."""
from __future__ import annotations

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDateEdit, QDialog, QFormLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout,
)

from core.services import patient_service, prescription_service
from shared_ui.widgets import danger_button, primary_button, secondary_button


class PrescriptionDialog(QDialog):
    def __init__(self, parent, patient_id: str, doctor_id: str, consultation_id: str | None = None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.doctor_id = doctor_id
        self.consultation_id = consultation_id
        patient = patient_service.get_patient(patient_id)
        self.setWindowTitle(f"New Prescription - {patient['full_name']}")
        self.resize(600, 560)
        self.saved_prescription_id: str | None = None

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.diagnosis = QLineEdit()
        self.symptoms = QLineEdit()
        self.follow_up = QDateEdit(calendarPopup=True)
        self.follow_up.setDisplayFormat("yyyy-MM-dd")
        self.follow_up.setDate(QDate.currentDate().addDays(7))
        form.addRow("Diagnosis", self.diagnosis)
        form.addRow("Symptoms", self.symptoms)
        form.addRow("Follow-up Date", self.follow_up)
        layout.addLayout(form)

        layout.addWidget(QLabel("Medicines"))
        self.med_table = QTableWidget(0, 5)
        self.med_table.setHorizontalHeaderLabels(["Medicine", "Dosage", "Frequency", "Duration", "Before/After Food"])
        self.med_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        layout.addWidget(self.med_table)

        med_btn_row = QHBoxLayout()
        add_med_btn = secondary_button("Add Medicine")
        add_med_btn.clicked.connect(self._add_medicine_row)
        remove_med_btn = secondary_button("Remove Selected")
        remove_med_btn.clicked.connect(self._remove_medicine_row)
        med_btn_row.addWidget(add_med_btn)
        med_btn_row.addWidget(remove_med_btn)
        med_btn_row.addStretch()
        layout.addLayout(med_btn_row)

        self.instructions = QTextEdit()
        self.instructions.setMaximumHeight(50)
        self.instructions.setPlaceholderText("General instructions...")
        layout.addWidget(QLabel("General Instructions"))
        layout.addWidget(self.instructions)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #DC2626;")
        layout.addWidget(self.error_label)

        btn_row = QHBoxLayout()
        cancel_btn = secondary_button("Cancel")
        save_btn = primary_button("Save Prescription")
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

        self._add_medicine_row()

    def _add_medicine_row(self) -> None:
        r = self.med_table.rowCount()
        self.med_table.insertRow(r)
        for c in range(5):
            self.med_table.setItem(r, c, QTableWidgetItem(""))

    def _remove_medicine_row(self) -> None:
        row = self.med_table.currentRow()
        if row >= 0:
            self.med_table.removeRow(row)

    def _save(self) -> None:
        medicines = []
        for r in range(self.med_table.rowCount()):
            name_item = self.med_table.item(r, 0)
            name = name_item.text().strip() if name_item else ""
            if not name:
                continue
            medicines.append(dict(
                medicine_name=name,
                dosage=(self.med_table.item(r, 1).text().strip() if self.med_table.item(r, 1) else ""),
                frequency=(self.med_table.item(r, 2).text().strip() if self.med_table.item(r, 2) else ""),
                duration=(self.med_table.item(r, 3).text().strip() if self.med_table.item(r, 3) else ""),
                before_after_food=(self.med_table.item(r, 4).text().strip() if self.med_table.item(r, 4) else ""),
            ))
        if not medicines:
            self.error_label.setText("Add at least one medicine with a name.")
            return

        from core.security.auth import get_current_session
        session = get_current_session()
        data = dict(
            consultation_id=self.consultation_id, patient_id=self.patient_id, doctor_id=self.doctor_id,
            diagnosis=self.diagnosis.text().strip(), symptoms=self.symptoms.text().strip(),
            instructions=self.instructions.toPlainText().strip(),
            follow_up_date=self.follow_up.date().toString("yyyy-MM-dd"),
        )
        try:
            self.saved_prescription_id = prescription_service.create_prescription(
                data, medicines, session.user_id if session else None, session.role_name if session else None)
            self.accept()
        except ValueError as exc:
            self.error_label.setText(str(exc))
