from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLineEdit

from ui.fonts import FONT_FAMILY


class InputBar(QLineEdit):
    submitted = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setPlaceholderText("Ask something...")
        self.setFont(QFont(FONT_FAMILY, 11))
        self.setStyleSheet("""
            QLineEdit {
                background: #1a1a2e;
                color: #e0e0e0;
                border: 1px solid #3a3a5e;
                border-radius: 8px;
                padding: 6px 12px;
                selection-background-color: #7ec8e3;
            }
            QLineEdit:focus {
                border-color: #7ec8e3;
            }
        """)
        self.returnPressed.connect(self._on_return)

    def _on_return(self) -> None:
        text = self.text().strip()
        if text:
            self.submitted.emit(text)
            self.clear()

    def set_busy(self, busy: bool) -> None:
        self.setEnabled(not busy)
        if busy:
            self.setPlaceholderText("Processing...")
        else:
            self.setPlaceholderText("Ask something...")
