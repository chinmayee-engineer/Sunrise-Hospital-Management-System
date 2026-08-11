"""Patient's own profile: view + edit contact/medical info (spec section 5)."""
from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QLineEdit, QTextEdit, QVBoxLayout, QWidget

from core.security.auth import Session
from core.services import patient_service
from core.utils.validators import valid_email, valid_phone
from shared_ui.widgets import info_message, primary_button, section_heading


class ProfileView(QWidget):
    def __init__(self, session: Session, main_window):
        super().__init__()
        self.session = session
        self.main_window = main_window
        self.layout_root = QVBoxLayout(self)
        self.layout_root.setContentsMargins(24, 20, 24, 24)
        self.layout_root.setSpacing(14)

    def refresh(self, **kwargs) -> None:
        while self.layout_root.count():
            item = self.layout_root.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.layout_root.addWidget(section_heading("My Profile"))

        patient_id = self.session.linked_patient_id
        if not patient_id:
            return
        patient = patient_service.get_patient(patient_id)

        form = QFormLayout()
        self.phone = QLineEdit(patient["phone"])
        self.email = QLineEdit(patient.get("email") or "")
        self.address = QLineEdit(patient.get("address") or "")
        self.city = QLineEdit(patient.get("city") or "")
        self.state = QLineEdit(patient.get("state") or "")
        self.pin_code = QLineEdit(patient.get("pin_code") or "")
        self.allergies = QLineEdit(patient.get("allergies") or "")
        self.important_notes = QTextEdit(patient.get("important_notes") or "")
        self.important_notes.setMaximumHeight(70)

        readonly_fields = [
            ("Full Name", patient["full_name"]), ("Date of Birth", patient["date_of_birth"]),
            ("Gender", patient["gender"]), ("Blood Group", patient.get("blood_group") or "-"),
        ]
        for label, value in readonly_fields:
            field = QLineEdit(value)
            field.setEnabled(False)
            form.addRow(label, field)
        form.addRow("Phone", self.phone)
        form.addRow("Email", self.email)
        form.addRow("Address", self.address)
        form.addRow("City", self.city)
        form.addRow("State", self.state)
        form.addRow("PIN Code", self.pin_code)
        form.addRow("Allergies", self.allergies)
        form.addRow("Notes for care team", self.important_notes)
        self.layout_root.addLayout(form)

        self.error_label = QWidget()
        save_btn = primary_button("Save Changes")
        save_btn.clicked.connect(lambda: self._save(patient_id))
        self.layout_root.addWidget(save_btn)
        self.layout_root.addStretch()

    def _save(self, patient_id: str) -> None:
        ok1, msg1 = valid_phone(self.phone.text().strip())
        ok2, msg2 = valid_email(self.email.text().strip(), required_field=False)
        if not ok1:
            info_message(self, "Invalid Phone", msg1)
            return
        if not ok2:
            info_message(self, "Invalid Email", msg2)
            return
        patient_service.update_patient(patient_id, dict(
            phone=self.phone.text().strip(), email=self.email.text().strip(),
            address=self.address.text().strip(), city=self.city.text().strip(),
            state=self.state.text().strip(), pin_code=self.pin_code.text().strip(),
            allergies=self.allergies.text().strip(), important_notes=self.important_notes.toPlainText().strip(),
        ), self.session.user_id, self.session.role_name)
        info_message(self, "Profile Updated", "✓ Your profile has been updated successfully.")
        self.refresh()
