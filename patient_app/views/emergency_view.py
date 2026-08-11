"""Emergency information: a quick-reference panel of critical medical
facts (spec section 5 - "Emergency Information")."""
from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from core.security.auth import Session
from core.services import patient_service
from core.theme import DANGER, DANGER_BG, NAVY
from shared_ui.widgets import section_heading


class EmergencyView(QWidget):
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
        self.layout_root.addWidget(section_heading("Emergency Information"))

        patient_id = self.session.linked_patient_id
        if not patient_id:
            return
        patient = patient_service.get_patient(patient_id)

        card = QLabel(
            f"<span style='font-size:16px; font-weight:700; color:{NAVY};'>{patient['full_name']}</span><br>"
            f"Blood Group: <b>{patient.get('blood_group') or 'Unknown'}</b><br><br>"
            f"<b>Allergies:</b><br>{patient.get('allergies') or 'None recorded'}<br><br>"
            f"<b>Chronic Conditions:</b><br>{patient.get('chronic_conditions') or 'None recorded'}<br><br>"
            f"<b>Existing Conditions:</b><br>{patient.get('existing_conditions') or 'None recorded'}<br><br>"
            f"<b>Emergency Contact:</b><br>{patient.get('emergency_contact_name') or '-'} "
            f"({patient.get('emergency_relationship') or '-'}) — {patient.get('emergency_phone') or '-'}"
        )
        card.setWordWrap(True)
        card.setStyleSheet(f"background: {DANGER_BG}; border: 1px solid {DANGER}; border-radius: 10px; padding: 18px;")
        self.layout_root.addWidget(card)
        self.layout_root.addStretch()
