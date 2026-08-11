"""Patient dashboard: next appointment, quick stats (spec section 6)."""
from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from core.security.auth import Session
from core.services import appointment_service, billing_service, lab_service, message_service, prescription_service
from core.theme import DANGER, NAVY, SUCCESS, TEAL, TEXT_MUTED, WARNING
from shared_ui.widgets import EmptyState, StatCard, StatusBadge, add_card_shadow, section_heading


class PatientDashboardView(QWidget):
    def __init__(self, session: Session, main_window):
        super().__init__()
        self.session = session
        self.main_window = main_window
        self.layout_root = QVBoxLayout(self)
        self.layout_root.setContentsMargins(24, 20, 24, 24)
        self.layout_root.setSpacing(16)

    def refresh(self, **kwargs) -> None:
        while self.layout_root.count():
            item = self.layout_root.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        patient_id = self.session.linked_patient_id
        if not patient_id:
            self.layout_root.addWidget(QLabel("This account is not linked to a patient record."))
            return

        greeting = QLabel(f"Welcome back, {self.session.full_name.split()[0]} 👋")
        greeting.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {TEAL};")
        self.layout_root.addWidget(greeting)

        all_appts = appointment_service.list_for_patient(patient_id)
        upcoming = [a for a in all_appts if a["status"] in ("Scheduled", "CheckedIn")]
        completed = [a for a in all_appts if a["status"] == "Completed"]
        cancelled = [a for a in all_appts if a["status"] == "Cancelled"]
        rx_count = len(prescription_service.list_for_patient(patient_id))
        lab_count = len(lab_service.list_for_patient(patient_id))
        pending_bills = [i for i in billing_service.list_for_patient(patient_id) if i["status"] in ("Pending", "PartiallyPaid")]
        unread_msgs = sum(c["unread_count"] for c in message_service.conversations_for_patient(patient_id))

        cards = QGridLayout()
        cards.setSpacing(14)
        cards.addWidget(StatCard("Upcoming Appointments", str(len(upcoming)), "", "📅", TEAL), 0, 0)
        cards.addWidget(StatCard("Completed Visits", str(len(completed)), "", "✅", SUCCESS), 0, 1)
        cards.addWidget(StatCard("Cancelled", str(len(cancelled)), "", "✕", DANGER), 0, 2)
        cards.addWidget(StatCard("Active Prescriptions", str(rx_count), "", "💊", NAVY), 0, 3)
        cards.addWidget(StatCard("Lab Reports", str(lab_count), "", "🧪", TEAL), 1, 0)
        cards.addWidget(StatCard("Pending Bills", str(len(pending_bills)), "", "💰", WARNING), 1, 1)
        cards.addWidget(StatCard("Unread Messages", str(unread_msgs), "", "💬", NAVY), 1, 2)
        cards.addWidget(StatCard("Total Appointments", str(len(all_appts)), "", "📋", TEAL), 1, 3)
        self.layout_root.addLayout(cards)

        self.layout_root.addWidget(section_heading("Next Appointment"))
        if upcoming:
            next_appt = sorted(upcoming, key=lambda a: (a["appointment_date"], a["appointment_time"]))[0]
            card = QWidget()
            card.setProperty("class", "card")
            add_card_shadow(card)
            card_layout = QVBoxLayout(card)
            card_layout.addWidget(QLabel(
                f"<b style='font-size:16px; color:{NAVY};'>Dr. {next_appt['doctor_name']}</b><br>"
                f"<span style='color:{TEXT_MUTED};'>{next_appt.get('specialization','')}</span><br><br>"
                f"<b>{next_appt['appointment_date']}</b>  {next_appt['appointment_time']}<br>"
                f"Token: {next_appt['token_number']}"
            ))
            self.layout_root.addWidget(card)
        else:
            self.layout_root.addWidget(EmptyState("📅", "No upcoming appointments",
                                                     "Find a doctor and book your next visit."))
        self.layout_root.addStretch()
