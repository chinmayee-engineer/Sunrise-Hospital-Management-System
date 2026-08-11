"""Shared professional healthcare visual theme (spec section 3) used by
both the patient and hospital applications so they feel like one product."""
from __future__ import annotations

NAVY = "#0B3D66"
NAVY_DARK = "#082A47"
MEDICAL_BLUE = "#2E75B6"
TEAL = "#0F8B8D"
TEAL_LIGHT = "#E6F5F5"
WHITE = "#FFFFFF"
SOFT_GRAY = "#F4F6F8"
BORDER_GRAY = "#E3E7EC"
TEXT_DARK = "#1F2937"
TEXT_MUTED = "#6B7280"
SUCCESS = "#16A34A"
SUCCESS_BG = "#E9F9EF"
WARNING = "#D97706"
WARNING_BG = "#FEF3E2"
DANGER = "#DC2626"
DANGER_BG = "#FDEAEA"
INFO = "#2563EB"

FONT_FAMILY = "Segoe UI, -apple-system, Helvetica, Arial, sans-serif"

STATUS_COLORS = {
    "Scheduled": (INFO, "#EAF1FD"),
    "CheckedIn": (TEAL, TEAL_LIGHT),
    "InConsultation": (WARNING, WARNING_BG),
    "Completed": (SUCCESS, SUCCESS_BG),
    "Cancelled": (DANGER, DANGER_BG),
    "NoShow": (TEXT_MUTED, SOFT_GRAY),
    "Active": (SUCCESS, SUCCESS_BG),
    "Archived": (TEXT_MUTED, SOFT_GRAY),
    "Pending": (WARNING, WARNING_BG),
    "PartiallyPaid": (INFO, "#EAF1FD"),
    "Paid": (SUCCESS, SUCCESS_BG),
    "Refunded": (TEXT_MUTED, SOFT_GRAY),
    "Requested": (INFO, "#EAF1FD"),
    "Processing": (WARNING, WARNING_BG),
    "SampleCollected": (MEDICAL_BLUE, "#EAF1FD"),
}


