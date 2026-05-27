from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QFont, QMouseEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

import httpx

from ui.fonts import FONT_FAMILY

_LABEL_STYLE = "color: #a0a0b8; background: transparent;"
_VALUE_STYLE = """
    QLineEdit, QSpinBox, QComboBox {
        background: #2a2a3e; color: #e0e0e0; border: 1px solid #3a3a5e;
        border-radius: 4px; padding: 2px 6px;
    }
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
        border-color: #06d6a0;
    }
"""
_CHECK_STYLE = """
    QCheckBox { color: #e0e0e0; background: transparent; spacing: 4px; }
    QCheckBox::indicator {
        width: 14px; height: 14px; border-radius: 3px;
        border: 1px solid #3a3a5e; background: #2a2a3e;
    }
    QCheckBox::indicator:checked { background: #06d6a0; border-color: #06d6a0; }
"""

_FIELD_DEFS: list[dict] = [
    {
        "key": "LLM_PROVIDER",
        "label": "LLM Provider",
        "type": "combo",
        "options": ["gemini", "openai", "ollama"],
        "group": "LLM",
    },
    {"key": "MODEL_NAME", "label": "Model Name", "type": "str", "group": "LLM"},
    {"key": "DEBUG", "label": "Debug Mode", "type": "bool", "group": "General"},
    {
        "key": "REACT_MAX_ITERATIONS",
        "label": "Max ReAct Steps",
        "type": "int",
        "min": 1,
        "max": 200,
        "group": "General",
    },
    {
        "key": "MEMORY_TURNS",
        "label": "Memory Turns",
        "type": "int",
        "min": 0,
        "max": 100,
        "group": "General",
    },
    {
        "key": "WEB_TIMEOUT",
        "label": "Web Timeout (s)",
        "type": "float",
        "group": "Network",
    },
    {
        "key": "HTTP_TIMEOUT",
        "label": "HTTP Timeout (s)",
        "type": "float",
        "group": "Network",
    },
    {
        "key": "MCP_CALL_TIMEOUT",
        "label": "MCP Timeout (s)",
        "type": "float",
        "group": "Network",
    },
    {"key": "UI_SHOW_LOGS", "label": "Show Logs", "type": "bool", "group": "UI"},
    {"key": "UI_TAMAGOTCHI", "label": "Show Tamagotchi", "type": "bool", "group": "UI"},
    {
        "key": "UI_AUTO_APPROVE",
        "label": "Auto-approve Tasks",
        "type": "bool",
        "group": "UI",
    },
    {
        "key": "UI_MAX_VISIBLE_TASKS",
        "label": "Max Visible Tasks",
        "type": "int",
        "min": 1,
        "max": 50,
        "group": "UI",
    },
    {
        "key": "UI_SUMMARY_DELAY_MS",
        "label": "Summary Delay (ms)",
        "type": "int",
        "min": 0,
        "max": 10000,
        "group": "UI",
    },
    {
        "key": "UI_FONT_SIZE",
        "label": "Font Size (pt)",
        "type": "int",
        "min": 6,
        "max": 24,
        "group": "UI",
    },
    {
        "key": "UI_LANGUAGE",
        "label": "Language",
        "type": "combo",
        "options": ["uk", "en"],
        "group": "UI",
    },
]


