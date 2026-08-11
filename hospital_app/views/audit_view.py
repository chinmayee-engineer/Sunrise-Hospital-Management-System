"""Audit log viewer, Administrator-only (spec section 36)."""
from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QHeaderView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from core.security.auth import Session
from core.services import audit_service
from shared_ui.widgets import SearchBox, section_heading


class AuditView(QWidget):
    def __init__(self, session: Session, main_window):
        super().__init__()
        self.session = session
        self.main_window = main_window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)
        layout.addWidget(section_heading("Audit Log"))

        filter_row = QHBoxLayout()
        self.search_box = SearchBox("Filter by user or role")
        self.search_box.textChanged.connect(self.refresh)
        self.action_box = SearchBox("Filter by action")
        self.action_box.textChanged.connect(self.refresh)
        filter_row.addWidget(self.search_box)
        filter_row.addWidget(self.action_box)
        layout.addLayout(filter_row)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Date/Time", "User", "Role", "Action", "Related Record", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

    def refresh(self, **kwargs) -> None:
        rows = audit_service.recent_logs(limit=500, action_filter=self.action_box.text().strip(),
                                          user_filter=self.search_box.text().strip())
        self.table.setRowCount(0)
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            for col, value in enumerate([row["created_at"], row.get("user_id") or "-", row.get("role_name") or "-",
                                          row["action"], row.get("related_record") or "-",
                                          row.get("description") or ""]):
                self.table.setItem(r, col, QTableWidgetItem(value))
