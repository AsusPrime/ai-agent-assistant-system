from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QFont, QMouseEvent
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

import httpx

from ui.fonts import FONT_FAMILY

_CARD_STYLE = """
    QPushButton {
        background: #2a2a3e; color: #e0e0e0; border: none;
        border-radius: 6px; padding: 6px 10px;
        text-align: left;
    }
    QPushButton:hover { background: #3a3a5e; }
"""


class _RecipeCard(QWidget):
    run_clicked = Signal(str)

    def __init__(
        self,
        recipe_id: str,
        title: str,
        description: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._recipe_id = recipe_id
        self.setStyleSheet("""
            _RecipeCard {
                background: #2a2a3e; border-radius: 6px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 4, 4)
        layout.setSpacing(6)

        text_col = QVBoxLayout()
        text_col.setSpacing(1)

        title_label = QLabel(title)
        title_label.setFont(QFont(FONT_FAMILY, 9, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #e0e0e0; background: transparent;")
        title_label.setWordWrap(True)
        text_col.addWidget(title_label)

        if description:
            desc_label = QLabel(description)
            desc_label.setFont(QFont(FONT_FAMILY, 7))
            desc_label.setStyleSheet("color: #808090; background: transparent;")
            desc_label.setWordWrap(True)
            text_col.addWidget(desc_label)

        layout.addLayout(text_col, stretch=1)

        run_btn = QPushButton("▶")
        run_btn.setFont(QFont(FONT_FAMILY, 10))
        run_btn.setFixedSize(26, 26)
        run_btn.setStyleSheet("""
            QPushButton {
                background: #06d6a0; color: #1a1a2e; border: none;
                border-radius: 6px;
            }
            QPushButton:hover { background: #05c090; }
        """)
        run_btn.setToolTip(f"Run {title}")
        run_btn.clicked.connect(lambda: self.run_clicked.emit(self._recipe_id))
        layout.addWidget(run_btn, alignment=Qt.AlignmentFlag.AlignVCenter)


class RecipeListPanel(QWidget):
    closed = Signal()
    recipe_run = Signal(str)

    def __init__(
        self, base_url: str = "http://127.0.0.1:8000", parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._base_url = base_url
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(8, 4, 8, 4)

        title = QLabel("Recipes")
        title.setFont(QFont(FONT_FAMILY, 9, QFont.Weight.Bold))
        title.setStyleSheet("color: #e0e0e0; background: transparent;")
        header.addWidget(title)
        header.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFont(QFont(FONT_FAMILY, 9))
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #888; border: none; }
            QPushButton:hover { color: #ef476f; }
        """)
        close_btn.clicked.connect(self.closed.emit)
        header.addWidget(close_btn)

        outer.addLayout(header)

        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #3a3a5e;")
        outer.addWidget(sep)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
        )
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._content = QWidget()
        self._content.setStyleSheet("background: transparent;")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(8, 6, 8, 6)
        self._content_layout.setSpacing(4)
        self._content_layout.addStretch()

        self._scroll.setWidget(self._content)
        outer.addWidget(self._scroll, stretch=1)

    def load_recipes(self) -> None:
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{self._base_url}/recipes")
                resp.raise_for_status()
                data = resp.json()
        except Exception:
            empty = QLabel("Cannot load recipes")
            empty.setFont(QFont(FONT_FAMILY, 8))
            empty.setStyleSheet("color: #888; background: transparent;")
            self._content_layout.insertWidget(0, empty)
            return

        recipes = data.get("recipes", [])
        if not recipes:
            empty = QLabel("No recipes yet")
            empty.setFont(QFont(FONT_FAMILY, 8))
            empty.setStyleSheet("color: #888; background: transparent;")
            self._content_layout.insertWidget(0, empty)
            return

        for r in recipes:
            if isinstance(r, str):
                recipe_id, title, desc = r, r.replace("_", " ").title(), ""
            else:
                recipe_id = r.get("id", "")
                title = r.get("title", recipe_id)
                desc = r.get("description", "")
            card = _RecipeCard(recipe_id, title, desc, self._content)
            card.run_clicked.connect(self.recipe_run.emit)
            self._content_layout.insertWidget(self._content_layout.count() - 1, card)


class RecipeWindow(QWidget):
    recipe_run = Signal(str)

    _WIDTH = 360
    _HEIGHT = 380

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

        container = QWidget(self)
        container.setObjectName("recipe_container")
        container.setStyleSheet("""
            #recipe_container {
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

        self._panel = RecipeListPanel(parent=container)
        self._panel.closed.connect(self.hide)
        self._panel.recipe_run.connect(self.recipe_run.emit)
        inner.addWidget(self._panel)

    _BASE_FONT_SIZE = 9

    def set_font_size(self, size: int) -> None:
        self._font_size = size
        self._apply_font_scaling()

    def _apply_font_scaling(self) -> None:
        delta = getattr(self, "_font_size", self._BASE_FONT_SIZE) - self._BASE_FONT_SIZE
        from PySide6.QtWidgets import QWidget
        for child in self.findChildren(QWidget):
            if not hasattr(child, "_orig_font_pt"):
                ps = child.font().pointSize()
                if ps > 0:
                    child._orig_font_pt = ps
            orig = getattr(child, "_orig_font_pt", 0)
            if orig > 0:
                f = child.font()
                f.setPointSize(max(6, orig + delta))
                child.setFont(f)

    def load_and_show(self, parent_pos: QPoint) -> None:
        from PySide6.QtWidgets import QApplication

        self._panel.load_recipes()
        self._apply_font_scaling()
        x = parent_pos.x() - self._WIDTH - 8
        y = parent_pos.y()
        screen = QApplication.screenAt(parent_pos)
        if screen is None:
            screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            if x < geo.x():
                x = parent_pos.x() + self._WIDTH + 8
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
