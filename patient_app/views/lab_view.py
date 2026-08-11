"""Patient's own lab reports (spec section 27)."""
from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from core.security.auth import Session
from core.services import lab_service
from shared_ui.widgets import EmptyState, StatusBadge, section_heading


class PatientLabView(QWidget):
    def __init__(self, session: Session, main_window):
        super().__init__()
        self.session = session
        self.main_window = main_window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)
        layout.addWidget(section_heading("Lab Reports"))
        self.container = QVBoxLayout()
        layout.addLayout(self.container)
        layout.addStretch()

    def refresh(self, **kwargs) -> None:
        while self.container.count():
            item = self.container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        patient_id = self.session.linked_patient_id
        rows = lab_service.list_for_patient(patient_id) if patient_id else []
        if not rows:
            self.container.addWidget(EmptyState("🧪", "No lab reports yet", ""))
            return
        for lab in rows:
            box = QWidget()
            box.setProperty("class", "card")
            layout = QHBoxLayout(box)
            text = QLabel(f"<b>{lab['test_name']}</b> ({lab['test_type']})<br>"
                         f"Requested by Dr. {lab['doctor_name']} on {lab['requested_date']}<br>"
                         f"{('Result: ' + lab['result_summary']) if lab.get('result_summary') else 'Awaiting result'}")
            text.setWordWrap(True)
            layout.addWidget(text, stretch=1)
            layout.addWidget(StatusBadge(lab["status"]))
            self.container.addWidget(box)
