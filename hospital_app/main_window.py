"""Main dashboard shell for the Hospital / Staff application: sidebar
navigation, top bar (search, notifications, user menu) and a stacked
content area (spec section 4)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMenu, QPushButton,
    QScrollArea, QStackedWidget, QStatusBar, QVBoxLayout, QWidget,
)

from core.security.auth import Session, set_current_session
from core.services import notification_service
from core.services.audit_service import log_action
from core.theme import NAVY, WHITE
from shared_ui.widgets import SearchBox

# (key, label with icon, allowed roles; Administrator always allowed)
NAV_ITEMS = [
    ("dashboard", "🏠  Dashboard", ("Administrator", "Doctor", "Receptionist", "Nurse", "LabStaff", "Pharmacist")),
    ("patients", "👥  Patients", ("Administrator", "Doctor", "Receptionist", "Nurse")),
    ("doctors", "🩺  Doctors", ("Administrator", "Receptionist")),
    ("appointments", "📅  Appointments", ("Administrator", "Doctor", "Receptionist", "Nurse")),
    ("queue", "🎫  Queue", ("Administrator", "Doctor", "Receptionist", "Nurse")),
    ("consultations", "🗒️  Consultations", ("Administrator", "Doctor")),
    ("prescriptions", "💊  Prescriptions", ("Administrator", "Doctor", "Pharmacist")),
    ("lab", "🧪  Lab Tests", ("Administrator", "Doctor", "LabStaff")),
    ("documents", "📄  Documents", ("Administrator", "Doctor", "Nurse")),
    ("billing", "💰  Billing", ("Administrator", "Receptionist")),
    ("messages", "💬  Messages", ("Administrator", "Doctor")),
    ("reports", "📊  Reports & Analytics", ("Administrator",)),
    ("audit", "🛡️  Audit Log", ("Administrator",)),
    ("settings", "⚙️  Settings", ("Administrator",)),
]


class HospitalMainWindow(QMainWindow):
    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        set_current_session(session)
        self.setWindowTitle("Sunrise Hospital - Staff Console")
        self.resize(1360, 860)

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
        self.statusBar().showMessage(f"Signed in as {session.full_name} ({session.role_name})")

        self._load_pages()
        self.navigate_to("dashboard")

    # ------------------------------------------------------------ sidebar
    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 10)
        layout.setSpacing(2)

        brand = QLabel("🏥  Sunrise Hospital")
        brand.setObjectName("sidebarBrand")
        layout.addWidget(brand)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons: dict[str, QPushButton] = {}

        for key, label, allowed_roles in NAV_ITEMS:
            if not self.session.has_permission(allowed_roles):
                continue
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

    # ------------------------------------------------------------- topbar
    def _build_topbar(self) -> QWidget:
        topbar = QWidget()
        topbar.setObjectName("topbar")
        layout = QHBoxLayout(topbar)
        layout.setContentsMargins(20, 0, 20, 0)

        self.title_label = QLabel("Dashboard")
        self.title_label.setObjectName("topbarTitle")
        layout.addWidget(self.title_label)
        layout.addStretch()

        self.global_search = SearchBox("Search patients, doctors, appointments...")
        self.global_search.setMaximumWidth(320)
        self.global_search.returnPressed.connect(self._global_search)
        layout.addWidget(self.global_search)

        self.notif_btn = QPushButton("🔔")
        self.notif_btn.setFlat(True)
        self.notif_btn.setCursor(Qt.PointingHandCursor)
        self.notif_btn.clicked.connect(self._show_notifications)
        layout.addWidget(self.notif_btn)

        user_badge = QLabel(f"👤  {self.session.full_name}\n{self.session.role_name}")
        user_badge.setObjectName("userBadge")
        layout.addWidget(user_badge)

        return topbar

    def _global_search(self) -> None:
        term = self.global_search.text().strip()
        if not term:
            return
        self.navigate_to("patients")
        page = self.pages.get("patients")
        if page and hasattr(page, "search_box"):
            page.search_box.setText(term)
            page.refresh()

    def _show_notifications(self) -> None:
        doctor_id = self.session.linked_doctor_id
        notifications = notification_service.for_doctor(doctor_id, limit=15) if doctor_id else []
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
        from hospital_app.login_window import LoginWindow
        self.login_window = LoginWindow()
        self.login_window.show()
        self.close()

    # -------------------------------------------------------------- pages
    def _load_pages(self) -> None:
        from hospital_app.views.dashboard_view import DashboardView
        from hospital_app.views.patients_view import PatientsView
        from hospital_app.views.doctors_view import DoctorsView
        from hospital_app.views.appointments_view import AppointmentsView
        from hospital_app.views.queue_view import QueueView
        from hospital_app.views.consultations_view import ConsultationsView
        from hospital_app.views.prescriptions_view import PrescriptionsView
        from hospital_app.views.lab_view import LabView
        from hospital_app.views.documents_view import DocumentsView
        from hospital_app.views.billing_view import BillingView
        from hospital_app.views.messages_view import MessagesView
        from hospital_app.views.reports_view import ReportsView
        from hospital_app.views.audit_view import AuditView
        from hospital_app.views.settings_view import SettingsView

        registry = {
            "dashboard": DashboardView, "patients": PatientsView, "doctors": DoctorsView,
            "appointments": AppointmentsView, "queue": QueueView, "consultations": ConsultationsView,
            "prescriptions": PrescriptionsView, "lab": LabView, "documents": DocumentsView,
            "billing": BillingView, "messages": MessagesView, "reports": ReportsView,
            "audit": AuditView, "settings": SettingsView,
        }
        for key in self.nav_buttons:
            view_class = registry[key]
            page = view_class(self.session, self)
            self.pages[key] = page
            self.stack.addWidget(page)

    def navigate_to(self, key: str, **kwargs) -> None:
        if key not in self.pages:
            return
        self.nav_buttons[key].setChecked(True)
        label = dict((k, l) for k, l, _ in NAV_ITEMS)[key]
        self.title_label.setText(label.split("  ", 1)[-1])
        page = self.pages[key]
        if hasattr(page, "refresh"):
            page.refresh(**kwargs)
        self.stack.setCurrentWidget(page)

    def open_patient_profile(self, patient_id: str) -> None:
        self.navigate_to("patients", open_patient_id=patient_id)
