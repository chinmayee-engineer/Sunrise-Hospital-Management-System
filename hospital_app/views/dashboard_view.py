"""Staff dashboard: today's queue, upcoming appointments, and quick
analytics (spec sections 4, 24)."""
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from core.security.auth import Session
from core.services import analytics_service, appointment_service, consultation_service, lab_service
from core.theme import DANGER, NAVY, SUCCESS, TEAL, TEXT_MUTED, WARNING
from shared_ui.widgets import EmptyState, StatCard, StatusBadge, section_heading


class DashboardView(QWidget):
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

        greeting = QLabel(f"Welcome back, {self.session.full_name.split()[0]} 👋")
        greeting.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {NAVY};")
        self.layout_root.addWidget(greeting)

        today = datetime.now().strftime("%Y-%m-%d")
        appt_stats = analytics_service.appointment_stats(days=1)
        appt_today = appointment_service.list_all(day=today)
        waiting = len([a for a in appt_today if a["status"] in ("Scheduled", "CheckedIn")])
        in_consult = len([a for a in appt_today if a["status"] == "InConsultation"])
        completed = len([a for a in appt_today if a["status"] == "Completed"])
        pending_labs = len(lab_service.list_all(status="Requested")) + len(lab_service.list_all(status="Processing"))

        cards = QGridLayout()
        cards.setSpacing(14)
        cards.addWidget(StatCard("Today's Appointments", str(len(appt_today)), "", "📅", TEAL), 0, 0)
        cards.addWidget(StatCard("Waiting Patients", str(waiting), "", "⏳", WARNING), 0, 1)
        cards.addWidget(StatCard("In Consultation", str(in_consult), "", "🩺", NAVY), 0, 2)
        cards.addWidget(StatCard("Completed Today", str(completed), "", "✅", SUCCESS), 0, 3)
        cards.addWidget(StatCard("Pending Lab Reports", str(pending_labs), "", "🧪", DANGER), 1, 0)
        fin = analytics_service.financial_stats(days=30)
        cards.addWidget(StatCard("Revenue (30 days)", f"₹{fin['revenue_last_period']:.0f}", "", "💰", SUCCESS), 1, 1)
        pstats = analytics_service.patient_stats()
        cards.addWidget(StatCard("Active Patients", str(pstats["total_active"]), "", "👥", TEAL), 1, 2)
        cards.addWidget(StatCard("New Patients (30d)", str(pstats["new_last_30_days"]), "", "🆕", NAVY), 1, 3)
        self.layout_root.addLayout(cards)

        self.layout_root.addWidget(section_heading("Today's Appointments"))
        if not appt_today:
            self.layout_root.addWidget(EmptyState("📅", "No appointments today", "Enjoy the quiet moment."))
        else:
            for appt in appt_today[:8]:
                self.layout_root.addWidget(self._appointment_row(appt))

        self.layout_root.addStretch()

    def _appointment_row(self, appt: dict) -> QWidget:
        row = QWidget()
        row.setStyleSheet("background: white; border: 1px solid #E3E7EC; border-radius: 8px;")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(14, 10, 14, 10)
        info = QLabel(f"Token {appt['token_number']}  •  {appt['appointment_time']}  •  "
                       f"{appt['patient_name']}  →  Dr. {appt['doctor_name']}")
        layout.addWidget(info)
        layout.addStretch()
        layout.addWidget(StatusBadge(appt["status"]))
        return row
