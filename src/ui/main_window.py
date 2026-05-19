from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QFont, QMouseEvent

from ui.fonts import FONT_FAMILY
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.api_client import AkashiApiClient, SingleExecResult, StepResult
from ui.emotions import Emotion, get_time_of_day, TimeOfDay
from ui.input_bar import InputBar
from ui.status_card import StatusPanel
from ui.tamagotchi import TamagotchiWidget
from ui.weather import WeatherState, fetch_weather


def _friendly_llm_error(raw: str) -> str:
    low = raw.lower()
    if "429" in raw or "quota" in low or "rate" in low:
        return "Квота LLM вичерпана — спробуй пізніше або зміни модель."
    if "401" in raw or "unauthorized" in low or "api_key" in low:
        return "Невірний API ключ — перевір налаштування .env."
    if "403" in raw or "denied" in low or "forbidden" in low:
        return "Доступ заборонено — перевір API ключ та проєкт в Google AI Studio."
    if "timeout" in low:
        return "Час очікування LLM вичерпано — спробуй ще раз."
    if "503" in raw or "overloaded" in low or "experiencing high" in low:
        return "Модель перевантажена — спробуй пізніше або зміни модель."
    if "500" in raw or "internal" in low:
        return "Помилка LLM сервісу — спробуй пізніше."
    return raw[:150]


