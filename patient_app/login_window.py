"""Patient login screen with self-service registration."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from core.services.user_service import authenticate
from core.theme import SOFT_GRAY, TEAL, TEXT_MUTED, WHITE
from patient_app.registration_dialog import PatientRegistrationDialog
from shared_ui.widgets import add_card_shadow, info_message, link_button, primary_button


class PatientLoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sunrise Hospital - Patient Portal")
        self.resize(980, 620)
        self.setStyleSheet(f"background: {SOFT_GRAY};")
        self.main_window = None
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        brand_panel = QFrame()
        brand_panel.setStyleSheet(f"background: {TEAL};")
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
        subtitle = QLabel("Patient Portal")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #E3F7F7; font-size: 13px; margin-top: 6px;")
        brand_layout.addWidget(icon)
        brand_layout.addWidget(title)
        brand_layout.addWidget(subtitle)
        outer.addWidget(brand_panel)

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

        heading = QLabel("Welcome to your health portal")
        heading.setWordWrap(True)
        heading.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {TEAL};")
        sub = QLabel("Sign in to manage your appointments and records")
        sub.setWordWrap(True)
        sub.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; margin-bottom: 8px;")
        form_layout.addWidget(heading)
        form_layout.addWidget(sub)

        form_layout.addWidget(QLabel("Username"))
        self.username_input = QLineEdit()
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

        register_btn = link_button("New patient? Create an account")
        register_btn.clicked.connect(self._open_registration)
        form_layout.addWidget(register_btn, alignment=Qt.AlignCenter)

        hint = QLabel("Demo account: patient10001 / Patient@123 (or any seeded patient ID digits)")
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
        if session.role_name != "Patient":
            self.error_label.setText("This is a staff account. Please use the Hospital Staff application.")
            return
        self.error_label.setText("")
        from patient_app.main_window import PatientMainWindow
        self.main_window = PatientMainWindow(session)
        self.main_window.show()
        self.close()

    def _open_registration(self) -> None:
        dialog = PatientRegistrationDialog(self)
        if dialog.exec() and dialog.registered_username:
            info_message(self, "Registration Successful",
                          "✓ Your account has been created. You can now sign in.")
            self.username_input.setText(dialog.registered_username)
