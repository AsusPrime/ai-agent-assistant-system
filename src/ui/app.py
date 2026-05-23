from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from ui.main_window import FloatingBar

_ASSETS = Path(__file__).resolve().parent / "assets"


class AssistantApp:
    def __init__(self) -> None:
        self._app = QApplication(sys.argv)
        self._app.setApplicationName("AI Assistant")
        self._app.setQuitOnLastWindowClosed(False)

        self._bar = FloatingBar()
        self._tray = self._build_tray()

    def _build_tray(self) -> QSystemTrayIcon:
        icon_path = _ASSETS / "icon.svg"
        icon = QIcon(str(icon_path)) if icon_path.exists() else QIcon()

        tray = QSystemTrayIcon(icon, self._app)

        menu = QMenu()

        show_action = QAction("Show / Hide", menu)
        show_action.triggered.connect(self._toggle_bar)
        menu.addAction(show_action)

        menu.addSeparator()

        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        tray.setContextMenu(menu)
        tray.activated.connect(self._on_tray_activated)
        tray.setToolTip("AI Assistant")
        tray.show()
        return tray

    def _toggle_bar(self) -> None:
        if self._bar.isVisible():
            self._bar.hide()
        else:
            self._bar.show()
            self._bar.raise_()
            self._bar.activateWindow()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        import platform

        if platform.system() == "Darwin":
            return
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._toggle_bar()

    def _quit(self) -> None:
        self._bar.close()
        self._tray.hide()
        self._app.quit()

    def run(self) -> int:
        self._position_bar()
        self._bar.show()
        return self._app.exec()

    def _position_bar(self) -> None:
        screen = self._app.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.center().x() - self._bar.width() // 2
            y = geo.top() + 20
            self._bar.move(x, y)


def main() -> None:
    app = AssistantApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
