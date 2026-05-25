import platform
from typing import Any

from tools.system_control.base import SystemControlBase


def _get_controller() -> SystemControlBase:
    system = platform.system()
    if system == "Darwin":
        from tools.system_control.darwin import DarwinSystemControl

        return DarwinSystemControl()
    elif system == "Windows":
        from tools.system_control.windows import WindowsSystemControl

        return WindowsSystemControl()
    else:
        from tools.system_control.linux import LinuxSystemControl

        return LinuxSystemControl()


_controller: SystemControlBase | None = None


def _ctrl() -> SystemControlBase:
    global _controller
    if _controller is None:
        _controller = _get_controller()
    return _controller


_METHODS_WITH_PARAMS = {
    "set_brightness": ["value"],
    "get_brightness": [],
    "set_dark_mode": ["enabled"],
    "get_dark_mode": [],
    "set_volume": ["value"],
    "get_volume": [],
    "set_mute": ["muted"],
    "set_mic_mute": ["muted"],
    "screenshot": ["path", "region"],
    "media_play_pause": [],
    "media_next": [],
    "media_previous": [],
    "media_now_playing": [],
    "lock_screen": [],
    "sleep": [],
    "shutdown": [],
    "restart": [],
    "battery_info": [],
    "set_wifi": ["enabled"],
    "set_bluetooth": ["enabled"],
    "list_windows": [],
    "focus_window": ["title"],
    "minimize_window": ["title"],
    "maximize_window": ["title"],
    "clipboard_read": [],
    "clipboard_write": ["text"],
    "notify": ["title", "message"],
    "list_apps": [],
    "kill_app": ["name"],
    "focus_app": ["name"],
    "open_file": ["path"],
    "reveal_in_file_manager": ["path"],
    "trash_file": ["path"],
    "system_info": [],
}

_BOOL_PARAMS = {"enabled", "muted"}
_INT_PARAMS = {"value"}


def _cast_param(name: str, value: Any) -> Any:
    if value is None:
        return None
    if name in _BOOL_PARAMS:
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")
        return bool(value)
    if name in _INT_PARAMS:
        return int(value)
    return value


def system_control(task, session=None) -> str:
    method_name = task.name
    if method_name not in _METHODS_WITH_PARAMS:
        available = ", ".join(sorted(_METHODS_WITH_PARAMS.keys()))
        return (
            f"Unknown system_control command: '{method_name}'. Available: {available}"
        )

    ctrl = _ctrl()
    method = getattr(ctrl, method_name)
    param_names = _METHODS_WITH_PARAMS[method_name]

    kwargs = {}
    for p in param_names:
        val = task.params.get(p)
        if val is not None:
            kwargs[p] = _cast_param(p, val)
        elif p in ("region",):
            pass  # optional
        else:
            if p not in task.params:
                continue

    try:
        return method(**kwargs)
    except Exception as e:
        return f"Error executing {method_name}: {e}"
