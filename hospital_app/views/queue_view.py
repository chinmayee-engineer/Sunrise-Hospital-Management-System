"""Hospital-style token queue management (spec section 9)."""
from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from core.security.auth import Session
from core.services import appointment_service, doctor_service
from core.theme import NAVY, TEAL, TEXT_MUTED
from shared_ui.widgets import EmptyState, StatusBadge, info_message, primary_button, section_heading


class QueueView(QWidget):
    def __init__(self, session: Session, main_window):
        super().__init__()
        self.session = session
        self.main_window = main_window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        header_row = QHBoxLayout()
        header_row.addWidget(section_heading("Queue / Token System"))
        header_row.addStretch()
        layout.addLayout(header_row)

        control_row = QHBoxLayout()
        self.doctor_combo = QComboBox()
        self.doctor_combo.currentIndexChanged.connect(self.refresh)
        control_row.addWidget(QLabel("Doctor:"))
        control_row.addWidget(self.doctor_combo)
        self.call_next_btn = primary_button("Call Next Token")
        self.call_next_btn.clicked.connect(self._call_next)
        control_row.addWidget(self.call_next_btn)
        control_row.addStretch()
        layout.addLayout(control_row)

        self.current_token_label = QLabel("")
        self.current_token_label.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {TEAL};")
        layout.addWidget(self.current_token_label)

        self.queue_container = QVBoxLayout()
        layout.addLayout(self.queue_container)
        layout.addStretch()

    def refresh(self, **kwargs) -> None:
        doctors = doctor_service.search_doctors(active_only=True)
        if self.doctor_combo.count() == 0:
            self.doctor_combo.blockSignals(True)
            for d in doctors:
                self.doctor_combo.addItem(f"Dr. {d['full_name']}", d["doctor_id"])
            self.doctor_combo.blockSignals(False)
        if self.doctor_combo.count() == 0:
            return

        doctor_id = self.doctor_combo.currentData()
        today = datetime.now().strftime("%Y-%m-%d")
        current = appointment_service.current_token(doctor_id, today)
        self.current_token_label.setText(f"🎫 Current Token: {current if current else '— none in consultation —'}")

        while self.queue_container.count():
            item = self.queue_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        queue = appointment_service.queue_for_doctor(doctor_id, today)
        if not queue:
            self.queue_container.addWidget(EmptyState("🎫", "No tokens in the queue today", ""))
            return
        for appt in queue:
            row = QWidget()
            row.setStyleSheet("background: white; border: 1px solid #E3E7EC; border-radius: 8px;")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(14, 10, 14, 10)
            label = QLabel(f"TOKEN {appt['token_number']:>3}     {appt['patient_name']}     "
                           f"({appt['appointment_time']})")
            label.setStyleSheet(f"font-family: Consolas, monospace; color: {NAVY};")
            row_layout.addWidget(label)
            row_layout.addStretch()
            row_layout.addWidget(StatusBadge(appt["status"]))
            self.queue_container.addWidget(row)

    def _call_next(self) -> None:
        if self.doctor_combo.count() == 0:
            return
        doctor_id = self.doctor_combo.currentData()
        result = appointment_service.call_next(doctor_id, actor_user_id=self.session.user_id,
                                                 actor_role=self.session.role_name)
        if result:
            info_message(self, "Next Token Called", f"✓ Token {result['token_number']} ({result['patient_name']}) "
                                                       f"is now in consultation.")
        else:
            info_message(self, "Queue Empty", "No more patients waiting in the queue.")
        self.refresh()
