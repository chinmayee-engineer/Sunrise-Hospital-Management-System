"""Patient's own bills and payment history (spec section 29)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QTabWidget, QVBoxLayout, QWidget

from core.security.auth import Session
from core.services import billing_service
from shared_ui.widgets import EmptyState, StatusBadge, info_message, secondary_button, section_heading


class PatientBillingView(QWidget):
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
        self.layout_root.addWidget(section_heading("Bills & Payments"))
        patient_id = self.session.linked_patient_id

        tabs = QTabWidget()
        tabs.addTab(self._invoices_tab(patient_id), "Invoices")
        tabs.addTab(self._payments_tab(patient_id), "Payment History")
        self.layout_root.addWidget(tabs)

    def _invoices_tab(self, patient_id: str) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        rows = billing_service.list_for_patient(patient_id) if patient_id else []
        if not rows:
            layout.addWidget(EmptyState("💰", "No invoices yet", ""))
        for inv in rows:
            box = QWidget()
            box.setProperty("class", "card")
            box_layout = QHBoxLayout(box)
            text = QLabel(f"<b>{inv['invoice_id']}</b> — {inv['invoice_date']}<br>"
                         f"Total: ₹{inv['total']:.2f}  •  Paid: ₹{inv['amount_paid']:.2f}  •  "
                         f"Balance: ₹{(inv['total']-inv['amount_paid']):.2f}")
            box_layout.addWidget(text, stretch=1)
            box_layout.addWidget(StatusBadge(inv["status"]))
            pdf_btn = secondary_button("Download PDF")
            pdf_btn.clicked.connect(lambda checked, iid=inv["invoice_id"]: self._download(iid))
            box_layout.addWidget(pdf_btn)
            layout.addWidget(box)
        layout.addStretch()
        return widget

    def _payments_tab(self, patient_id: str) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        rows = billing_service.payment_history_for_patient(patient_id) if patient_id else []
        if not rows:
            layout.addWidget(EmptyState("💳", "No payments yet", ""))
        for pay in rows:
            box = QLabel(f"{pay['payment_date']} — ₹{pay['amount']:.2f} via {pay['payment_method']} "
                         f"(Invoice {pay['invoice_id']})")
            box.setStyleSheet("background: white; border: 1px solid #E3E7EC; border-radius: 8px; padding: 10px;")
            layout.addWidget(box)
        layout.addStretch()
        return widget

    def _download(self, invoice_id: str) -> None:
        from core.reports.pdf_reports import generate_invoice_pdf
        invoice = billing_service.get_invoice(invoice_id)
        path = generate_invoice_pdf(invoice)
        info_message(self, "PDF Ready", f"✓ Invoice saved to:\n{path}")
