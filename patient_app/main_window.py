"""Main dashboard shell for the Patient application (spec section 5)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup, QHBoxLayout, QLabel, QMainWindow, QMenu, QPushButton, QScrollArea,
    QStackedWidget, QStatusBar, QVBoxLayout, QWidget,
)

from core.security.auth import Session, set_current_session
from core.services import notification_service
from core.services.audit_service import log_action
from shared_ui.widgets import SearchBox

NAV_ITEMS = [
    ("dashboard", "🏠  Dashboard"),
    ("appointments", "📅  My Appointments"),
    ("find_doctor", "🔍  Find a Doctor"),
    ("history", "🩺  Medical History"),
    ("prescriptions", "💊  Prescriptions"),
    ("lab", "🧪  Lab Reports"),
    ("documents", "📄  Documents"),
    ("billing", "💰  Bills & Payments"),
    ("messages", "💬  Messages"),
    ("profile", "👤  My Profile"),
    ("emergency", "🚑  Emergency Info"),
]


class PatientMainWindow(QMainWindow):
    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        set_current_session(session)
        self.setWindowTitle("Sunrise Hospital - Patient Portal")
        self.resize(1300, 840)

        self.pages: dict[str, QWidget] = {}
        self.stack = QStackedWidget()

        root = QWidget()
        root.setObjectName("rootWidget")
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self._build_sidebar())

        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(0)
        right_col.addWidget(self._build_topbar())
        content_wrap = QScrollArea()
        content_wrap.setWidgetResizable(True)
        content_wrap.setWidget(self.stack)
        right_col.addWidget(content_wrap)
        right_widget = QWidget()
        right_widget.setLayout(right_col)
        root_layout.addWidget(right_widget, stretch=1)

        self.setCentralWidget(root)
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage(f"Signed in as {session.full_name}")

        self._load_pages()
        self.navigate_to("dashboard")

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setStyleSheet(sidebar.styleSheet() + "QWidget#sidebar { background: #0F8B8D; }")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 10)
        layout.setSpacing(2)

        brand = QLabel("🏥  Sunrise Hospital")
        brand.setObjectName("sidebarBrand")
        layout.addWidget(brand)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons: dict[str, QPushButton] = {}
        for key, label in NAV_ITEMS:
            btn = QPushButton(label)
            btn.setProperty("class", "navButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self.navigate_to(k))
            layout.addWidget(btn)
            self.nav_group.addButton(btn)
            self.nav_buttons[key] = btn

        layout.addStretch()
        logout_btn = QPushButton("🚪  Logout")
        logout_btn.setProperty("class", "navButton")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self._logout)
        layout.addWidget(logout_btn)
        return sidebar

    def _build_topbar(self) -> QWidget:
        topbar = QWidget()
        topbar.setObjectName("topbar")
        layout = QHBoxLayout(topbar)
        layout.setContentsMargins(20, 0, 20, 0)

        self.title_label = QLabel("Dashboard")
        self.title_label.setObjectName("topbarTitle")
        layout.addWidget(self.title_label)
        layout.addStretch()

        self.notif_btn = QPushButton("🔔")
        self.notif_btn.setFlat(True)
        self.notif_btn.setCursor(Qt.PointingHandCursor)
        self.notif_btn.clicked.connect(self._show_notifications)
        layout.addWidget(self.notif_btn)

        user_badge = QLabel(f"👤  {self.session.full_name}")
        user_badge.setObjectName("userBadge")
        layout.addWidget(user_badge)
        return topbar

    def _show_notifications(self) -> None:
        notifications = notification_service.for_patient(self.session.linked_patient_id, limit=15)
        menu = QMenu(self)
        if not notifications:
            menu.addAction("No notifications").setEnabled(False)
        for n in notifications:
            action = menu.addAction(("● " if not n["is_read"] else "  ") + n["title"])
            action.triggered.connect(lambda checked, nid=n["notification_id"]: notification_service.mark_read(nid))
        menu.exec(self.notif_btn.mapToGlobal(self.notif_btn.rect().bottomLeft()))

    def _logout(self) -> None:
        log_action(self.session.user_id, self.session.role_name, "Logout", self.session.user_id, "")
        set_current_session(None)
        from patient_app.login_window import PatientLoginWindow
        self.login_window = PatientLoginWindow()
        self.login_window.show()
        self.close()

    def _load_pages(self) -> None:
        from patient_app.views.dashboard_view import PatientDashboardView
        from patient_app.views.appointments_view import PatientAppointmentsView
        from patient_app.views.find_doctor_view import FindDoctorView
        from patient_app.views.history_view import HistoryView
        from patient_app.views.prescriptions_view import PatientPrescriptionsView
        from patient_app.views.lab_view import PatientLabView
        from patient_app.views.documents_view import PatientDocumentsView
        from patient_app.views.billing_view import PatientBillingView
        from patient_app.views.messages_view import PatientMessagesView
        from patient_app.views.profile_view import ProfileView
        from patient_app.views.emergency_view import EmergencyView

        registry = {
            "dashboard": PatientDashboardView, "appointments": PatientAppointmentsView,
            "find_doctor": FindDoctorView, "history": HistoryView, "prescriptions": PatientPrescriptionsView,
            "lab": PatientLabView, "documents": PatientDocumentsView, "billing": PatientBillingView,
            "messages": PatientMessagesView, "profile": ProfileView, "emergency": EmergencyView,
        }
        for key, view_class in registry.items():
            page = view_class(self.session, self)
            self.pages[key] = page
            self.stack.addWidget(page)

    def navigate_to(self, key: str, **kwargs) -> None:
        if key not in self.pages:
            return
        self.nav_buttons[key].setChecked(True)
        label = dict(NAV_ITEMS)[key]
        self.title_label.setText(label.split("  ", 1)[-1])
        page = self.pages[key]
        if hasattr(page, "refresh"):
            page.refresh(**kwargs)
        self.stack.setCurrentWidget(page)
