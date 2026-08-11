"""Administrator settings: user/role management and backup & restore
(spec sections 35, 39)."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox, QDialog, QFileDialog, QFormLayout, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)

from core.security.auth import Session
from core.services import backup_service, user_service
from core.services.user_service import DEFAULT_ROLES
from shared_ui.widgets import confirm, info_message, primary_button, secondary_button, section_heading


class AddUserDialog(QDialog):
    def __init__(self, parent, session: Session):
        super().__init__(parent)
        self.session = session
        self.setWindowTitle("Add Staff User")
        self.resize(360, 320)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.full_name = QLineEdit()
        self.role = QComboBox()
        self.role.addItems([r[0] for r in DEFAULT_ROLES if r[0] != "Patient"])
        self.email = QLineEdit()
        form.addRow("Username", self.username)
        form.addRow("Temporary Password", self.password)
        form.addRow("Full Name", self.full_name)
        form.addRow("Role", self.role)
        form.addRow("Email", self.email)
        layout.addLayout(form)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #DC2626;")
        layout.addWidget(self.error_label)

        btn_row = QHBoxLayout()
        cancel_btn = secondary_button("Cancel")
        save_btn = primary_button("Create User")
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)
        self.saved = False

    def _save(self) -> None:
        if not self.username.text().strip() or not self.password.text() or not self.full_name.text().strip():
            self.error_label.setText("Username, password and full name are required.")
            return
        try:
            user_service.create_user(self.username.text().strip(), self.password.text(),
                                      self.full_name.text().strip(), self.role.currentText(),
                                      email=self.email.text().strip())
            self.saved = True
            self.accept()
        except ValueError as exc:
            self.error_label.setText(str(exc))


class SettingsView(QWidget):
    def __init__(self, session: Session, main_window):
        super().__init__()
        self.session = session
        self.main_window = main_window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)
        layout.addWidget(section_heading("Settings"))

        tabs = QTabWidget()
        tabs.addTab(self._build_users_tab(), "Users & Roles")
        tabs.addTab(self._build_backup_tab(), "Backup & Restore")
        layout.addWidget(tabs)

    def _build_users_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        header_row = QHBoxLayout()
        header_row.addStretch()
        add_btn = primary_button("+ Add Staff User")
        add_btn.clicked.connect(self._add_user)
        header_row.addWidget(add_btn)
        layout.addLayout(header_row)

        self.user_table = QTableWidget(0, 5)
        self.user_table.setHorizontalHeaderLabels(["User ID", "Username", "Full Name", "Role", "Status"])
        self.user_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.user_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.user_table)
        self._refresh_users()
        return widget

    def _refresh_users(self) -> None:
        self.user_table.setRowCount(0)
        for u in user_service.list_users():
            r = self.user_table.rowCount()
            self.user_table.insertRow(r)
            for col, value in enumerate([u["user_id"], u["username"], u["full_name"], u["role_name"]]):
                self.user_table.setItem(r, col, QTableWidgetItem(value))
            self.user_table.setItem(r, 4, QTableWidgetItem("Active" if u["is_active"] else "Inactive"))

    def _add_user(self) -> None:
        dialog = AddUserDialog(self, self.session)
        if dialog.exec() and dialog.saved:
            info_message(self, "User Created", "✓ Staff user created successfully.")
            self._refresh_users()

    def _build_backup_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        btn_row = QHBoxLayout()
        backup_btn = primary_button("Create Backup Now")
        backup_btn.clicked.connect(self._create_backup)
        restore_btn = secondary_button("Restore From File...")
        restore_btn.clicked.connect(self._restore_backup)
        btn_row.addWidget(backup_btn)
        btn_row.addWidget(restore_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.backup_table = QTableWidget(0, 3)
        self.backup_table.setHorizontalHeaderLabels(["Backup ID", "Created At", "File Path"])
        self.backup_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.backup_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.backup_table)
        self._refresh_backups()
        return widget

    def _refresh_backups(self) -> None:
        self.backup_table.setRowCount(0)
        for b in backup_service.list_backups():
            r = self.backup_table.rowCount()
            self.backup_table.insertRow(r)
            for col, value in enumerate([b["backup_id"], b["created_at"], b["file_path"]]):
                self.backup_table.setItem(r, col, QTableWidgetItem(value))

    def _create_backup(self) -> None:
        path = backup_service.create_backup(actor_user_id=self.session.user_id, actor_role=self.session.role_name)
        info_message(self, "Backup Created", f"✓ Backup created: {path}")
        self._refresh_backups()

    def _restore_backup(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Backup File", filter="Database Files (*.db)")
        if not path:
            return
        if not confirm(self, "Restore Backup",
                        "This will overwrite the current database with the selected backup and cannot be undone. "
                        "Continue?"):
            return
        backup_service.restore_backup(path, self.session.user_id, self.session.role_name)
        info_message(self, "Restored", "✓ Database restored. Please restart the application.")