def app_stylesheet() -> str:
    return f"""
    * {{
        font-family: {FONT_FAMILY};
    }}
    QMainWindow, QWidget#rootWidget {{
        background: {SOFT_GRAY};
    }}
    QWidget {{
        color: {TEXT_DARK};
        font-size: 13px;
    }}

    /* ---- Sidebar ---- */
    QWidget#sidebar {{
        background: {NAVY};
        min-width: 230px;
        max-width: 230px;
    }}
    QLabel#sidebarBrand {{
        color: {WHITE};
        font-size: 16px;
        font-weight: 700;
        padding: 20px 18px 14px 18px;
    }}
    QPushButton.navButton {{
        background: transparent;
        color: #D9E4F1;
        border: none;
        text-align: left;
        padding: 11px 18px;
        font-size: 13px;
        border-radius: 0px;
    }}
    QPushButton.navButton:hover {{
        background: {NAVY_DARK};
        color: {WHITE};
    }}
    QPushButton.navButton:checked {{
        background: {TEAL};
        color: {WHITE};
        font-weight: 600;
        border-left: 4px solid {WHITE};
    }}

    /* ---- Top bar ---- */
    QWidget#topbar {{
        background: {WHITE};
        border-bottom: 1px solid {BORDER_GRAY};
        min-height: 56px;
        max-height: 56px;
    }}
    QLabel#topbarTitle {{
        font-size: 16px;
        font-weight: 700;
        color: {NAVY};
    }}
    QLabel#userBadge {{
        color: {TEXT_MUTED};
        font-size: 12px;
    }}

    /* ---- Cards ---- */
    QFrame.card {{
        background: {WHITE};
        border: 1px solid {BORDER_GRAY};
        border-radius: 10px;
    }}
    QLabel.cardTitle {{
        color: {TEXT_MUTED};
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
    }}
    QLabel.cardValue {{
        color: {NAVY};
        font-size: 24px;
        font-weight: 700;
    }}
    QLabel.cardSubtext {{
        color: {TEXT_MUTED};
        font-size: 11px;
    }}
    QLabel.sectionHeading {{
        color: {NAVY};
        font-size: 16px;
        font-weight: 700;
        padding: 4px 0px;
    }}
    QLabel.pageSubtitle {{
        color: {TEXT_MUTED};
        font-size: 12px;
    }}

    /* ---- Buttons ---- */
    QPushButton.primaryButton {{
        background: {TEAL};
        color: {WHITE};
        border: none;
        border-radius: 6px;
        padding: 9px 18px;
        font-weight: 600;
    }}
    QPushButton.primaryButton:hover {{ background: #0C7476; }}
    QPushButton.primaryButton:pressed {{ background: #0A6062; }}
    QPushButton.primaryButton:disabled {{ background: #A9C7C8; }}

    QPushButton.secondaryButton {{
        background: {WHITE};
        color: {NAVY};
        border: 1px solid {BORDER_GRAY};
        border-radius: 6px;
        padding: 9px 18px;
        font-weight: 600;
    }}
    QPushButton.secondaryButton:hover {{ background: {SOFT_GRAY}; }}

    QPushButton.dangerButton {{
        background: {WHITE};
        color: {DANGER};
        border: 1px solid #F3C4C4;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 600;
    }}
    QPushButton.dangerButton:hover {{ background: {DANGER_BG}; }}

    QPushButton.linkButton {{
        background: transparent;
        color: {MEDICAL_BLUE};
        border: none;
        font-weight: 600;
        text-align: left;
    }}
    QPushButton.linkButton:hover {{ text-decoration: underline; }}

    /* ---- Inputs ---- */
    QLineEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit {{
        background: {WHITE};
        border: 1px solid {BORDER_GRAY};
        border-radius: 6px;
        padding: 7px 10px;
        selection-background-color: {TEAL};
    }}
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {{
        border: 1px solid {TEAL};
    }}
    QComboBox::drop-down {{ border: none; width: 24px; }}

    /* ---- Tables ---- */
    QTableWidget {{
        background: {WHITE};
        border: 1px solid {BORDER_GRAY};
        border-radius: 8px;
        gridline-color: {BORDER_GRAY};
        selection-background-color: {TEAL_LIGHT};
        selection-color: {TEXT_DARK};
    }}
    QHeaderView::section {{
        background: {SOFT_GRAY};
        color: {TEXT_MUTED};
        font-weight: 600;
        font-size: 11px;
        border: none;
        border-bottom: 1px solid {BORDER_GRAY};
        padding: 8px;
        text-transform: uppercase;
    }}
    QTableWidget::item {{ padding: 6px; }}

    /* ---- Tabs ---- */
    QTabWidget::pane {{
        border: 1px solid {BORDER_GRAY};
        border-radius: 8px;
        background: {WHITE};
        top: -1px;
    }}
    QTabBar::tab {{
        background: transparent;
        color: {TEXT_MUTED};
        padding: 9px 16px;
        font-weight: 600;
        border-bottom: 3px solid transparent;
    }}
    QTabBar::tab:selected {{
        color: {NAVY};
        border-bottom: 3px solid {TEAL};
    }}
    QTabBar::tab:hover {{ color: {NAVY}; }}

    /* ---- Misc ---- */
    QScrollArea {{ border: none; background: transparent; }}
    QStatusBar {{ background: {WHITE}; border-top: 1px solid {BORDER_GRAY}; color: {TEXT_MUTED}; }}
    QToolTip {{ background: {NAVY}; color: {WHITE}; border: none; padding: 4px 8px; border-radius: 4px; }}
    QMenu {{ background: {WHITE}; border: 1px solid {BORDER_GRAY}; }}
    QMenu::item:selected {{ background: {TEAL_LIGHT}; }}
    """
