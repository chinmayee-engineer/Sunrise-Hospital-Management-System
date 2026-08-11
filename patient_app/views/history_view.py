"""Medical History: previous consultations + medical timeline
(spec sections 15-16)."""
from __future__ import annotations

from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from core.security.auth import Session
from core.services import consultation_service
from core.theme import NAVY, TEAL
from shared_ui.widgets import EmptyState, section_heading


class HistoryView(QWidget):
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
        self.layout_root.addWidget(section_heading("Medical History"))

        patient_id = self.session.linked_patient_id
        tabs = QTabWidget()
        tabs.addTab(self._consultations_tab(patient_id), "Previous Consultations")
        tabs.addTab(self._timeline_tab(patient_id), "Medical Timeline")
        self.layout_root.addWidget(tabs)

    def _consultations_tab(self, patient_id: str) -> QWidget:
        from PySide6.QtWidgets import QLabel
        widget = QWidget()
        layout = QVBoxLayout(widget)
        rows = consultation_service.history_for_patient(patient_id) if patient_id else []
        if not rows:
            layout.addWidget(EmptyState("🩺", "No consultation history yet", ""))
        for c in rows:
            box = QLabel(
                f"<b>{c['consultation_date']}</b><br>Dr. {c['doctor_name']} — {c.get('specialization','')}<br><br>"
                f"<b>Reason:</b><br>{c.get('chief_complaint') or '-'}<br><br>"
                f"<b>Diagnosis:</b><br>{c.get('diagnosis') or '-'}<br><br>"
                f"<b>Symptoms:</b><br>{c.get('symptoms') or '-'}<br><br>"
                f"<b>Vitals:</b><br>BP: {c.get('blood_pressure') or '-'}  "
                f"Temperature: {c.get('temperature') or '-'}°F  Heart Rate: {c.get('heart_rate') or '-'}<br><br>"
                f"<b>Treatment:</b><br>{c.get('treatment') or '-'}<br><br>"
                f"<b>Follow-up:</b><br>{c.get('follow_up_date') or '-'}"
            )
            box.setWordWrap(True)
            box.setStyleSheet("background: white; border: 1px solid #E3E7EC; border-radius: 8px; padding: 12px;")
            layout.addWidget(box)
        layout.addStretch()
        return widget

    def _timeline_tab(self, patient_id: str) -> QWidget:
        from PySide6.QtWidgets import QLabel
        widget = QWidget()
        layout = QVBoxLayout(widget)
        events = consultation_service.medical_timeline(patient_id) if patient_id else []
        if not events:
            layout.addWidget(EmptyState("🕒", "No medical timeline yet", ""))
        current_date = None
        for event in events:
            if event["date"] != current_date:
                current_date = event["date"]
                date_label = QLabel(f"<b>{current_date}</b>")
                date_label.setStyleSheet(f"color: {NAVY}; margin-top: 10px; font-size: 14px;")
                layout.addWidget(date_label)
            row = QLabel(f"├── {event['type']}: {event['summary']}")
            row.setStyleSheet(f"color: {TEAL}; margin-left: 10px;")
            layout.addWidget(row)
        layout.addStretch()
        return widget
