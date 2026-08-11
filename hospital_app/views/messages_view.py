"""Doctor-side messaging with patients (spec section 30)."""
from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QListWidget, QTextEdit, QVBoxLayout, QWidget

from core.security.auth import Session
from core.services import message_service
from shared_ui.widgets import EmptyState, primary_button, section_heading


class MessagesView(QWidget):
    def __init__(self, session: Session, main_window):
        super().__init__()
        self.session = session
        self.main_window = main_window
        self.active_patient_id: str | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 24)
        outer.addWidget(section_heading("Messages"))

        body = QHBoxLayout()
        self.conv_list = QListWidget()
        self.conv_list.setMaximumWidth(280)
        self.conv_list.itemClicked.connect(self._open_conversation)
        body.addWidget(self.conv_list)

        right = QVBoxLayout()
        self.thread_view = QTextEdit()
        self.thread_view.setReadOnly(True)
        right.addWidget(self.thread_view)
        input_row = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type a message...")
        self.message_input.returnPressed.connect(self._send)
        send_btn = primary_button("Send")
        send_btn.clicked.connect(self._send)
        input_row.addWidget(self.message_input)
        input_row.addWidget(send_btn)
        right.addLayout(input_row)
        body.addLayout(right, stretch=1)
        outer.addLayout(body)

    def refresh(self, **kwargs) -> None:
        if not self.session.linked_doctor_id:
            self.conv_list.clear()
            self.conv_list.addItem("Messaging is available for doctor accounts.")
            return
        self.conv_list.clear()
        convs = message_service.conversations_for_doctor(self.session.linked_doctor_id)
        if not convs:
            self.conv_list.addItem("No conversations yet.")
            return
        for c in convs:
            label = f"{c['patient_name']}" + (f"  ({c['unread_count']})" if c["unread_count"] else "")
            self.conv_list.addItem(label)
            self.conv_list.item(self.conv_list.count() - 1).setData(1000, c["patient_id"])

    def _open_conversation(self, item) -> None:
        patient_id = item.data(1000)
        if not patient_id:
            return
        self.active_patient_id = patient_id
        message_service.mark_conversation_read(patient_id, self.session.linked_doctor_id, "doctor")
        self._render_thread()

    def _render_thread(self) -> None:
        if not self.active_patient_id:
            return
        msgs = message_service.conversation(self.active_patient_id, self.session.linked_doctor_id)
        lines = []
        for m in msgs:
            who = "You" if m["sender"] == "doctor" else "Patient"
            lines.append(f"[{m['created_at'][:16]}] {who}: {m['body']}")
        self.thread_view.setPlainText("\n".join(lines) or "No messages yet.")

    def _send(self) -> None:
        text = self.message_input.text().strip()
        if not text or not self.active_patient_id:
            return
        message_service.send_message(self.active_patient_id, self.session.linked_doctor_id, "doctor", text)
        self.message_input.clear()
        self._render_thread()
        self.refresh()
