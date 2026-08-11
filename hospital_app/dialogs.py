"""Shared, reusable dialogs for the hospital app: add/edit patient,
duplicate warning, add/edit doctor. Kept separate from views/ because
they're opened from several different pages."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QDateEdit, QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QSpinBox, QDoubleSpinBox, QTabWidget, QTextEdit,
    QVBoxLayout, QWidget, QCheckBox,
)
from PySide6.QtCore import QDate

from core.services import doctor_service, patient_service
from core.utils.validators import valid_email, valid_phone, valid_pincode, required
from shared_ui.widgets import danger_button, error_message, primary_button, secondary_button


class DuplicatePatientDialog(QDialog):
    """Shown before creating a patient when possible duplicates exist
    (spec section 13)."""

    def __init__(self, parent, duplicates: list[dict]):
        super().__init__(parent)
        self.setWindowTitle("Possible Existing Patient")
        self.result_action = "cancel"
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("⚠ We found existing patient records that may match:"))
        for d in duplicates[:5]:
            box = QLabel(
                f"Patient ID: {d['patient_id']}\nName: {d['full_name']}\n"
                f"Date of Birth: {d['date_of_birth']}\nPhone: {d['phone']}"
            )
            box.setStyleSheet("background: #FEF3E2; border: 1px solid #F3C97A; border-radius: 6px; padding: 8px;")
            layout.addWidget(box)
        btn_row = QHBoxLayout()
        view_btn = secondary_button("View Existing Patient")
        create_btn = danger_button("Create Anyway")
        cancel_btn = primary_button("Cancel")
        view_btn.clicked.connect(lambda: self._finish("view"))
        create_btn.clicked.connect(lambda: self._finish("create"))
        cancel_btn.clicked.connect(lambda: self._finish("cancel"))
        btn_row.addWidget(view_btn)
        btn_row.addWidget(create_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)
        self._existing_id = duplicates[0]["patient_id"] if duplicates else None

    def _finish(self, action: str) -> None:
        self.result_action = action
        self.accept()


class PatientFormDialog(QDialog):
    """Multi-section Add/Edit Patient form (spec section 12)."""

    def __init__(self, parent, patient: dict | None = None):
        super().__init__(parent)
        self.patient = patient
        self.setWindowTitle("Edit Patient" if patient else "Add New Patient")
        self.resize(560, 640)
        self.saved_patient_id: str | None = None

        outer = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        form = QVBoxLayout(inner)
        form.setSpacing(14)

        form.addWidget(self._section_label("Personal Information"))
        personal = QFormLayout()
        self.full_name = QLineEdit()
        self.dob = QDateEdit(calendarPopup=True)
        self.dob.setDisplayFormat("yyyy-MM-dd")
        self.dob.setDate(QDate(1990, 1, 1))
        self.gender = QComboBox()
        self.gender.addItems(["Male", "Female", "Other"])
        self.blood_group = QComboBox()
        self.blood_group.addItems(["", "O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"])
        personal.addRow("Full Name *", self.full_name)
        personal.addRow("Date of Birth *", self.dob)
        personal.addRow("Gender *", self.gender)
        personal.addRow("Blood Group", self.blood_group)
        form.addLayout(personal)

        form.addWidget(self._section_label("Contact Information"))
        contact = QFormLayout()
        self.phone = QLineEdit()
        self.email = QLineEdit()
        self.address = QLineEdit()
        self.city = QLineEdit()
        self.state = QLineEdit()
        self.pin_code = QLineEdit()
        contact.addRow("Phone *", self.phone)
        contact.addRow("Email", self.email)
        contact.addRow("Address", self.address)
        contact.addRow("City", self.city)
        contact.addRow("State", self.state)
        contact.addRow("PIN Code", self.pin_code)
        form.addLayout(contact)

        form.addWidget(self._section_label("Emergency Information"))
        emergency = QFormLayout()
        self.emergency_name = QLineEdit()
        self.emergency_relationship = QLineEdit()
        self.emergency_phone = QLineEdit()
        emergency.addRow("Contact Name", self.emergency_name)
        emergency.addRow("Relationship", self.emergency_relationship)
        emergency.addRow("Emergency Phone", self.emergency_phone)
        form.addLayout(emergency)

        form.addWidget(self._section_label("Medical Information"))
        medical = QFormLayout()
        self.allergies = QLineEdit()
        self.existing_conditions = QLineEdit()
        self.previous_surgeries = QLineEdit()
        self.chronic_conditions = QLineEdit()
        self.medical_history = QTextEdit()
        self.medical_history.setMaximumHeight(70)
        self.important_notes = QTextEdit()
        self.important_notes.setMaximumHeight(60)
        medical.addRow("Allergies", self.allergies)
        medical.addRow("Existing Conditions", self.existing_conditions)
        medical.addRow("Previous Surgeries", self.previous_surgeries)
        medical.addRow("Chronic Conditions", self.chronic_conditions)
        medical.addRow("Medical History", self.medical_history)
        medical.addRow("Important Notes", self.important_notes)
        form.addLayout(medical)

        scroll.setWidget(inner)
        outer.addWidget(scroll)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #DC2626;")
        self.error_label.setWordWrap(True)
        outer.addWidget(self.error_label)

        btn_row = QHBoxLayout()
        cancel_btn = secondary_button("Cancel")
        clear_btn = secondary_button("Clear")
        save_btn = primary_button("Save Patient")
        cancel_btn.clicked.connect(self.reject)
        clear_btn.clicked.connect(self._clear)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        outer.addLayout(btn_row)

        if patient:
            self._populate(patient)

    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("font-weight: 700; color: #0B3D66; font-size: 13px; margin-top: 4px;")
        return label

    def _populate(self, p: dict) -> None:
        self.full_name.setText(p["full_name"])
        y, m, d = (int(x) for x in p["date_of_birth"].split("-"))
        self.dob.setDate(QDate(y, m, d))
        self.gender.setCurrentText(p["gender"])
        self.blood_group.setCurrentText(p.get("blood_group") or "")
        self.phone.setText(p["phone"])
        self.email.setText(p.get("email") or "")
        self.address.setText(p.get("address") or "")
        self.city.setText(p.get("city") or "")
        self.state.setText(p.get("state") or "")
        self.pin_code.setText(p.get("pin_code") or "")
        self.emergency_name.setText(p.get("emergency_contact_name") or "")
        self.emergency_relationship.setText(p.get("emergency_relationship") or "")
        self.emergency_phone.setText(p.get("emergency_phone") or "")
        self.allergies.setText(p.get("allergies") or "")
        self.existing_conditions.setText(p.get("existing_conditions") or "")
        self.previous_surgeries.setText(p.get("previous_surgeries") or "")
        self.chronic_conditions.setText(p.get("chronic_conditions") or "")
        self.medical_history.setPlainText(p.get("medical_history") or "")
        self.important_notes.setPlainText(p.get("important_notes") or "")

    def _clear(self) -> None:
        for widget in (self.full_name, self.phone, self.email, self.address, self.city, self.state,
                       self.pin_code, self.emergency_name, self.emergency_relationship, self.emergency_phone,
                       self.allergies, self.existing_conditions, self.previous_surgeries, self.chronic_conditions):
            widget.clear()
        self.medical_history.clear()
        self.important_notes.clear()

    def _collect(self) -> dict:
        return dict(
            full_name=self.full_name.text().strip(), date_of_birth=self.dob.date().toString("yyyy-MM-dd"),
            gender=self.gender.currentText(), blood_group=self.blood_group.currentText(),
            phone=self.phone.text().strip(), email=self.email.text().strip(), address=self.address.text().strip(),
            city=self.city.text().strip(), state=self.state.text().strip(), pin_code=self.pin_code.text().strip(),
            emergency_contact_name=self.emergency_name.text().strip(),
            emergency_relationship=self.emergency_relationship.text().strip(),
            emergency_phone=self.emergency_phone.text().strip(), allergies=self.allergies.text().strip(),
            existing_conditions=self.existing_conditions.text().strip(),
            previous_surgeries=self.previous_surgeries.text().strip(),
            chronic_conditions=self.chronic_conditions.text().strip(),
            medical_history=self.medical_history.toPlainText().strip(),
            important_notes=self.important_notes.toPlainText().strip(), status="Active",
        )

    def _save(self) -> None:
        data = self._collect()
        for ok, msg in (required(data["full_name"], "Full name"), valid_phone(data["phone"]),
                        valid_email(data["email"], required_field=False), valid_pincode(data["pin_code"])):
            if not ok:
                self.error_label.setText(msg)
                return
        self.error_label.setText("")

        from core.security.auth import get_current_session
        session = get_current_session()
        actor_id = session.user_id if session else None
        actor_role = session.role_name if session else None

        if self.patient:
            try:
                patient_service.update_patient(self.patient["patient_id"], data, actor_id, actor_role)
                self.saved_patient_id = self.patient["patient_id"]
                self.accept()
            except ValueError as exc:
                self.error_label.setText(str(exc))
            return

        duplicates = patient_service.find_possible_duplicates(
            data["phone"], data["email"], data["full_name"], data["date_of_birth"])
        if duplicates:
            dialog = DuplicatePatientDialog(self, duplicates)
            dialog.exec()
            if dialog.result_action == "cancel":
                return
            if dialog.result_action == "view":
                self.saved_patient_id = duplicates[0]["patient_id"]
                self.reject()
                return
            # "create" falls through and creates anyway

        try:
            self.saved_patient_id = patient_service.create_patient(data, actor_id, actor_role)
            self.accept()
        except ValueError as exc:
            self.error_label.setText(str(exc))


class DoctorFormDialog(QDialog):
    """Add/Edit Doctor form with personal, professional and schedule
    sections (spec section 23)."""

    DAY_CODES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def __init__(self, parent, doctor: dict | None = None):
        super().__init__(parent)
        self.doctor = doctor
        self.setWindowTitle("Edit Doctor" if doctor else "Add Doctor")
        self.resize(520, 660)
        self.saved_doctor_id: str | None = None

        outer = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        form = QVBoxLayout(inner)
        form.setSpacing(14)

        form.addWidget(self._section_label("Personal"))
        personal = QFormLayout()
        self.full_name = QLineEdit()
        self.gender = QComboBox()
        self.gender.addItems(["Male", "Female", "Other"])
        self.dob = QDateEdit(calendarPopup=True)
        self.dob.setDisplayFormat("yyyy-MM-dd")
        self.dob.setDate(QDate(1985, 1, 1))
        self.phone = QLineEdit()
        self.email = QLineEdit()
        personal.addRow("Full Name *", self.full_name)
        personal.addRow("Gender", self.gender)
        personal.addRow("Date of Birth", self.dob)
        personal.addRow("Phone", self.phone)
        personal.addRow("Email", self.email)
        form.addLayout(personal)

        form.addWidget(self._section_label("Professional"))
        professional = QFormLayout()
        self.qualification = QLineEdit()
        self.specialization = QComboBox()
        self.specialization.setEditable(True)
        self.specialization.addItems(["General Medicine", "Cardiology", "Dermatology", "Pediatrics",
                                       "Orthopedics", "Neurology", "Gynecology", "ENT"])
        self.department = QLineEdit()
        self.experience_years = QSpinBox()
        self.experience_years.setRange(0, 60)
        self.consultation_fee = QDoubleSpinBox()
        self.consultation_fee.setRange(0, 100000)
        self.consultation_fee.setPrefix("₹ ")
        self.description = QTextEdit()
        self.description.setMaximumHeight(70)
        professional.addRow("Qualification", self.qualification)
        professional.addRow("Specialization *", self.specialization)
        professional.addRow("Department", self.department)
        professional.addRow("Experience (years)", self.experience_years)
        professional.addRow("Consultation Fee", self.consultation_fee)
        professional.addRow("Description", self.description)
        form.addLayout(professional)

        form.addWidget(self._section_label("Schedule"))
        schedule = QFormLayout()
        self.day_checks: dict[str, QCheckBox] = {}
        day_row = QHBoxLayout()
        for day in self.DAY_CODES:
            cb = QCheckBox(day)
            if day in ("Mon", "Tue", "Wed", "Thu", "Fri"):
                cb.setChecked(True)
            self.day_checks[day] = cb
            day_row.addWidget(cb)
        schedule.addRow("Working Days", day_row)
        self.start_time = QLineEdit("09:00")
        self.end_time = QLineEdit("17:00")
        self.break_start = QLineEdit("13:00")
        self.break_end = QLineEdit("14:00")
        self.slot_duration = QSpinBox()
        self.slot_duration.setRange(5, 120)
        self.slot_duration.setValue(15)
        self.slot_duration.setSuffix(" min")
        schedule.addRow("Start Time (HH:MM)", self.start_time)
        schedule.addRow("End Time (HH:MM)", self.end_time)
        schedule.addRow("Break Start", self.break_start)
        schedule.addRow("Break End", self.break_end)
        schedule.addRow("Appointment Duration", self.slot_duration)
        form.addLayout(schedule)

        scroll.setWidget(inner)
        outer.addWidget(scroll)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #DC2626;")
        self.error_label.setWordWrap(True)
        outer.addWidget(self.error_label)

        btn_row = QHBoxLayout()
        cancel_btn = secondary_button("Cancel")
        clear_btn = secondary_button("Clear")
        save_btn = primary_button("Save Doctor")
        cancel_btn.clicked.connect(self.reject)
        clear_btn.clicked.connect(self._clear)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        outer.addLayout(btn_row)

        if doctor:
            self._populate(doctor)

    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("font-weight: 700; color: #0B3D66; font-size: 13px; margin-top: 4px;")
        return label

    def _populate(self, d: dict) -> None:
        self.full_name.setText(d["full_name"])
        if d.get("gender"):
            self.gender.setCurrentText(d["gender"])
        if d.get("date_of_birth"):
            try:
                y, m, dd = (int(x) for x in d["date_of_birth"].split("-"))
                self.dob.setDate(QDate(y, m, dd))
            except ValueError:
                pass
        self.phone.setText(d.get("phone") or "")
        self.email.setText(d.get("email") or "")
        self.qualification.setText(d.get("qualification") or "")
        self.specialization.setCurrentText(d["specialization"])
        self.department.setText(d.get("department_name") or "")
        self.experience_years.setValue(d.get("experience_years") or 0)
        self.consultation_fee.setValue(d.get("consultation_fee") or 0)
        self.description.setPlainText(d.get("description") or "")
        for day in self.DAY_CODES:
            self.day_checks[day].setChecked(day in (d.get("working_days") or ""))
        self.start_time.setText(d.get("start_time") or "09:00")
        self.end_time.setText(d.get("end_time") or "17:00")
        self.break_start.setText(d.get("break_start") or "")
        self.break_end.setText(d.get("break_end") or "")
        self.slot_duration.setValue(d.get("slot_duration_minutes") or 15)

    def _clear(self) -> None:
        for widget in (self.full_name, self.phone, self.email, self.qualification, self.department):
            widget.clear()
        self.description.clear()

    def _collect(self) -> dict:
        working_days = ",".join(day for day, cb in self.day_checks.items() if cb.isChecked())
        return dict(
            full_name=self.full_name.text().strip(), gender=self.gender.currentText(),
            date_of_birth=self.dob.date().toString("yyyy-MM-dd"), phone=self.phone.text().strip(),
            email=self.email.text().strip(), qualification=self.qualification.text().strip(),
            specialization=self.specialization.currentText().strip(), department=self.department.text().strip(),
            experience_years=self.experience_years.value(), consultation_fee=self.consultation_fee.value(),
            description=self.description.toPlainText().strip(), working_days=working_days,
            start_time=self.start_time.text().strip(), end_time=self.end_time.text().strip(),
            break_start=self.break_start.text().strip(), break_end=self.break_end.text().strip(),
            slot_duration_minutes=self.slot_duration.value(), is_active=1,
        )

    def _save(self) -> None:
        data = self._collect()
        ok, msg = required(data["full_name"], "Full name")
        if not ok:
            self.error_label.setText(msg)
            return
        if not data["specialization"]:
            self.error_label.setText("Specialization is required.")
            return
        self.error_label.setText("")

        from core.security.auth import get_current_session
        session = get_current_session()
        actor_id = session.user_id if session else None
        actor_role = session.role_name if session else None
        try:
            if self.doctor:
                doctor_service.update_doctor(self.doctor["doctor_id"], data, actor_id, actor_role)
                self.saved_doctor_id = self.doctor["doctor_id"]
            else:
                self.saved_doctor_id = doctor_service.create_doctor(data, actor_id, actor_role)
            self.accept()
        except ValueError as exc:
            self.error_label.setText(str(exc))
