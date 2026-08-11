"""Consultations module: start a new consultation (with previous
consultation summary shown automatically), record vitals, diagnosis,
treatment, and browse consultation history (spec sections 16-20)."""
from __future__ import annotations

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox, QDateEdit, QDialog, QDoubleSpinBox, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QSpinBox, QTextEdit, QVBoxLayout, QWidget,
)

from core.security.auth import Session
from core.services import consultation_service, doctor_service, lab_service, patient_service, prescription_service
from core.theme import NAVY, TEAL, TEXT_MUTED, WARNING_BG
from hospital_app.prescription_dialog import PrescriptionDialog
from shared_ui.widgets import (
    EmptyState, error_message, info_message, primary_button, secondary_button, section_heading,
)


class NewConsultationDialog(QDialog):
    def __init__(self, parent, session: Session, patient_id: str, doctor_id: str | None = None,
                 appointment_id: str | None = None):
        super().__init__(parent)
        self.session = session
        self.patient = patient_service.get_patient(patient_id)
        self.appointment_id = appointment_id
        self.setWindowTitle(f"New Consultation - {self.patient['full_name']}")
        self.resize(600, 700)
        self.saved_consultation_id: str | None = None

        outer = QVBoxLayout(self)

        summary_header = QLabel(
            f"<b>{self.patient['full_name']}</b> — "
            f"{patient_service.calculate_age(self.patient['date_of_birth'])} yrs, {self.patient['gender']}, "
            f"Blood Group {self.patient.get('blood_group') or '-'}<br>"
            f"<span style='color:#DC2626;'>Allergies: {self.patient.get('allergies') or 'None recorded'}</span>  "
            f"Conditions: {self.patient.get('existing_conditions') or 'None recorded'}"
        )
        summary_header.setWordWrap(True)
        outer.addWidget(summary_header)

        last = consultation_service.last_consultation(patient_id)
        if last:
            prev = QLabel(
                f"<b>Previous Consultation Summary</b><br>"
                f"Date: {last['consultation_date']}  •  Doctor: Dr. {last['doctor_name']}<br>"
                f"Diagnosis: {last.get('diagnosis') or '-'}<br>"
                f"Previous Symptoms: {last.get('symptoms') or '-'}<br>"
                f"Previous Treatment: {last.get('treatment') or '-'}<br>"
                f"Follow-up: {last.get('follow_up_date') or '-'}"
            )
            prev.setWordWrap(True)
            prev.setStyleSheet(f"background: {WARNING_BG}; border-radius: 8px; padding: 10px;")
            outer.addWidget(prev)
        else:
            outer.addWidget(QLabel("This is the patient's first recorded consultation."))

        outer.addWidget(section_heading("Current Consultation"))
        form = QFormLayout()

        self.doctor_combo = QComboBox()
        self.doctors = doctor_service.search_doctors(active_only=True)
        for d in self.doctors:
            self.doctor_combo.addItem(f"Dr. {d['full_name']}", d["doctor_id"])
        if doctor_id:
            idx = next((i for i, d in enumerate(self.doctors) if d["doctor_id"] == doctor_id), -1)
            if idx >= 0:
                self.doctor_combo.setCurrentIndex(idx)
        elif session.linked_doctor_id:
            idx = next((i for i, d in enumerate(self.doctors) if d["doctor_id"] == session.linked_doctor_id), -1)
            if idx >= 0:
                self.doctor_combo.setCurrentIndex(idx)
        form.addRow("Doctor", self.doctor_combo)

        self.chief_complaint = QLineEdit()
        self.symptoms = QLineEdit()
        form.addRow("Chief Complaint", self.chief_complaint)
        form.addRow("Symptoms", self.symptoms)

        vitals_row = QHBoxLayout()
        self.temperature = QDoubleSpinBox(); self.temperature.setRange(90, 110); self.temperature.setValue(98.6)
        self.bp = QLineEdit(); self.bp.setPlaceholderText("120/80")
        self.heart_rate = QSpinBox(); self.heart_rate.setRange(30, 220)
        self.resp_rate = QSpinBox(); self.resp_rate.setRange(5, 60)
        self.spo2 = QDoubleSpinBox(); self.spo2.setRange(50, 100); self.spo2.setValue(98)
        vitals_row.addWidget(QLabel("Temp (°F)")); vitals_row.addWidget(self.temperature)
        vitals_row.addWidget(QLabel("BP")); vitals_row.addWidget(self.bp)
        vitals_row.addWidget(QLabel("HR")); vitals_row.addWidget(self.heart_rate)
        form.addRow("Vitals", vitals_row)
        vitals_row2 = QHBoxLayout()
        vitals_row2.addWidget(QLabel("RR")); vitals_row2.addWidget(self.resp_rate)
        vitals_row2.addWidget(QLabel("SpO2 %")); vitals_row2.addWidget(self.spo2)
        form.addRow("", vitals_row2)

        self.weight = QDoubleSpinBox(); self.weight.setRange(0, 300)
        self.height = QDoubleSpinBox(); self.height.setRange(0, 250)
        weight_row = QHBoxLayout()
        weight_row.addWidget(QLabel("Weight (kg)")); weight_row.addWidget(self.weight)
        weight_row.addWidget(QLabel("Height (cm)")); weight_row.addWidget(self.height)
        form.addRow("Body Metrics", weight_row)

        self.physical_exam = QTextEdit(); self.physical_exam.setMaximumHeight(50)
        self.diagnosis = QLineEdit()
        self.treatment = QTextEdit(); self.treatment.setMaximumHeight(50)
        self.doctor_notes = QTextEdit(); self.doctor_notes.setMaximumHeight(50)
        self.follow_up = QDateEdit(calendarPopup=True); self.follow_up.setDisplayFormat("yyyy-MM-dd")
        self.follow_up.setDate(QDate.currentDate().addDays(7))
        form.addRow("Physical Examination", self.physical_exam)
        form.addRow("Diagnosis", self.diagnosis)
        form.addRow("Treatment", self.treatment)
        form.addRow("Doctor Notes", self.doctor_notes)
        form.addRow("Follow-up Date", self.follow_up)
        outer.addLayout(form)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #DC2626;")
        outer.addWidget(self.error_label)

        btn_row = QHBoxLayout()
        cancel_btn = secondary_button("Cancel")
        save_btn = primary_button("Complete Consultation")
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        outer.addLayout(btn_row)

    def _save(self) -> None:
        if self.doctor_combo.count() == 0:
            self.error_label.setText("No active doctors available.")
            return
        data = dict(
            appointment_id=self.appointment_id, patient_id=self.patient["patient_id"],
            doctor_id=self.doctor_combo.currentData(), chief_complaint=self.chief_complaint.text().strip(),
            symptoms=self.symptoms.text().strip(), temperature=self.temperature.value(),
            blood_pressure=self.bp.text().strip(), heart_rate=self.heart_rate.value(),
            respiratory_rate=self.resp_rate.value(), oxygen_saturation=self.spo2.value(),
            weight_kg=self.weight.value() or None, height_cm=self.height.value() or None,
            physical_examination=self.physical_exam.toPlainText().strip(), diagnosis=self.diagnosis.text().strip(),
            treatment=self.treatment.toPlainText().strip(), doctor_notes=self.doctor_notes.toPlainText().strip(),
            follow_up_date=self.follow_up.date().toString("yyyy-MM-dd"),
        )
        try:
            self.saved_consultation_id = consultation_service.create_consultation(
                data, self.session.user_id, self.session.role_name)
            self.accept()
        except ValueError as exc:
            self.error_label.setText(str(exc))


