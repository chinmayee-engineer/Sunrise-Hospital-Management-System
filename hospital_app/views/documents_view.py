"""Medical documents browser for staff: search by patient, upload,
categorize, archive (spec section 28)."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox, QDialog, QFileDialog, QFormLayout, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QListWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from core.security.auth import Session
from core.services import document_service, patient_service
from shared_ui.widgets import (
    EmptyState, SearchBox, confirm, error_message, info_message, primary_button,
    secondary_button, section_heading,
)


class UploadDocumentDialog(QDialog):
    def __init__(self, parent, session: Session):
        super().__init__(parent)
        self.session = session
        self.setWindowTitle("Upload Medical Document")
        self.resize(420, 380)
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
        self.doc_type = QComboBox()
        self.doc_type.addItems(document_service.DOCUMENT_TYPES)
        self.title = QLineEdit()
        form.addRow("Document Type", self.doc_type)
        form.addRow("Title", self.title)
        layout.addLayout(form)

        file_row = QHBoxLayout()
        self.file_label = QLabel("No file chosen")
        choose_file_btn = secondary_button("Choose File")
        choose_file_btn.clicked.connect(self._choose_file)
        file_row.addWidget(self.file_label)
        file_row.addWidget(choose_file_btn)
        layout.addLayout(file_row)
        self.file_path = None

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #DC2626;")
        layout.addWidget(self.error_label)

        btn_row = QHBoxLayout()
        cancel_btn = secondary_button("Cancel")
        save_btn = primary_button("Upload")
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _choose_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Document")
        if path:
            self.file_path = path
            self.file_label.setText(path.split("/")[-1])

    def _save(self) -> None:
        if not self.patient_id:
            self.error_label.setText("Please select a patient.")
            return
        if not self.file_path:
            self.error_label.setText("Please choose a file.")
            return
        if not self.title.text().strip():
            self.error_label.setText("Please enter a title.")
            return
        try:
            self.saved_id = document_service.upload_document(
                self.patient_id, self.doc_type.currentText(), self.title.text().strip(), self.file_path,
                self.session.user_id, self.session.role_name)
            self.accept()
        except Exception as exc:  # noqa: BLE001 -- surface any I/O error to the user, not a crash
            self.error_label.setText(f"Unable to upload document: {exc}")


class DocumentsView(QWidget):
    def __init__(self, session: Session, main_window):
        super().__init__()
        self.session = session
        self.main_window = main_window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        header_row = QHBoxLayout()
        header_row.addWidget(section_heading("Medical Documents"))
        header_row.addStretch()
        upload_btn = primary_button("+ Upload Document")
        upload_btn.clicked.connect(self._open_upload)
        header_row.addWidget(upload_btn)
        layout.addLayout(header_row)

        self.search_box = SearchBox("Search by patient ID")
        self.search_box.textChanged.connect(self.refresh)
        layout.addWidget(self.search_box)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Document ID", "Title", "Type", "Uploaded"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)
        self.hint = QLabel("Search by a Patient ID (e.g. P-10001) to view that patient's documents.")
        self.hint.setStyleSheet("color: #6B7280; font-size: 12px;")
        layout.addWidget(self.hint)

    def refresh(self, **kwargs) -> None:
        term = self.search_box.text().strip()
        self.table.setRowCount(0)
        if not term.upper().startswith("P-"):
            return
        rows = document_service.list_for_patient(term.upper())
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            for col, value in enumerate([row["document_id"], row["title"], row["document_type"],
                                          row["uploaded_at"][:10]]):
                self.table.setItem(r, col, QTableWidgetItem(value))

    def _open_upload(self) -> None:
        dialog = UploadDocumentDialog(self, self.session)
        if dialog.exec() and dialog.saved_id:
            info_message(self, "Document Uploaded", "✓ Document uploaded successfully.")
            self.refresh()
