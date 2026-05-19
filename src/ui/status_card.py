from __future__ import annotations

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property, Signal
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QPushButton,
)

from ui.fonts import FONT_FAMILY

_STATUS_STYLES = {
    "success": ("#06d6a0", "✓"),
    "error": ("#ef476f", "✗"),
    "failed": ("#ef476f", "✗"),
    "running": ("#ffd166", "◌"),
    "pending": ("#7ec8e3", "…"),
    "skipped": ("#888888", "—"),
}


class StatusDot(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(12, 12)
        self._color = QColor("#888888")
        self._pulse_opacity = 1.0
        self._pulse_anim: QPropertyAnimation | None = None

    def _get_pulse(self) -> float:
        return self._pulse_opacity

    def _set_pulse(self, val: float) -> None:
        self._pulse_opacity = val
        self.update()

    pulse = Property(float, _get_pulse, _set_pulse)

    def set_status(self, status: str) -> None:
        color_hex = _STATUS_STYLES.get(status, ("#888888", "…"))[0]
        self._color = QColor(color_hex)

        if self._pulse_anim:
            self._pulse_anim.stop()
            self._pulse_anim = None

        if status in ("running", "pending"):
            anim = QPropertyAnimation(self, b"pulse", self)
            anim.setStartValue(1.0)
            anim.setEndValue(0.3)
            anim.setDuration(800)
            anim.setEasingCurve(QEasingCurve.Type.InOutSine)
            anim.setLoopCount(-1)
            self._pulse_anim = anim
            anim.start()
        else:
            self._pulse_opacity = 1.0

        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = QColor(self._color)
        c.setAlphaF(self._pulse_opacity)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(c)
        painter.drawEllipse(1, 1, 10, 10)
        painter.end()


class TaskCard(QWidget):
    _MAX_NAME_LEN = 35

    def __init__(self, name: str, status: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("""
            TaskCard {
                background: #2a2a3e;
                border-radius: 6px;
            }
        """)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(24)

        layout = self._build_layout(name, status)
        self.setLayout(layout)

    def _build_layout(self, name: str, status: str):
        from PySide6.QtWidgets import QHBoxLayout

        layout = QHBoxLayout()
        layout.setContentsMargins(6, 1, 6, 1)
        layout.setSpacing(4)

        dot = StatusDot(self)
        dot.set_status(status)
        layout.addWidget(dot)

        display_name = (
            name
            if len(name) <= self._MAX_NAME_LEN
            else name[: self._MAX_NAME_LEN] + "…"
        )
        label = QLabel(display_name)
        label.setFont(QFont(FONT_FAMILY, 8))
        label.setStyleSheet("color: #e0e0e0; background: transparent;")
        layout.addWidget(label, stretch=1)

        status_upper = status.upper()
        status_label = QLabel(status_upper)
        status_label.setFont(QFont(FONT_FAMILY, 7))
        color = _STATUS_STYLES.get(status.lower(), ("#888", "…"))[0]
        status_label.setStyleSheet(f"color: {color}; background: transparent;")
        layout.addWidget(status_label)

        return layout


class StatusPanel(QWidget):
    approved = Signal()
    denied = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 4, 0, 0)
        self._layout.setSpacing(3)
        self.setLayout(self._layout)
        self._cards: list[TaskCard] = []

        self._buttons_widget = QWidget(self)
        btn_layout = QHBoxLayout(self._buttons_widget)
        btn_layout.setContentsMargins(0, 2, 0, 2)
        btn_layout.setSpacing(6)

        self._approve_btn = QPushButton("✓ Approve")
        self._approve_btn.setFont(QFont(FONT_FAMILY, 8))
        self._approve_btn.setStyleSheet("""
            QPushButton {
                background: #06d6a0; color: #1a1a2e; border: none;
                border-radius: 6px; padding: 3px 12px;
            }
            QPushButton:hover { background: #05c090; }
        """)
        self._approve_btn.setFixedHeight(22)
        self._approve_btn.clicked.connect(self.approved.emit)

        self._deny_btn = QPushButton("✗ Deny")
        self._deny_btn.setFont(QFont(FONT_FAMILY, 8))
        self._deny_btn.setStyleSheet("""
            QPushButton {
                background: #ef476f; color: #e0e0e0; border: none;
                border-radius: 6px; padding: 3px 12px;
            }
            QPushButton:hover { background: #d63d5f; }
        """)
        self._deny_btn.setFixedHeight(22)
        self._deny_btn.clicked.connect(self.denied.emit)

        btn_layout.addStretch()
        btn_layout.addWidget(self._approve_btn)
        btn_layout.addWidget(self._deny_btn)
        btn_layout.addStretch()

        self._buttons_widget.hide()
        self._layout.addWidget(self._buttons_widget)

        self._reply_label = QLabel("")
        self._reply_label.setWordWrap(True)
        self._reply_label.setFont(QFont(FONT_FAMILY, 8))
        self._reply_label.setStyleSheet(
            "color: #c0c0c0; background: transparent; padding: 2px 4px;"
        )
        self._reply_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self._reply_label.hide()
        self._layout.addWidget(self._reply_label)

    def clear(self) -> None:
        for card in self._cards:
            self._layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()
        self._reply_label.hide()
        self._buttons_widget.hide()

    def set_tasks(self, tasks: list[dict], max_visible: int = 5) -> None:
        self.clear()
        visible = tasks[-max_visible:] if len(tasks) > max_visible else tasks
        for t in visible:
            card = TaskCard(t.get("name", "?"), t.get("status", "pending"), self)
            self._cards.append(card)
            idx = self._layout.count() - 2
            self._layout.insertWidget(max(idx, 0), card)

    def show_approve_buttons(self, visible: bool = True) -> None:
        if visible:
            self._buttons_widget.show()
        else:
            self._buttons_widget.hide()

    def set_reply(self, text: str) -> None:
        if text:
            truncated = text[:500] + "…" if len(text) > 500 else text
            self._reply_label.setText(truncated)
            self._reply_label.show()
        else:
            self._reply_label.hide()
