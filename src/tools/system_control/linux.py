import json
import os
import subprocess

from tools.system_control.base import SystemControlBase


def _run(cmd: list[str], timeout: int = 10) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        return f"Error: '{cmd[0]}' not found. Install it first."
    out = r.stdout.strip()
    if r.returncode != 0 and r.stderr.strip():
        return f"Error: {r.stderr.strip()}"
    return out


class LinuxSystemControl(SystemControlBase):

    # -- Display --

    def set_brightness(self, value: int) -> str:
        v = max(0, min(100, value))
        return _run(["brightnessctl", "s", f"{v}%"]) or f"Brightness set to {v}%"

    def get_brightness(self) -> str:
        r = _run(["brightnessctl", "g"])
        m = _run(["brightnessctl", "m"])
        try:
            pct = int(int(r) / int(m) * 100)
            return f"Brightness: {pct}%"
        except (ValueError, ZeroDivisionError):
            return f"Brightness: {r}/{m}"

    def set_dark_mode(self, enabled: bool) -> str:
        scheme = "prefer-dark" if enabled else "prefer-light"
        _run(
            ["gsettings", "set", "org.gnome.desktop.interface", "color-scheme", scheme]
        )
        return f"Dark mode {'enabled' if enabled else 'disabled'} (GNOME)"

    def get_dark_mode(self) -> str:
        r = _run(["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"])
        return f"Dark mode: {r}"

    # -- Audio --

    def set_volume(self, value: int) -> str:
        v = max(0, min(100, value))
        _run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{v}%"])
        return f"Volume set to {v}%"

    def get_volume(self) -> str:
        r = _run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"])
        return f"Volume: {r}"

    def set_mute(self, muted: bool) -> str:
        val = "1" if muted else "0"
        _run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", val])
        return f"Output {'muted' if muted else 'unmuted'}"

    def set_mic_mute(self, muted: bool) -> str:
        val = "1" if muted else "0"
        _run(["pactl", "set-source-mute", "@DEFAULT_SOURCE@", val])
        return f"Microphone {'muted' if muted else 'unmuted'}"

    # -- Screenshots --

    def screenshot(self, path: str, region: str | None = None) -> str:
        path = os.path.expanduser(path)
        try:
            import mss

            with mss.mss() as s:
                if region:
                    parts = [int(x) for x in region.split(",")]
                    monitor = {
                        "left": parts[0],
                        "top": parts[1],
                        "width": parts[2],
                        "height": parts[3],
                    }
                    s.shot(mon=monitor, output=path)
                else:
                    s.shot(output=path)
            return f"Screenshot saved: {path}"
        except ImportError:
            if region:
                return (
                    _run(["scrot", "-a", region, path]) or f"Screenshot saved: {path}"
                )
            return _run(["scrot", path]) or f"Screenshot saved: {path}"

    # -- Power --

    def lock_screen(self) -> str:
        _run(["loginctl", "lock-session"])
        return "Screen locked"

    def sleep(self) -> str:
        _run(["systemctl", "suspend"])
        return "Going to sleep"

    def shutdown(self) -> str:
        _run(["shutdown", "-h", "now"])
        return "Shutting down"

    def restart(self) -> str:
        _run(["shutdown", "-r", "now"])
        return "Restarting"

    def battery_info(self) -> str:
        try:
            import psutil

            b = psutil.sensors_battery()
            if b is None:
                return "No battery detected"
            return json.dumps(
                {
                    "percent": b.percent,
                    "plugged_in": b.power_plugged,
                    "seconds_left": b.secsleft if b.secsleft > 0 else None,
                }
            )
        except ImportError:
            return _run(
                ["upower", "-i", "/org/freedesktop/UPower/devices/battery_BAT0"]
            )

    # -- Network --

    def set_wifi(self, enabled: bool) -> str:
        state = "on" if enabled else "off"
        _run(["nmcli", "radio", "wifi", state])
        return f"Wi-Fi turned {state}"

    def set_bluetooth(self, enabled: bool) -> str:
        state = "on" if enabled else "off"
        _run(["bluetoothctl", "power", state])
        return f"Bluetooth turned {state}"

    # -- Windows --

    def list_windows(self) -> str:
        try:
            import pywinctl

            wins = pywinctl.getAllWindows()
            items = [{"title": w.title} for w in wins if w.title.strip()]
            return json.dumps(items[:50])
        except ImportError:
            return _run(["wmctrl", "-l"])

    def focus_window(self, title: str) -> str:
        try:
            import pywinctl

            wins = pywinctl.getWindowsWithTitle(title)
            if wins:
                wins[0].activate()
                return f"Focused: {wins[0].title}"
        except ImportError:
            _run(["xdotool", "search", "--name", title, "windowactivate"])
            return f"Focused: {title}"
        return f"Window not found: {title}"

    def minimize_window(self, title: str) -> str:
        _run(["xdotool", "search", "--name", title, "windowminimize"])
        return "Minimized"

    def maximize_window(self, title: str) -> str:
        wid = _run(["xdotool", "search", "--name", title])
        if wid:
            _run(
                [
                    "wmctrl",
                    "-i",
                    "-r",
                    wid.split()[0],
                    "-b",
                    "add,maximized_vert,maximized_horz",
                ]
            )
        return "Maximized"

    # -- Media --

    def media_play_pause(self) -> str:
        r = _run(["playerctl", "play-pause"])
        if "Error" in r:
            return r
        return "Media: play/pause toggled"

    def media_next(self) -> str:
        r = _run(["playerctl", "next"])
        if "Error" in r:
            return r
        return "Media: next track"

    def media_previous(self) -> str:
        r = _run(["playerctl", "previous"])
        if "Error" in r:
            return r
        return "Media: previous track"

    def media_now_playing(self) -> str:
        status = _run(["playerctl", "status"])
        if "Error" in status:
            return status
        metadata = _run(["playerctl", "metadata", "--format", "{{artist}} - {{title}}"])
        return f"{status}: {metadata}" if metadata else status

    # -- Clipboard --

    def clipboard_read(self) -> str:
        return _run(["xclip", "-selection", "clipboard", "-o"])

    def clipboard_write(self, text: str) -> str:
        subprocess.run(
            ["xclip", "-selection", "clipboard"],
            input=text.encode(),
            timeout=5,
        )
        return "Text copied to clipboard"

    # -- Notifications --

    def notify(self, title: str, message: str) -> str:
        _run(["notify-send", title, message])
        return f"Notification sent: {title}"

    # -- Applications --

    def list_apps(self) -> str:
        try:
            import psutil

            apps = [
                {"pid": p.info["pid"], "name": p.info["name"]}
                for p in psutil.process_iter(["pid", "name"])
            ]
            return json.dumps(apps[:50])
        except ImportError:
            return _run(["ps", "aux", "--sort=-%mem"])

    def kill_app(self, name: str) -> str:
        return _run(["pkill", "-f", name])

    def focus_app(self, name: str) -> str:
        _run(["xdotool", "search", "--name", name, "windowactivate"])
        return f"Focused: {name}"

    # -- Files --

    def open_file(self, path: str) -> str:
        path = os.path.expanduser(path)
        _run(["xdg-open", path])
        return f"Opened: {path}"

    def reveal_in_file_manager(self, path: str) -> str:
        path = os.path.expanduser(path)
        _run(["xdg-open", os.path.dirname(path)])
        return f"Revealed: {path}"

    def trash_file(self, path: str) -> str:
        path = os.path.expanduser(path)
        try:
            from send2trash import send2trash

            send2trash(path)
            return f"Moved to Trash: {path}"
        except ImportError:
            _run(["gio", "trash", path])
            return f"Moved to Trash: {path}"

    # -- System Info --

    def system_info(self) -> str:
        try:
            import psutil

            info = {
                "cpu_percent": psutil.cpu_percent(interval=0.5),
                "ram_percent": psutil.virtual_memory().percent,
                "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 1),
                "disk_percent": psutil.disk_usage("/").percent,
            }
            batt = psutil.sensors_battery()
            if batt:
                info["battery_percent"] = batt.percent
                info["plugged_in"] = batt.power_plugged
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    if entries:
                        info["cpu_temp"] = entries[0].current
                        break
            return json.dumps(info)
        except ImportError:
            return _run(["cat", "/proc/meminfo"])