class SettingsPanel(QWidget):
    closed = Signal()
    settings_changed = Signal(dict)

    def __init__(
        self, base_url: str = "http://127.0.0.1:8000", parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._base_url = base_url
        self._widgets: dict[str, QWidget] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        self.setStyleSheet(_VALUE_STYLE + _CHECK_STYLE)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(8, 4, 8, 4)

        title = QLabel("Settings")
        title.setFont(QFont(FONT_FAMILY, 9, QFont.Weight.Bold))
        title.setStyleSheet("color: #e0e0e0; background: transparent;")
        header.addWidget(title)

        header.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFont(QFont(FONT_FAMILY, 9))
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #888; border: none;
            }
            QPushButton:hover { color: #ef476f; }
        """)
        close_btn.clicked.connect(self.closed.emit)
        header.addWidget(close_btn)

        outer.addLayout(header)

        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #3a3a5e;")
        outer.addWidget(sep)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        form = QVBoxLayout(content)
        form.setContentsMargins(8, 6, 8, 6)
        form.setSpacing(4)

        current_group = ""
        for fdef in _FIELD_DEFS:
            group = fdef.get("group", "")
            if group != current_group:
                current_group = group
                grp_label = QLabel(group)
                grp_label.setFont(QFont(FONT_FAMILY, 8, QFont.Weight.Bold))
                grp_label.setStyleSheet(
                    "color: #06d6a0; background: transparent; margin-top: 4px;"
                )
                form.addWidget(grp_label)

            row = QHBoxLayout()
            row.setSpacing(6)

            lbl = QLabel(fdef["label"])
            lbl.setFont(QFont(FONT_FAMILY, 8))
            lbl.setStyleSheet(_LABEL_STYLE)
            lbl.setFixedWidth(130)
            row.addWidget(lbl)

            widget = self._create_widget(fdef)
            self._widgets[fdef["key"]] = widget
            row.addWidget(widget, stretch=1)

            form.addLayout(row)

        form.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(8, 4, 8, 6)
        btn_row.addStretch()

        save_btn = QPushButton("Save")
        save_btn.setFont(QFont(FONT_FAMILY, 8))
        save_btn.setFixedHeight(24)
        save_btn.setStyleSheet("""
            QPushButton {
                background: #06d6a0; color: #1a1a2e; border: none;
                border-radius: 6px; padding: 3px 20px;
            }
            QPushButton:hover { background: #05c090; }
        """)
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)
        btn_row.addStretch()

        outer.addLayout(btn_row)

    def _create_widget(self, fdef: dict) -> QWidget:
        ftype = fdef["type"]
        if ftype == "bool":
            cb = QCheckBox()
            cb.setFont(QFont(FONT_FAMILY, 8))
            return cb
        if ftype == "int":
            sb = QSpinBox()
            sb.setFont(QFont(FONT_FAMILY, 8))
            sb.setMinimum(fdef.get("min", 0))
            sb.setMaximum(fdef.get("max", 999999))
            sb.setFixedHeight(22)
            return sb
        if ftype == "float":
            le = QLineEdit()
            le.setFont(QFont(FONT_FAMILY, 8))
            le.setFixedHeight(22)
            return le
        if ftype == "combo":
            cb = QComboBox()
            cb.setFont(QFont(FONT_FAMILY, 8))
            cb.setFixedHeight(22)
            for opt in fdef.get("options", []):
                cb.addItem(opt)
            return cb
        le = QLineEdit()
        le.setFont(QFont(FONT_FAMILY, 8))
        le.setFixedHeight(22)
        return le

    def load_settings(self) -> None:
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{self._base_url}/settings")
                resp.raise_for_status()
                data = resp.json()
        except Exception:
            return

        for fdef in _FIELD_DEFS:
            key = fdef["key"]
            if key not in data:
                continue
            widget = self._widgets.get(key)
            if widget is None:
                continue
            val = data[key]
            self._set_widget_value(widget, fdef, val)

    def _set_widget_value(self, widget: QWidget, fdef: dict, val) -> None:
        ftype = fdef["type"]
        if ftype == "bool" and isinstance(widget, QCheckBox):
            widget.setChecked(bool(val))
        elif ftype == "int" and isinstance(widget, QSpinBox):
            widget.setValue(int(val))
        elif ftype == "float" and isinstance(widget, QLineEdit):
            widget.setText(str(val))
        elif ftype == "combo" and isinstance(widget, QComboBox):
            idx = widget.findText(str(val))
            if idx >= 0:
                widget.setCurrentIndex(idx)
            else:
                widget.addItem(str(val))
                widget.setCurrentIndex(widget.count() - 1)
        elif isinstance(widget, QLineEdit):
            widget.setText(str(val))

    def _get_widget_value(self, widget: QWidget, fdef: dict):
        ftype = fdef["type"]
        if ftype == "bool" and isinstance(widget, QCheckBox):
            return widget.isChecked()
        if ftype == "int" and isinstance(widget, QSpinBox):
            return widget.value()
        if ftype == "float" and isinstance(widget, QLineEdit):
            try:
                return float(widget.text())
            except ValueError:
                return None
        if ftype == "combo" and isinstance(widget, QComboBox):
            return widget.currentText()
        if isinstance(widget, QLineEdit):
            return widget.text()
        return None

    def _on_save(self) -> None:
        payload = {}
        for fdef in _FIELD_DEFS:
            key = fdef["key"]
            widget = self._widgets.get(key)
            if widget is None:
                continue
            val = self._get_widget_value(widget, fdef)
            if val is not None:
                payload[key] = val

        if "UI_AUTO_APPROVE" in payload:
            payload["API_AUTO_APPROVE"] = payload["UI_AUTO_APPROVE"]

        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.patch(f"{self._base_url}/settings", json=payload)
                resp.raise_for_status()
                data = resp.json()
        except Exception:
            return

        self.settings_changed.emit(data)
        self.closed.emit()


class SettingsWindow(QWidget):
    settings_changed = Signal(dict)

    _WIDTH = 340
    _HEIGHT = 420

    def __init__(self) -> None:
        super().__init__()
        self._drag_pos: QPoint | None = None

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(self._WIDTH, self._HEIGHT)

        from PySide6.QtWidgets import QGraphicsDropShadowEffect

        container = QWidget(self)
        container.setObjectName("settings_container")
        container.setStyleSheet("""
            #settings_container {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #16213e, stop:1 #1a1a2e
                );
                border-radius: 12px;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 4)
        shadow.setColor(Qt.GlobalColor.black)
        container.setGraphicsEffect(shadow)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.addWidget(container)

        inner = QVBoxLayout(container)
        inner.setContentsMargins(0, 0, 0, 0)
        inner.setSpacing(0)

        self._panel = SettingsPanel(parent=container)
        self._panel.closed.connect(self.hide)
        self._panel.settings_changed.connect(self.settings_changed.emit)
        inner.addWidget(self._panel)

    def load_and_show(self, parent_pos: QPoint) -> None:
        from PySide6.QtWidgets import QApplication

        self._panel.load_settings()
        x = parent_pos.x() - self._WIDTH - 8
        y = parent_pos.y()
        screen = QApplication.screenAt(parent_pos)
        if screen is None:
            screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            if x < geo.x():
                x = parent_pos.x() + 420 + 8
            if y + self._HEIGHT > geo.bottom():
                y = geo.bottom() - self._HEIGHT
            x = max(x, geo.x())
            y = max(y, geo.y())
        self.move(x, y)
        self.show()
        self.raise_()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_pos = None