class FloatingBar(QWidget):
    _WIDTH = 420

    def __init__(self) -> None:
        super().__init__()
        self._drag_pos: QPoint | None = None

        self._last_query: str = ""
        self._observations: list[dict] = []
        self._current_task: dict | None = None
        self._completed_cards: list[dict] = []

        self._setup_window()
        self._build_ui()
        self._connect_signals()
        self._init_context()
        self._greet()

    def _setup_window(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._pin_on_top()
        self.setFixedWidth(self._WIDTH)

    def _build_ui(self) -> None:
        self.setFixedWidth(self._WIDTH)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self._container = QWidget(self)
        self._container.setObjectName("container")
        self._container.setStyleSheet("""
            #container {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #16213e, stop:1 #1a1a2e
                );
                border-radius: 14px;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(Qt.GlobalColor.black)
        self._container.setGraphicsEffect(shadow)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.addWidget(self._container)

        main_layout = QVBoxLayout(self._container)
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(6)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self._tamagotchi = TamagotchiWidget(self._container)
        top_row.addWidget(self._tamagotchi, alignment=Qt.AlignmentFlag.AlignTop)

        self._input = InputBar(self._container)
        top_row.addWidget(
            self._input, stretch=1, alignment=Qt.AlignmentFlag.AlignVCenter
        )

        self._connection_dot = QLabel("●")
        self._connection_dot.setFont(QFont(FONT_FAMILY, 8))
        self._connection_dot.setStyleSheet("color: #888; background: transparent;")
        self._connection_dot.setFixedWidth(14)
        top_row.addWidget(self._connection_dot, alignment=Qt.AlignmentFlag.AlignVCenter)

        main_layout.addLayout(top_row)

        self._separator = QWidget(self._container)
        self._separator.setFixedHeight(1)
        self._separator.setStyleSheet("background: #3a3a5e;")
        self._separator.hide()
        main_layout.addWidget(self._separator)

        self._status_panel = StatusPanel(self._container)
        self._status_panel.hide()
        main_layout.addWidget(self._status_panel)

        self._api = AkashiApiClient()

        self._health_timer = QTimer(self)
        self._health_timer.timeout.connect(self._check_health)
        self._health_timer.start(10_000)
        QTimer.singleShot(500, self._check_health)

    def _connect_signals(self) -> None:
        self._input.submitted.connect(self._on_submit)
        self._api.step_finished.connect(self._on_step_finished)
        self._api.exec_single_finished.connect(self._on_exec_single_finished)
        self._status_panel.approved.connect(self._on_approve)
        self._status_panel.denied.connect(self._on_deny)

    def _init_context(self) -> None:
        tod = get_time_of_day()
        if tod != TimeOfDay.DAY:
            self._tamagotchi.set_time_of_day(tod.value)

        weather = fetch_weather()
        if weather != WeatherState.CLEAR:
            self._tamagotchi.set_weather(weather.value)

    def _greet(self) -> None:
        self._tamagotchi.set_emotion(Emotion.GREETING)

    # -- ReAct flow --

    def _on_submit(self, text: str) -> None:
        self._input.set_busy(True)
        self._last_query = text
        self._observations = []
        self._current_task = None
        self._completed_cards = []

        self._status_panel.clear()
        self._status_panel.show()
        self._separator.show()
        self._tamagotchi.set_emotion(Emotion.THINKING)

        self._api.send_step(text, [])
        self._adjust_height()

    def _on_step_finished(self, result: StepResult) -> None:
        if result.error:
            self._input.set_busy(False)
            self._tamagotchi.set_emotion(Emotion.SAD)
            self._status_panel.set_tasks(
                self._completed_cards + [{"name": result.error, "status": "error"}]
            )
            self._adjust_height()
            QTimer.singleShot(5000, lambda: self._tamagotchi.set_emotion(Emotion.IDLE))
            return

        if result.done:
            self._input.set_busy(False)
            reply = result.reply or ""
            is_error = reply.startswith("[LLM Error]")

            if is_error:
                friendly = _friendly_llm_error(reply)
            else:
                friendly = ""

            def _show_summary() -> None:
                self._status_panel.clear()
                if is_error:
                    self._status_panel.set_reply(friendly)
                    self._tamagotchi.set_emotion(Emotion.SAD)
                elif reply:
                    self._status_panel.set_reply(reply)
                    self._tamagotchi.set_emotion(Emotion.HAPPY)
                else:
                    self._tamagotchi.set_emotion(Emotion.HAPPY)
                self._adjust_height()

            self._status_panel.set_tasks(self._completed_cards)
            self._adjust_height()
            QTimer.singleShot(1500, _show_summary)
            return

        if result.task:
            self._current_task = result.task
            pending_card = {"name": result.task["name"], "status": "pending"}
            self._status_panel.set_tasks(self._completed_cards + [pending_card])
            self._status_panel.show_approve_buttons(True)
            self._adjust_height()

    def _on_approve(self) -> None:
        self._status_panel.show_approve_buttons(False)
        if not self._current_task:
            return

        running_card = {"name": self._current_task["name"], "status": "running"}
        self._status_panel.set_tasks(self._completed_cards + [running_card])
        self._tamagotchi.set_emotion(Emotion.THINKING)
        self._api.send_exec_single(self._current_task)
        self._adjust_height()

    def _on_deny(self) -> None:
        self._status_panel.show_approve_buttons(False)
        self._input.set_busy(False)

        if self._current_task:
            self._completed_cards.append(
                {"name": self._current_task["name"], "status": "skipped"}
            )
            self._observations.append(
                {
                    "action": self._current_task["action"],
                    "name": self._current_task["name"],
                    "params": self._current_task.get("params", {}),
                    "skipped": True,
                }
            )

        self._current_task = None
        self._status_panel.set_tasks(self._completed_cards)
        self._tamagotchi.set_emotion(Emotion.IDLE)
        self._adjust_height()

    def _on_exec_single_finished(self, result: SingleExecResult) -> None:
        if result.error:
            self._completed_cards.append({"name": result.error, "status": "error"})
            self._status_panel.set_tasks(self._completed_cards)
            self._input.set_busy(False)
            self._tamagotchi.set_emotion(Emotion.SAD)
            self._adjust_height()
            return

        status = result.status.lower()
        self._completed_cards.append({"name": result.name, "status": status})

        self._observations.append(
            {
                "action": result.action,
                "name": result.name,
                "params": (
                    self._current_task.get("params", {}) if self._current_task else {}
                ),
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "skipped": result.skipped,
            }
        )

        self._current_task = None

        thinking_card = {"name": "Thinking about next step…", "status": "running"}
        self._status_panel.set_tasks(self._completed_cards + [thinking_card])
        self._adjust_height()

        self._tamagotchi.set_emotion(Emotion.THINKING)
        self._api.send_step(self._last_query, self._observations)

    def _hide_panel(self) -> None:
        if not self._input.isEnabled():
            return
        self._status_panel.clear()
        self._status_panel.hide()
        self._separator.hide()
        self._adjust_height()

    # -- health / resize --

    def _check_health(self) -> None:
        healthy = self._api.check_health()
        if healthy:
            self._connection_dot.setStyleSheet(
                "color: #06d6a0; background: transparent;"
            )
            self._connection_dot.setToolTip("API connected")
        else:
            self._connection_dot.setStyleSheet(
                "color: #ef476f; background: transparent;"
            )
            self._connection_dot.setToolTip("API offline")

    def _adjust_height(self) -> None:
        QTimer.singleShot(0, self._do_resize)

    def _do_resize(self) -> None:
        self._container.adjustSize()
        h = self._container.sizeHint().height() + 16
        self.setFixedHeight(max(h, 96))

    def _pin_on_top(self) -> None:
        import platform

        if platform.system() != "Darwin":
            return
        try:
            import ctypes
            import ctypes.util

            objc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))
            objc.objc_getClass.restype = ctypes.c_void_p
            objc.sel_registerName.restype = ctypes.c_void_p
            objc.objc_msgSend.restype = ctypes.c_void_p
            objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

            NSApp = objc.objc_msgSend(
                objc.objc_getClass(b"NSApplication"),
                objc.sel_registerName(b"sharedApplication"),
            )

            windows_sel = objc.sel_registerName(b"windows")
            windows = objc.objc_msgSend(NSApp, windows_sel)

            count_sel = objc.sel_registerName(b"count")
            count_fn = ctypes.CFUNCTYPE(
                ctypes.c_ulong, ctypes.c_void_p, ctypes.c_void_p
            )
            count = count_fn(objc.objc_msgSend)(windows, count_sel)

            obj_at_sel = objc.sel_registerName(b"objectAtIndex:")
            obj_at_fn = ctypes.CFUNCTYPE(
                ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong
            )

            set_level_sel = objc.sel_registerName(b"setLevel:")
            set_level_fn = ctypes.CFUNCTYPE(
                None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long
            )

            set_behavior_sel = objc.sel_registerName(b"setCollectionBehavior:")
            set_behavior_fn = ctypes.CFUNCTYPE(
                None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong
            )

            NSFloatingWindowLevel = 3
            canJoinAllSpaces = 1 << 0
            stationary = 1 << 4

            for i in range(count):
                win = obj_at_fn(objc.objc_msgSend)(windows, obj_at_sel, i)
                set_level_fn(objc.objc_msgSend)(
                    win, set_level_sel, NSFloatingWindowLevel + 1
                )
                set_behavior_fn(objc.objc_msgSend)(
                    win, set_behavior_sel, canJoinAllSpaces | stationary
                )
        except Exception:
            pass

    # --- Dragging ---

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
