"""Lab test requests and results workflow (spec section 27)."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox, QDialog, QFormLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QListWidget, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
)

from core.security.auth import Session
from core.services import doctor_service, lab_service, patient_service
from shared_ui.widgets import (
    SearchBox, StatusBadge, info_message, primary_button, secondary_button, section_heading,
)


class RequestLabTestDialog(QDialog):
    def __init__(self, parent, session: Session):
        super().__init__(parent)
        self.session = session
        self.setWindowTitle("Request Lab Test")
        self.resize(420, 420)
        self.saved_id: str | None = None
        layout = QVBoxLayout(self)

        search = SearchBox("Search patient")
        results = QListWidget()
        results.setMaximumHeight(90)
        layout.addWidget(search)
        layout.addWidget(results)
        self.patient_id = None
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

        form = QFormLayout()
        self.doctor_combo = QComboBox()
        self.doctors = doctor_service.search_doctors(active_only=True)
        for d in self.doctors:
            self.doctor_combo.addItem(f"Dr. {d['full_name']}", d["doctor_id"])
        self.test_type = QComboBox()
        self.test_type.addItems(lab_service.TEST_TYPES)
        self.test_name = QLineEdit()
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(50)
        form.addRow("Doctor", self.doctor_combo)
        form.addRow("Test Type", self.test_type)
        form.addRow("Test Name", self.test_name)
        form.addRow("Notes", self.notes)
        layout.addLayout(form)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #DC2626;")
        layout.addWidget(self.error_label)

        btn_row = QHBoxLayout()
        cancel_btn = secondary_button("Cancel")
        save_btn = primary_button("Request Test")
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _save(self) -> None:
        if not self.patient_id:
            self.error_label.setText("Please select a patient.")
            return
        if not self.test_name.text().strip():
            self.error_label.setText("Please enter a test name.")
            return
        try:
            self.saved_id = lab_service.request_test(dict(
                patient_id=self.patient_id, doctor_id=self.doctor_combo.currentData(),
                test_type=self.test_type.currentText(), test_name=self.test_name.text().strip(),
                notes=self.notes.toPlainText().strip(),
            ), self.session.user_id, self.session.role_name)
            self.accept()
        except ValueError as exc:
            self.error_label.setText(str(exc))


class EnterResultDialog(QDialog):
    def __init__(self, parent, session: Session, lab_test: dict):
        super().__init__(parent)
        self.session = session
        self.lab_test = lab_test
        self.setWindowTitle(f"Enter Result - {lab_test['test_name']}")
        self.resize(420, 260)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Patient: {lab_test['patient_name']}   Test: {lab_test['test_name']}"))
        self.result_summary = QTextEdit()
        self.result_summary.setPlaceholderText("Result summary...")
        layout.addWidget(self.result_summary)

        btn_row = QHBoxLayout()
        cancel_btn = secondary_button("Cancel")
        save_btn = primary_button("Save Result")
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _save(self) -> None:
        lab_service.enter_result(self.lab_test["lab_test_id"], self.result_summary.toPlainText().strip(),
                                   actor_user_id=self.session.user_id, actor_role=self.session.role_name)
        self.accept()


class LabView(QWidget):
    def __init__(self, session: Session, main_window):
        super().__init__()
        self.session = session
        self.main_window = main_window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        header_row = QHBoxLayout()
        header_row.addWidget(section_heading("Lab Tests"))
        header_row.addStretch()
        request_btn = primary_button("+ Request Lab Test")
        request_btn.clicked.connect(self._open_request)
        header_row.addWidget(request_btn)
        layout.addLayout(header_row)

        filter_row = QHBoxLayout()
        self.search_box = SearchBox("Search patient or test")
        self.search_box.textChanged.connect(self.refresh)
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All"] + lab_service.STATUSES)
        self.status_filter.currentTextChanged.connect(self.refresh)
        filter_row.addWidget(self.search_box)
        filter_row.addWidget(self.status_filter)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Lab ID", "Patient", "Test", "Type", "Requested", "Status", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

    def refresh(self, **kwargs) -> None:
        term = self.search_box.text().strip()
        status = "" if self.status_filter.currentText() == "All" else self.status_filter.currentText()
        rows = lab_service.list_all(status=status, term=term)
        self.table.setRowCount(0)
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            for col, value in enumerate([row["lab_test_id"], row["patient_name"], row["test_name"],
                                          row["test_type"], row["requested_date"]]):
                self.table.setItem(r, col, QTableWidgetItem(value))
            status_container = QWidget()
            status_layout = QHBoxLayout(status_container)
            status_layout.setContentsMargins(4, 2, 4, 2)
            status_layout.addWidget(StatusBadge(row["status"]))
            self.table.setCellWidget(r, 5, status_container)

            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            if row["status"] not in ("Completed", "Cancelled"):
                next_status_map = {"Requested": "Scheduled", "Scheduled": "SampleCollected",
                                    "SampleCollected": "Processing"}
                if row["status"] in next_status_map:
                    advance_btn = secondary_button(f"Mark {next_status_map[row['status']]}")
                    advance_btn.clicked.connect(
                        lambda checked, lid=row["lab_test_id"], s=next_status_map[row["status"]]: self._advance(lid, s))
                    actions_layout.addWidget(advance_btn)
                result_btn = secondary_button("Enter Result")
                result_btn.clicked.connect(lambda checked, l=row: self._enter_result(l))
                actions_layout.addWidget(result_btn)
            self.table.setCellWidget(r, 6, actions)

    def _open_request(self) -> None:
        dialog = RequestLabTestDialog(self, self.session)
        if dialog.exec() and dialog.saved_id:
            info_message(self, "Lab Test Requested", "✓ Lab test requested successfully.")
            self.refresh()

    def _advance(self, lab_test_id: str, status: str) -> None:
        lab_service.update_status(lab_test_id, status, self.session.user_id, self.session.role_name)
        self.refresh()

    def _enter_result(self, lab_test: dict) -> None:
        dialog = EnterResultDialog(self, self.session, lab_test)
        if dialog.exec():
            info_message(self, "Result Saved", "✓ Lab result saved and patient notified.")
            self.refresh()