class ConsultationsView(QWidget):
    def __init__(self, session: Session, main_window):
        super().__init__()
        self.session = session
        self.main_window = main_window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        header_row = QHBoxLayout()
        header_row.addWidget(section_heading("Consultations"))
        header_row.addStretch()
        new_btn = primary_button("+ New Consultation")
        new_btn.clicked.connect(self._open_new_consultation)
        header_row.addWidget(new_btn)
        layout.addLayout(header_row)

        self.list_container = QVBoxLayout()
        layout.addLayout(self.list_container)
        layout.addStretch()

    def refresh(self, **kwargs) -> None:
        while self.list_container.count():
            item = self.list_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        doctor_id = self.session.linked_doctor_id
        rows = (consultation_service.history_for_doctor(doctor_id) if doctor_id
                else self._all_recent_consultations())
        if not rows:
            self.list_container.addWidget(EmptyState("🩺", "No consultations recorded yet",
                                                        "Start a new consultation to begin."))
            return
        for c in rows[:40]:
            box = QLabel(
                f"<b>{c['consultation_date']}</b> — {c.get('patient_name','')}"
                f"{' with Dr. ' + c['doctor_name'] if 'doctor_name' in c and not doctor_id else ''}<br>"
                f"Diagnosis: {c.get('diagnosis') or '-'}"
            )
            box.setStyleSheet("background: white; border: 1px solid #E3E7EC; border-radius: 8px; padding: 10px;")
            self.list_container.addWidget(box)

    def _all_recent_consultations(self) -> list[dict]:
        from core.database.db import query_all
        return query_all(
            """SELECT c.*, p.full_name AS patient_name, d.full_name AS doctor_name FROM consultations c
               JOIN patients p ON p.patient_id = c.patient_id
               JOIN doctors d ON d.doctor_id = c.doctor_id
               ORDER BY c.consultation_date DESC LIMIT 60""")

    def _open_new_consultation(self) -> None:
        from shared_ui.widgets import SearchBox
        from PySide6.QtWidgets import QDialog, QListWidget

        picker = QDialog(self)
        picker.setWindowTitle("Select Patient")
        picker.resize(420, 400)
        layout = QVBoxLayout(picker)
        search = SearchBox("Search patient by name, ID or phone")
        results = QListWidget()
        layout.addWidget(search)
        layout.addWidget(results)

        def do_search(text: str) -> None:
            results.clear()
            if len(text.strip()) < 1:
                return
            for p in patient_service.search_patients(text.strip(), limit=15):
                results.addItem(f"{p['patient_id']} — {p['full_name']} ({p['phone']})")
                results.item(results.count() - 1).setData(1000, p["patient_id"])

        search.textChanged.connect(do_search)
        do_search("")
        selected = {"patient_id": None}

        def choose(item) -> None:
            selected["patient_id"] = item.data(1000)
            picker.accept()

        results.itemDoubleClicked.connect(choose)
        picker.exec()

        if not selected["patient_id"]:
            return
        dialog = NewConsultationDialog(self, self.session, selected["patient_id"],
                                        doctor_id=self.session.linked_doctor_id)
        if dialog.exec() and dialog.saved_consultation_id:
            info_message(self, "Consultation Saved", "✓ Consultation saved successfully.")
            self._offer_prescription(dialog.saved_consultation_id, selected["patient_id"],
                                      dialog.doctor_combo.currentData())
            self.refresh()

    def _offer_prescription(self, consultation_id: str, patient_id: str, doctor_id: str) -> None:
        from shared_ui.widgets import confirm
        if confirm(self, "Add Prescription?", "Would you like to create a prescription for this consultation?"):
            dialog = PrescriptionDialog(self, patient_id, doctor_id, consultation_id)
            if dialog.exec() and dialog.saved_prescription_id:
                info_message(self, "Prescription Saved", "✓ Prescription created successfully.")
