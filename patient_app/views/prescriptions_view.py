"""Patient's own prescriptions with PDF download (spec section 6)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from core.security.auth import Session
from core.services import prescription_service
from shared_ui.widgets import EmptyState, info_message, secondary_button, section_heading


class PatientPrescriptionsView(QWidget):
    def __init__(self, session: Session, main_window):
        super().__init__()
        self.session = session
        self.main_window = main_window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)
        layout.addWidget(section_heading("My Prescriptions"))
        self.container = QVBoxLayout()
        layout.addLayout(self.container)
        layout.addStretch()

    def refresh(self, **kwargs) -> None:
        while self.container.count():
            item = self.container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        patient_id = self.session.linked_patient_id
        rows = prescription_service.list_for_patient(patient_id) if patient_id else []
        if not rows:
            self.container.addWidget(EmptyState("💊", "No prescriptions yet", ""))
            return
        for rx in rows:
            full = prescription_service.get_prescription(rx["prescription_id"])
            meds = "<br>".join(f"• {m['medicine_name']} — {m['dosage']}, {m['frequency']}, {m['duration']}"
                                for m in full["items"])
            box = QWidget()
            box.setProperty("class", "card")
            box_layout = QHBoxLayout(box)
            text = QLabel(f"<b>{rx['prescription_date']}</b> — Dr. {rx['doctor_name']}<br>"
                         f"Diagnosis: {rx.get('diagnosis') or '-'}<br>{meds}")
            text.setWordWrap(True)
            box_layout.addWidget(text, stretch=1)
            pdf_btn = secondary_button("Download PDF")
            pdf_btn.clicked.connect(lambda checked, p=full: self._download(p))
            box_layout.addWidget(pdf_btn, alignment=Qt.AlignTop)
            self.container.addWidget(box)

    def _download(self, prescription: dict) -> None:
        from core.reports.pdf_reports import generate_prescription_pdf
        path = generate_prescription_pdf(prescription)
        info_message(self, "PDF Ready", f"✓ Prescription saved to:\n{path}")
