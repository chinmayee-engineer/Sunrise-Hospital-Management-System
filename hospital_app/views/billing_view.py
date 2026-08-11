"""Billing module: invoices, payments, PDF invoice/receipt generation
(spec section 29)."""
from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QHeaderView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from core.security.auth import Session
from core.services import billing_service
from hospital_app.billing_dialog import CreateInvoiceDialog, RecordPaymentDialog
from shared_ui.widgets import SearchBox, StatusBadge, info_message, primary_button, secondary_button, section_heading


class BillingView(QWidget):
    def __init__(self, session: Session, main_window):
        super().__init__()
        self.session = session
        self.main_window = main_window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        header_row = QHBoxLayout()
        header_row.addWidget(section_heading("Billing & Invoices"))
        header_row.addStretch()
        create_btn = primary_button("+ Create Invoice")
        create_btn.clicked.connect(self._create_invoice)
        header_row.addWidget(create_btn)
        layout.addLayout(header_row)

        filter_row = QHBoxLayout()
        self.search_box = SearchBox("Search by invoice ID or patient")
        self.search_box.textChanged.connect(self.refresh)
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Pending", "PartiallyPaid", "Paid", "Cancelled", "Refunded"])
        self.status_filter.currentTextChanged.connect(self.refresh)
        filter_row.addWidget(self.search_box)
        filter_row.addWidget(self.status_filter)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Invoice ID", "Patient", "Date", "Total", "Paid", "Status", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

    def refresh(self, **kwargs) -> None:
        term = self.search_box.text().strip()
        status = "" if self.status_filter.currentText() == "All" else self.status_filter.currentText()
        rows = billing_service.list_all(status=status, term=term)
        self.table.setRowCount(0)
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            for col, value in enumerate([row["invoice_id"], row["patient_name"], row["invoice_date"],
                                          f"₹{row['total']:.2f}", f"₹{row['amount_paid']:.2f}"]):
                self.table.setItem(r, col, QTableWidgetItem(value))
            status_container = QWidget()
            status_layout = QHBoxLayout(status_container)
            status_layout.setContentsMargins(4, 2, 4, 2)
            status_layout.addWidget(StatusBadge(row["status"]))
            self.table.setCellWidget(r, 5, status_container)

            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            if row["status"] in ("Pending", "PartiallyPaid"):
                pay_btn = secondary_button("Record Payment")
                pay_btn.clicked.connect(lambda checked, iid=row["invoice_id"]: self._record_payment(iid))
                actions_layout.addWidget(pay_btn)
            pdf_btn = secondary_button("PDF")
            pdf_btn.clicked.connect(lambda checked, iid=row["invoice_id"]: self._generate_invoice_pdf(iid))
            actions_layout.addWidget(pdf_btn)
            self.table.setCellWidget(r, 6, actions)

    def _create_invoice(self) -> None:
        dialog = CreateInvoiceDialog(self, self.session)
        if dialog.exec() and dialog.saved_invoice_id:
            info_message(self, "Invoice Created", "✓ Invoice created successfully.")
            self.refresh()

    def _record_payment(self, invoice_id: str) -> None:
        invoice = billing_service.get_invoice(invoice_id)
        dialog = RecordPaymentDialog(self, self.session, invoice)
        if dialog.exec() and dialog.saved:
            info_message(self, "Payment Recorded", "✓ Payment recorded successfully.")
            self.refresh()

    def _generate_invoice_pdf(self, invoice_id: str) -> None:
        from core.reports.pdf_reports import generate_invoice_pdf
        invoice = billing_service.get_invoice(invoice_id)
        path = generate_invoice_pdf(invoice)
        info_message(self, "PDF Generated", f"✓ Invoice PDF saved to:\n{path}")
