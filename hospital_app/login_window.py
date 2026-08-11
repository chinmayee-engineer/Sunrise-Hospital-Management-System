"""Staff login screen for the Hospital application."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QVBoxLayout, QWidget,
)

from core.services.user_service import authenticate
from core.theme import NAVY, SOFT_GRAY, TEAL, TEXT_MUTED, WHITE
from shared_ui.widgets import add_card_shadow, primary_button


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sunrise Hospital - Staff Console")
        self.resize(980, 620)
        self.setStyleSheet(f"background: {SOFT_GRAY};")
        self.main_window = None
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Left branding panel
        brand_panel = QFrame()
        brand_panel.setStyleSheet(f"background: {NAVY};")
        brand_panel.setFixedWidth(420)
        brand_layout = QVBoxLayout(brand_panel)
        brand_layout.setAlignment(Qt.AlignCenter)
        brand_layout.setContentsMargins(50, 50, 50, 50)
        icon = QLabel("🏥")
        icon.setStyleSheet("font-size: 56px;")
        icon.setAlignment(Qt.AlignCenter)
        title = QLabel("Sunrise Multispecialty\nHospital")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color: {WHITE}; font-size: 22px; font-weight: 700; margin-top: 12px;")
        subtitle = QLabel("Staff & Doctor Console")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #B7CBE0; font-size: 13px; margin-top: 6px;")
        brand_layout.addWidget(icon)
        brand_layout.addWidget(title)
        brand_layout.addWidget(subtitle)
        outer.addWidget(brand_panel)

        # Right login form
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setAlignment(Qt.AlignCenter)
        right_layout.setContentsMargins(80, 40, 80, 40)

        form_card = QFrame()
        form_card.setProperty("class", "card")
        form_card.setMaximumWidth(380)
        add_card_shadow(form_card)
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(30, 30, 30, 30)
        form_layout.setSpacing(12)

        heading = QLabel("Welcome back")
        heading.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {NAVY};")
        sub = QLabel("Sign in with your staff credentials")
        sub.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; margin-bottom: 8px;")
        form_layout.addWidget(heading)
        form_layout.addWidget(sub)

        form_layout.addWidget(QLabel("Username"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("e.g. admin, dr.priya, reception")
        form_layout.addWidget(self.username_input)

        form_layout.addWidget(QLabel("Password"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self._attempt_login)
        form_layout.addWidget(self.password_input)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #DC2626; font-size: 12px;")
        self.error_label.setWordWrap(True)
        form_layout.addWidget(self.error_label)

        login_btn = primary_button("Sign In")
        login_btn.clicked.connect(self._attempt_login)
        form_layout.addWidget(login_btn)

        hint = QLabel(
            "Demo accounts: admin / Admin@123 · reception / Reception@123\n"
            "dr.priya / Doctor@123 · nurse / Nurse@123 · labstaff / Lab@123"
        )
        hint.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; margin-top: 6px;")
        hint.setWordWrap(True)
        form_layout.addWidget(hint)

        right_layout.addWidget(form_card, alignment=Qt.AlignCenter)
        outer.addWidget(right)

    def _attempt_login(self) -> None:
        username = self.username_input.text().strip()
        password = self.password_input.text()
        if not username or not password:
            self.error_label.setText("Please enter both username and password.")
            return
        session = authenticate(username, password)
        if not session:
            self.error_label.setText("Invalid username or password.")
            return
        if session.role_name == "Patient":
            self.error_label.setText("This account is a patient account. Please use the Patient application.")
            return
        self.error_label.setText("")
        from hospital_app.main_window import HospitalMainWindow
        self.main_window = HospitalMainWindow(session)
        self.main_window.show()
        self.close()
