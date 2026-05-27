from __future__ import annotations

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property, Signal, QUrl
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QTextDocument
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QPushButton,
    QTextBrowser,
)

import re

from markdown_it import MarkdownIt

from ui.fonts import FONT_FAMILY

_md = MarkdownIt().enable(["table", "strikethrough"])

_TASKLIST_RE = re.compile(r"<li>\[([ xX])\]\s*", re.MULTILINE)

_CSS = """\
<style>
body {{ color: #c0c0c0; font-family: {font}; font-size: {size}pt; }}
h1 {{ font-size: {h1}pt; color: #7ec8e3; margin: 4px 0; }}
h2 {{ font-size: {h2}pt; color: #7ec8e3; margin: 3px 0; }}
h3 {{ font-size: {h3}pt; color: #7ec8e3; margin: 2px 0; }}
h4, h5, h6 {{ font-size: {h4}pt; color: #7ec8e3; margin: 2px 0; }}
code {{ background: #2a2a3e; padding: 1px 4px; border-radius: 3px; font-size: {code}pt; }}
pre {{ background: #2a2a3e; padding: 6px 8px; border-radius: 6px; overflow-x: auto; }}
pre code {{ background: transparent; padding: 0; }}
blockquote {{ border-left: 3px solid #3a3a5e; margin: 4px 0; padding: 2px 8px; color: #a0a0b8; }}
a {{ color: #7ec8e3; }}
table {{ border-collapse: collapse; margin: 4px 0; }}
th, td {{ border: 1px solid #3a3a5e; padding: 3px 8px; }}
th {{ background: #2a2a3e; }}
hr {{ border: none; border-top: 1px solid #3a3a5e; margin: 6px 0; }}
img {{ max-width: 100%; }}
.task-done {{ color: #06d6a0; }}
.task-todo {{ color: #888; }}
</style>
"""


def _md_to_html(text: str, font_size: int = 9) -> str:
    raw = _md.render(text)
    raw = _TASKLIST_RE.sub(_tasklist_replace, raw)
    css = _CSS.format(
        font=FONT_FAMILY,
        size=font_size,
        h1=font_size + 4,
        h2=font_size + 3,
        h3=font_size + 2,
        h4=font_size + 1,
        code=font_size - 1,
    )
    return f"{css}{raw}"


def _tasklist_replace(m: re.Match) -> str:
    checked = m.group(1) in ("x", "X")
    if checked:
        return '<li class="task-done">✓ '
    return '<li class="task-todo">☐ '


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


_IMG_SRC_RE = re.compile(r'<img\s[^>]*src="([^"]+)"', re.IGNORECASE)
_IMG_TAG_RE = re.compile(r"<img\s[^>]*/?\s*>", re.IGNORECASE)


def _strip_all_imgs(html: str) -> tuple[str, dict[str, str]]:
    placeholders: dict[str, str] = {}
    idx = 0
    for m in _IMG_SRC_RE.finditer(html):
        src = m.group(1)
        url = QUrl(src)
        if url.scheme() in ("http", "https") and src not in placeholders.values():
            key = f"__IMG_PLACEHOLDER_{idx}__"
            placeholders[key] = src
            idx += 1
    cleaned = _IMG_TAG_RE.sub("", html)
    return cleaned, placeholders


class _ReplyBrowser(QTextBrowser):
    _MAX_IMG_WIDTH = 380

    content_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._nam = QNetworkAccessManager(self)
        self._pending: dict[str, str] = {}
        self._clean_html: str = ""
        self._img_cache: dict[str, QImage] = {}

    def setHtml(self, html: str) -> None:
        clean, placeholders = _strip_all_imgs(html)
        self._clean_html = clean
        super().setHtml(clean)

        for key, src in placeholders.items():
            if src in self._img_cache:
                self._insert_img(src)
                continue
            if src in self._pending.values():
                continue
            self._pending[key] = src
            req = QNetworkRequest(QUrl(src))
            reply = self._nam.get(req)
            reply.finished.connect(lambda _r=reply, _s=src: self._on_loaded(_r, _s))

    def _on_loaded(self, reply: QNetworkReply, src: str) -> None:
        self._pending = {k: v for k, v in self._pending.items() if v != src}

        if reply.error() != QNetworkReply.NetworkError.NoError:
            reply.deleteLater()
            return

        data = reply.readAll()
        reply.deleteLater()

        img = QImage()
        if not img.loadFromData(data.data()):
            return

        if img.width() > self._MAX_IMG_WIDTH:
            img = img.scaledToWidth(
                self._MAX_IMG_WIDTH, Qt.TransformationMode.SmoothTransformation
            )

        self._img_cache[src] = img
        self._insert_img(src)

    def _insert_img(self, src: str) -> None:
        img = self._img_cache.get(src)
        if not img:
            return
        url = QUrl(src)
        self.document().addResource(
            int(QTextDocument.ResourceType.ImageResource), url, img
        )
        img_tag = f'<br><img src="{src}" width="{img.width()}" /><br>'
        html_with_img = self._clean_html + img_tag
        cursor_pos = self.verticalScrollBar().value()
        super().setHtml(html_with_img)
        self._clean_html = html_with_img
        self.verticalScrollBar().setValue(cursor_pos)
        self.content_changed.emit()


class StatusPanel(QWidget):
    approved = Signal()
    denied = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._font_size: int = 9
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

        self._reply_browser = _ReplyBrowser()
        self._reply_browser.setFont(QFont(FONT_FAMILY, 8))
        self._reply_browser.setOpenExternalLinks(True)
        self._reply_browser.setStyleSheet("""
            QTextBrowser {
                color: #c0c0c0;
                background: transparent;
                border: none;
                padding: 2px 4px;
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
        self._reply_browser.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self._reply_browser.hide()
        self._reply_browser.content_changed.connect(self._update_reply_height)
        self._layout.addWidget(self._reply_browser)

    def clear(self) -> None:
        for card in self._cards:
            self._layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()
        self._reply_browser.hide()
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

    def set_font_size(self, size: int) -> None:
        self._font_size = max(6, min(size, 24))

    def _update_reply_height(self) -> None:
        doc_height = int(self._reply_browser.document().size().height()) + 8
        self._reply_browser.setFixedHeight(doc_height)

    def set_reply(self, text: str) -> None:
        if text:
            html = _md_to_html(text, self._font_size)
            self._reply_browser.setHtml(html)
            self._update_reply_height()
            self._reply_browser.show()
        else:
            self._reply_browser.hide()
