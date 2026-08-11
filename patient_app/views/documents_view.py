"""Patient's own uploaded/received medical documents (spec section 28)."""
from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from core.security.auth import Session
from core.services import document_service
from shared_ui.widgets import EmptyState, section_heading


class PatientDocumentsView(QWidget):
    def __init__(self, session: Session, main_window):
        super().__init__()
        self.session = session
        self.main_window = main_window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)
        layout.addWidget(section_heading("My Documents"))
        self.container = QVBoxLayout()
        layout.addLayout(self.container)
        layout.addStretch()

    def refresh(self, **kwargs) -> None:
        while self.container.count():
            item = self.container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        patient_id = self.session.linked_patient_id
        rows = document_service.list_for_patient(patient_id) if patient_id else []
        if not rows:
            self.container.addWidget(EmptyState("📄", "No documents yet", ""))
            return
        for doc in rows:
            box = QLabel(f"<b>{doc['title']}</b> ({doc['document_type']}) — {doc['uploaded_at'][:10]}")
            box.setStyleSheet("background: white; border: 1px solid #E3E7EC; border-radius: 8px; padding: 10px;")
            self.container.addWidget(box)
