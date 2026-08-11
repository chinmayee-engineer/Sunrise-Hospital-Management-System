"""Reusable, theme-aware widgets shared by the Patient and Hospital
applications: stat cards, status badges, toast notifications,
confirmation dialogs and empty states (spec section 4)."""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QDialog, QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QMessageBox,
    QPushButton, QVBoxLayout, QWidget, QLineEdit,
)

from core.theme import (
    BORDER_GRAY, DANGER, DANGER_BG, NAVY, STATUS_COLORS, SUCCESS, SUCCESS_BG,
    TEAL, TEXT_MUTED, WARNING, WARNING_BG, WHITE,
)


def add_card_shadow(widget: QWidget) -> None:
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(18)
    effect.setOffset(0, 2)
    effect.setColor(QColor(11, 61, 102, 28))
    widget.setGraphicsEffect(effect)


class StatCard(QFrame):
    """A dashboard summary card: title, big value, optional subtext/icon."""

    clicked = Signal()

    def __init__(self, title: str, value: str, subtext: str = "", icon: str = "", accent: str = TEAL):
        super().__init__()
        self.setProperty("class", "card")
        self.setObjectName("statCard")
        self.setMinimumHeight(96)
        self.setCursor(Qt.PointingHandCursor)
        add_card_shadow(self)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 14)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        title_label = QLabel((f"{icon}  " if icon else "") + title)
        title_label.setProperty("class", "cardTitle")
        self.value_label = QLabel(value)
        self.value_label.setProperty("class", "cardValue")
        text_col.addWidget(title_label)
        text_col.addWidget(self.value_label)
        if subtext:
            sub = QLabel(subtext)
            sub.setProperty("class", "cardSubtext")
            text_col.addWidget(sub)
        outer.addLayout(text_col)
        outer.addStretch()
        self.setStyleSheet(self.styleSheet() + f"QFrame#statCard {{ border-left: 4px solid {accent}; }}")

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)

    def mousePressEvent(self, event):  # noqa: N802 (Qt override)
        self.clicked.emit()
        super().mousePressEvent(event)


class StatusBadge(QLabel):
    """A small pill-shaped label colored by status (spec: status badges)."""

    def __init__(self, status: str):
        super().__init__(_humanize(status))
        color, bg = STATUS_COLORS.get(status, (TEXT_MUTED, "#EEEEEE"))
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(
            f"background: {bg}; color: {color}; border-radius: 9px; padding: 2px 10px; "
            f"font-weight: 600; font-size: 11px;"
        )
        self.setFixedHeight(20)


def _humanize(status: str) -> str:
    out = []
    for i, ch in enumerate(status):
        if ch.isupper() and i > 0 and not status[i - 1].isupper():
            out.append(" ")
        out.append(ch)
    return "".join(out)


class EmptyState(QWidget):
    """Friendly placeholder for tables/lists with no data (spec section 4)."""

    def __init__(self, icon: str, title: str, subtitle: str = ""):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 40px;")
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {NAVY}; margin-top: 8px;")
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setAlignment(Qt.AlignCenter)
            subtitle_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
            layout.addWidget(subtitle_label)


class Toast(QFrame):
    """A transient, non-blocking notification banner shown at the top
    of the main content area."""

    KIND_STYLES = {
        "success": (SUCCESS, SUCCESS_BG, "✓"),
        "warning": (WARNING, WARNING_BG, "⚠"),
        "error": (DANGER, DANGER_BG, "✕"),
        "info": (TEAL, "#E6F5F5", "ℹ"),
    }

    def __init__(self, parent: QWidget, message: str, kind: str = "success", duration_ms: int = 3200):
        super().__init__(parent)
        color, bg, icon = self.KIND_STYLES.get(kind, self.KIND_STYLES["info"])
        self.setStyleSheet(
            f"background: {bg}; border: 1px solid {color}; border-radius: 8px; padding: 2px;"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        label = QLabel(f"{icon}  {message}")
        label.setStyleSheet(f"color: {color}; font-weight: 600; border: none; background: transparent;")
        label.setWordWrap(True)
        layout.addWidget(label)
        self.setMaximumHeight(0)
        QTimer.singleShot(duration_ms, self.deleteLater)


def show_toast(container_layout, parent_widget: QWidget, message: str, kind: str = "success") -> None:
    """Insert a Toast at the top of a layout and auto-remove it."""
    toast = Toast(parent_widget, message, kind)
    container_layout.insertWidget(0, toast)
    QTimer.singleShot(3200, lambda: container_layout.removeWidget(toast))


def confirm(parent: QWidget, title: str, message: str) -> bool:
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(message)
    box.setIcon(QMessageBox.Question)
    box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    box.setDefaultButton(QMessageBox.No)
    return box.exec() == QMessageBox.Yes


def info_message(parent: QWidget, title: str, message: str) -> None:
    QMessageBox.information(parent, title, message)


def error_message(parent: QWidget, title: str, message: str) -> None:
    QMessageBox.critical(parent, title, message)


def section_heading(text: str) -> QLabel:
    label = QLabel(text)
    label.setProperty("class", "sectionHeading")
    return label


def primary_button(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setProperty("class", "primaryButton")
    btn.setCursor(Qt.PointingHandCursor)
    return btn


def secondary_button(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setProperty("class", "secondaryButton")
    btn.setCursor(Qt.PointingHandCursor)
    return btn


def danger_button(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setProperty("class", "dangerButton")
    btn.setCursor(Qt.PointingHandCursor)
    return btn


def link_button(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setProperty("class", "linkButton")
    btn.setCursor(Qt.PointingHandCursor)
    return btn


class SearchBox(QLineEdit):
    def __init__(self, placeholder: str = "Search..."):
        super().__init__()
        self.setPlaceholderText(f"🔍  {placeholder}")
        self.setMinimumWidth(240)
