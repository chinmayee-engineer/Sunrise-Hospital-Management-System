"""Self-service new-patient registration used from the Patient app's
login screen. Creates both a patient record and a linked login."""
from __future__ import annotations

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox, QDateEdit, QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout,
)

from core.services import patient_service, user_service
from core.utils.validators import required, valid_email, valid_phone
from shared_ui.widgets import primary_button, secondary_button


class PatientRegistrationDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("New Patient Registration")
        self.resize(420, 500)
        self.registered_username: str | None = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Create your patient account"))

        form = QFormLayout()
        self.full_name = QLineEdit()
        self.dob = QDateEdit(calendarPopup=True)
        self.dob.setDisplayFormat("yyyy-MM-dd")
        self.dob.setDate(QDate(1995, 1, 1))
        self.gender = QComboBox()
        self.gender.addItems(["Male", "Female", "Other"])
        self.phone = QLineEdit()
        self.email = QLineEdit()
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        form.addRow("Full Name *", self.full_name)
        form.addRow("Date of Birth *", self.dob)
        form.addRow("Gender *", self.gender)
        form.addRow("Phone *", self.phone)
        form.addRow("Email", self.email)
        form.addRow("Choose Username *", self.username)
        form.addRow("Choose Password *", self.password)
        layout.addLayout(form)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #DC2626;")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)

        btn_row = QHBoxLayout()
        cancel_btn = secondary_button("Cancel")
        save_btn = primary_button("Register")
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self._register)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _register(self) -> None:
        checks = [
            required(self.full_name.text().strip(), "Full name"),
            valid_phone(self.phone.text().strip()),
            valid_email(self.email.text().strip(), required_field=False),
            required(self.username.text().strip(), "Username"),
            required(self.password.text(), "Password"),
        ]
        for ok, msg in checks:
            if not ok:
                self.error_label.setText(msg)
                return
        if len(self.password.text()) < 6:
            self.error_label.setText("Password must be at least 6 characters.")
            return

        try:
            patient_id = patient_service.create_patient(dict(
                full_name=self.full_name.text().strip(), date_of_birth=self.dob.date().toString("yyyy-MM-dd"),
                gender=self.gender.currentText(), phone=self.phone.text().strip(),
                email=self.email.text().strip(),
            ))
            user_service.create_user(self.username.text().strip(), self.password.text(),
                                      self.full_name.text().strip(), "Patient",
                                      email=self.email.text().strip(), phone=self.phone.text().strip(),
                                      linked_patient_id=patient_id)
            self.registered_username = self.username.text().strip()
            self.accept()
        except ValueError as exc:
            self.error_label.setText(str(exc))
