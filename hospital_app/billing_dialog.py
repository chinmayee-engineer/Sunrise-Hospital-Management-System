"""Create-invoice and record-payment dialogs for the Billing module
(spec section 29)."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox, QDialog, QDoubleSpinBox, QFormLayout, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QListWidget, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from core.services import billing_service, patient_service
from shared_ui.widgets import SearchBox, primary_button, secondary_button


class CreateInvoiceDialog(QDialog):
    def __init__(self, parent, session, patient_id: str | None = None):
        super().__init__(parent)
        self.session = session
        self.setWindowTitle("Create Invoice")
        self.resize(520, 520)
        self.saved_invoice_id: str | None = None
        layout = QVBoxLayout(self)

        self.patient_id = patient_id
        if not patient_id:
            search = SearchBox("Search patient")
            results = QListWidget()
            results.setMaximumHeight(90)
            layout.addWidget(search)
            layout.addWidget(results)
            self.patient_label = QLabel("No patient selected")
            layout.addWidget(self.patient_label)

            def do_search(text: str) -> None:
                results.clear()
                for p in patient_service.search_patients(text.strip(), limit=8):
                    results.addItem(f"{p['patient_id']} — {p['full_name']}")
                    results.item(results.count() - 1).setData(1000, p["patient_id"])

            def choose(item) -> None:
                self.patient_id = item.data(1000)
                self.patient_label.setText(item.text())

            search.textChanged.connect(do_search)
            results.itemClicked.connect(choose)
        else:
            p = patient_service.get_patient(patient_id)
            layout.addWidget(QLabel(f"Patient: {p['full_name']} ({patient_id})"))

        layout.addWidget(QLabel("Line Items"))
        self.item_table = QTableWidget(0, 4)
        self.item_table.setHorizontalHeaderLabels(["Description", "Category", "Quantity", "Unit Price"])
        self.item_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        layout.addWidget(self.item_table)

        item_btn_row = QHBoxLayout()
        add_item_btn = secondary_button("Add Item")
        add_item_btn.clicked.connect(self._add_item_row)
        remove_item_btn = secondary_button("Remove Selected")
        remove_item_btn.clicked.connect(self._remove_item_row)
        item_btn_row.addWidget(add_item_btn)
        item_btn_row.addWidget(remove_item_btn)
        item_btn_row.addStretch()
        layout.addLayout(item_btn_row)

        form = QFormLayout()
        self.discount = QDoubleSpinBox(); self.discount.setRange(0, 1000000); self.discount.setPrefix("₹ ")
        self.tax = QDoubleSpinBox(); self.tax.setRange(0, 1000000); self.tax.setPrefix("₹ ")
        form.addRow("Discount", self.discount)
        form.addRow("Tax", self.tax)
        layout.addLayout(form)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #DC2626;")
        layout.addWidget(self.error_label)

        btn_row = QHBoxLayout()
        cancel_btn = secondary_button("Cancel")
        save_btn = primary_button("Create Invoice")
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

        self._add_item_row()

    def _add_item_row(self) -> None:
        r = self.item_table.rowCount()
        self.item_table.insertRow(r)
        self.item_table.setItem(r, 0, QTableWidgetItem(""))
        self.item_table.setItem(r, 1, QTableWidgetItem("Consultation"))
        self.item_table.setItem(r, 2, QTableWidgetItem("1"))
        self.item_table.setItem(r, 3, QTableWidgetItem("0"))

    def _remove_item_row(self) -> None:
        row = self.item_table.currentRow()
        if row >= 0:
            self.item_table.removeRow(row)

    def _save(self) -> None:
        if not self.patient_id:
            self.error_label.setText("Please select a patient.")
            return
        items = []
        for r in range(self.item_table.rowCount()):
            desc_item = self.item_table.item(r, 0)
            desc = desc_item.text().strip() if desc_item else ""
            if not desc:
                continue
            try:
                qty = float(self.item_table.item(r, 2).text() or 0)
                price = float(self.item_table.item(r, 3).text() or 0)
            except ValueError:
                self.error_label.setText("Quantity and unit price must be numbers.")
                return
            items.append(dict(description=desc, category=self.item_table.item(r, 1).text().strip(),
                               quantity=qty, unit_price=price))
        if not items:
            self.error_label.setText("Add at least one line item.")
            return
        try:
            self.saved_invoice_id = billing_service.create_invoice(
                self.patient_id, items, discount=self.discount.value(), tax=self.tax.value(),
                actor_user_id=self.session.user_id, actor_role=self.session.role_name)
            self.accept()
        except ValueError as exc:
            self.error_label.setText(str(exc))


class RecordPaymentDialog(QDialog):
    def __init__(self, parent, session, invoice: dict):
        super().__init__(parent)
        self.session = session
        self.invoice = invoice
        self.setWindowTitle(f"Record Payment - {invoice['invoice_id']}")
        self.resize(380, 260)
        layout = QVBoxLayout(self)
        balance = invoice["total"] - invoice["amount_paid"]
        layout.addWidget(QLabel(f"Balance Due: ₹{balance:.2f}"))

        form = QFormLayout()
        self.amount = QDoubleSpinBox()
        self.amount.setRange(0, 10000000)
        self.amount.setPrefix("₹ ")
        self.amount.setValue(balance)
        self.method = QComboBox()
        self.method.addItems(billing_service.PAYMENT_METHODS)
        self.reference = QLineEdit()
        form.addRow("Amount", self.amount)
        form.addRow("Payment Method", self.method)
        form.addRow("Reference No.", self.reference)
        layout.addLayout(form)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #DC2626;")
        layout.addWidget(self.error_label)

        btn_row = QHBoxLayout()
        cancel_btn = secondary_button("Cancel")
        save_btn = primary_button("Record Payment")
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)
        self.saved = False

    def _save(self) -> None:
        try:
            billing_service.record_payment(self.invoice["invoice_id"], self.amount.value(),
                                             self.method.currentText(), self.reference.text().strip(),
                                             actor_user_id=self.session.user_id, actor_role=self.session.role_name)
            self.saved = True
            self.accept()
        except ValueError as exc:
            self.error_label.setText(str(exc))
