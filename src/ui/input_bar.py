from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QKeyEvent
from PySide6.QtWidgets import QTextEdit

from ui.fonts import FONT_FAMILY

_MIN_HEIGHT = 32
_MAX_HEIGHT = 90


class InputBar(QTextEdit):
    submitted = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setPlaceholderText("Ask something...")
        self.setFont(QFont(FONT_FAMILY, 11))
        self.setAcceptRichText(False)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFixedHeight(_MIN_HEIGHT)
        self.setStyleSheet("""
            QTextEdit {
                background: #1a1a2e;
                color: #e0e0e0;
                border: 1px solid #3a3a5e;
                border-radius: 8px;
                padding: 4px 10px;
                selection-background-color: #7ec8e3;
            }
            QTextEdit:focus {
                border-color: #7ec8e3;
            }
            QScrollBar:vertical {
                width: 4px;
                background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #3a3a5e;
                border-radius: 2px;
                min-height: 16px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        self.textChanged.connect(self._auto_resize)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                super().keyPressEvent(event)
            else:
                self._submit()
                event.accept()
                return
        super().keyPressEvent(event)

    def _submit(self) -> None:
        text = self.toPlainText().strip()
        if text:
            self.submitted.emit(text)
            self.clear()

    def _auto_resize(self) -> None:
        doc_height = int(self.document().size().height()) + 10
        new_height = max(_MIN_HEIGHT, min(doc_height, _MAX_HEIGHT))
        self.setFixedHeight(new_height)

    def set_busy(self, busy: bool) -> None:
        self.setEnabled(not busy)
        if busy:
            self.setPlaceholderText("Processing...")
        else:
            self.setPlaceholderText("Ask something...")
