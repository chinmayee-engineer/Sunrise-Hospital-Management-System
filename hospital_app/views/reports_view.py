"""Reports & Analytics dashboard, plus Excel export (spec sections 32, 34)."""
from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from core.security.auth import Session
from core.services import analytics_service, appointment_service, billing_service, doctor_service, patient_service
from core.theme import NAVY, SUCCESS, TEAL, WARNING
from shared_ui.widgets import StatCard, primary_button, secondary_button, section_heading


class ReportsView(QWidget):
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

        header_row = QHBoxLayout()
        header_row.addWidget(section_heading("Reports & Analytics"))
        header_row.addStretch()
        export_btn = primary_button("Export Analytics (Excel)")
        export_btn.clicked.connect(self._export_analytics)
        header_row.addWidget(export_btn)
        self.layout_root.addLayout(header_row)

        pstats = analytics_service.patient_stats()
        astats = analytics_service.appointment_stats(days=30)
        fstats = analytics_service.financial_stats(days=30)

        cards = QGridLayout()
        cards.setSpacing(14)
        cards.addWidget(StatCard("Active Patients", str(pstats["total_active"]), "", "👥", TEAL), 0, 0)
        cards.addWidget(StatCard("New Patients (30d)", str(pstats["new_last_30_days"]), "", "🆕", NAVY), 0, 1)
        cards.addWidget(StatCard("Returning Patients", str(pstats["returning"]), "", "🔁", TEAL), 0, 2)
        cards.addWidget(StatCard("Appointments (30d)", str(astats["total"]), "", "📅", NAVY), 0, 3)
        cards.addWidget(StatCard("Revenue (30d)", f"₹{fstats['revenue_last_period']:.0f}", "", "💰", SUCCESS), 1, 0)
        cards.addWidget(StatCard("Pending Amount", f"₹{fstats['pending_amount']:.0f}", "", "⏳", WARNING), 1, 1)
        cards.addWidget(StatCard("Paid Invoices", str(fstats["paid_invoices"]), "", "✅", SUCCESS), 1, 2)
        cards.addWidget(StatCard("Pending Invoices", str(fstats["pending_invoices"]), "", "🧾", WARNING), 1, 3)
        self.layout_root.addLayout(cards)

        self.layout_root.addWidget(section_heading("Appointments by Status (30 days)"))
        for status, count in astats["by_status"].items():
            self.layout_root.addWidget(self._bar_row(status, count, max(astats["by_status"].values() or [1])))

        self.layout_root.addWidget(section_heading("Doctor Workload (30 days)"))
        for d in analytics_service.doctor_workload(days=30)[:10]:
            row = QLabel(f"Dr. {d['full_name']} ({d['specialization']}) — "
                         f"{d['appointment_count'] or 0} appointments, {d['completed_count'] or 0} completed")
            self.layout_root.addWidget(row)

        self.layout_root.addWidget(section_heading("Export Data"))
        export_row = QHBoxLayout()
        for label, fn in [
            ("Patients", self._export_patients), ("Doctors", self._export_doctors),
            ("Appointments", self._export_appointments), ("Billing", self._export_billing),
        ]:
            btn = secondary_button(f"Export {label}")
            btn.clicked.connect(fn)
            export_row.addWidget(btn)
        export_row.addStretch()
        self.layout_root.addLayout(export_row)
        self.layout_root.addStretch()

    def _bar_row(self, label: str, count: int, max_value: int) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        name = QLabel(label)
        name.setFixedWidth(120)
        layout.addWidget(name)
        bar = QLabel()
        width = int(200 * (count / max_value)) if max_value else 0
        bar.setFixedSize(max(width, 4), 14)
        bar.setStyleSheet(f"background: {TEAL}; border-radius: 3px;")
        layout.addWidget(bar)
        layout.addWidget(QLabel(str(count)))
        layout.addStretch()
        return row

    def _export_analytics(self) -> None:
        from core.reports.excel_reports import export_analytics
        from shared_ui.widgets import info_message
        path = export_analytics(analytics_service.patient_stats(), analytics_service.appointment_stats(),
                                  analytics_service.doctor_workload(), analytics_service.financial_stats())
        info_message(self, "Exported", f"✓ Analytics exported to:\n{path}")

    def _export_patients(self) -> None:
        from core.reports.excel_reports import export_rows
        from shared_ui.widgets import info_message
        rows = patient_service.search_patients()
        path = export_rows("patients", ["patient_id", "full_name", "date_of_birth", "gender", "phone", "email",
                                          "status", "registration_date"], rows)
        info_message(self, "Exported", f"✓ Patients exported to:\n{path}")

    def _export_doctors(self) -> None:
        from core.reports.excel_reports import export_rows
        from shared_ui.widgets import info_message
        rows = doctor_service.search_doctors(active_only=False)
        path = export_rows("doctors", ["doctor_id", "full_name", "specialization", "department_name",
                                         "experience_years", "consultation_fee"], rows)
        info_message(self, "Exported", f"✓ Doctors exported to:\n{path}")

    def _export_appointments(self) -> None:
        from core.reports.excel_reports import export_rows
        from shared_ui.widgets import info_message
        rows = appointment_service.list_all(limit=2000)
        path = export_rows("appointments", ["appointment_id", "patient_name", "doctor_name", "appointment_date",
                                              "appointment_time", "status", "token_number"], rows)
        info_message(self, "Exported", f"✓ Appointments exported to:\n{path}")

    def _export_billing(self) -> None:
        from core.reports.excel_reports import export_rows
        from shared_ui.widgets import info_message
        rows = billing_service.list_all(limit=2000)
        path = export_rows("billing", ["invoice_id", "patient_name", "invoice_date", "total", "amount_paid",
                                         "status"], rows)
        info_message(self, "Exported", f"✓ Billing exported to:\n{path}")
