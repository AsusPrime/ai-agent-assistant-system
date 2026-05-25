import json
import os
import subprocess

from tools.system_control.base import SystemControlBase


def _osa(script: str) -> str:
    r = subprocess.run(
        ["osascript", "-e", script], capture_output=True, text=True, timeout=10
    )
    return r.stdout.strip() or r.stderr.strip()


def _run(cmd: list[str], timeout: int = 10) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        return f"Error: '{cmd[0]}' not found. Install it first."
    out = r.stdout.strip()
    if r.returncode != 0 and r.stderr.strip():
        return f"Error: {r.stderr.strip()}"
    return out


class DarwinSystemControl(SystemControlBase):

    # -- Display --

    def set_brightness(self, value: int) -> str:
        v = max(0, min(100, value))
        frac = v / 100.0
        try:
            from ctypes import cdll, c_float, c_uint32

            CoreDisplay = cdll.LoadLibrary(
                "/System/Library/Frameworks/CoreDisplay.framework/CoreDisplay"
            )
            CoreDisplay.CoreDisplay_Display_SetUserBrightness.argtypes = [
                c_uint32,
                c_float,
            ]
            CoreDisplay.CoreDisplay_Display_SetUserBrightness(0, c_float(frac))
            return f"Brightness set to {v}%"
        except Exception:
            _osa(
                f'tell application "System Events" to key code {144 if v > 50 else 145}'
            )
            return "Brightness adjusted (key event)"

    def get_brightness(self) -> str:
        try:
            from ctypes import cdll, c_float, c_uint32

            CoreDisplay = cdll.LoadLibrary(
                "/System/Library/Frameworks/CoreDisplay.framework/CoreDisplay"
            )
            CoreDisplay.CoreDisplay_Display_GetUserBrightness.restype = c_float
            CoreDisplay.CoreDisplay_Display_GetUserBrightness.argtypes = [c_uint32]
            val = CoreDisplay.CoreDisplay_Display_GetUserBrightness(0)
            return f"Brightness: {int(val * 100)}%"
        except Exception as e:
            return f"Cannot read brightness: {e}"

    def set_dark_mode(self, enabled: bool) -> str:
        val = "true" if enabled else "false"
        _osa(
            f'tell application "System Events" to tell appearance preferences to set dark mode to {val}'
        )
        return f"Dark mode {'enabled' if enabled else 'disabled'}"

    def get_dark_mode(self) -> str:
        r = _osa(
            'tell application "System Events" to tell appearance preferences to get dark mode'
        )
        return f"Dark mode: {r}"

    # -- Audio --

    def set_volume(self, value: int) -> str:
        v = max(0, min(100, value))
        _osa(f"set volume output volume {v}")
        return f"Volume set to {v}%"

    def get_volume(self) -> str:
        r = _osa("output volume of (get volume settings)")
        return f"Volume: {r}%"

    def set_mute(self, muted: bool) -> str:
        _osa(f"set volume output muted {'true' if muted else 'false'}")
        return f"Output {'muted' if muted else 'unmuted'}"

    def set_mic_mute(self, muted: bool) -> str:
        _osa(f"set volume input volume {'0' if muted else '100'}")
        return f"Microphone {'muted' if muted else 'unmuted'}"

    # -- Screenshots --

    def screenshot(self, path: str, region: str | None = None) -> str:
        path = os.path.expanduser(path)
        cmd = ["screencapture"]
        if region:
            cmd.extend(["-R", region])
        cmd.append(path)
        return _run(cmd) or f"Screenshot saved: {path}"

    # -- Power --

    def lock_screen(self) -> str:
        _run(
            [
                "/System/Library/CoreServices/Menu Extras/User.menu"
                "/Contents/Resources/CGSession",
                "-suspend",
            ]
        )
        return "Screen locked"

    def sleep(self) -> str:
        _run(["pmset", "sleepnow"])
        return "Going to sleep"

    def shutdown(self) -> str:
        _osa('tell application "System Events" to shut down')
        return "Shutting down"

    def restart(self) -> str:
        _osa('tell application "System Events" to restart')
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
            return _run(["pmset", "-g", "batt"])

    # -- Network --

    def set_wifi(self, enabled: bool) -> str:
        state = "on" if enabled else "off"
        _run(["networksetup", "-setairportpower", "en0", state])
        return f"Wi-Fi turned {state}"

    def set_bluetooth(self, enabled: bool) -> str:
        state = "1" if enabled else "0"
        r = _run(["blueutil", "--power", state])
        if "Error" in r:
            return "blueutil not installed. Install with: brew install blueutil"
        return f"Bluetooth turned {'on' if enabled else 'off'}"

    # -- Windows --

    def list_windows(self) -> str:
        script = """
        tell application "System Events"
            set windowList to {}
            repeat with proc in (every process whose visible is true)
                set procName to name of proc
                try
                    repeat with w in (every window of proc)
                        set end of windowList to procName & ": " & name of w
                    end repeat
                end try
            end repeat
            return windowList as text
        end tell
        """
        return _osa(script) or "No windows found"

    def focus_window(self, title: str) -> str:
        script = f"""
        tell application "System Events"
            repeat with proc in (every process whose visible is true)
                try
                    repeat with w in (every window of proc)
                        if name of w contains "{title}" then
                            set frontmost of proc to true
                            perform action "AXRaise" of w
                            return "Focused: " & name of w
                        end if
                    end repeat
                end try
            end repeat
        end tell
        return "Window not found: {title}"
        """
        return _osa(script)

    def minimize_window(self, title: str) -> str:
        script = f"""
        tell application "System Events"
            repeat with proc in (every process whose visible is true)
                try
                    repeat with w in (every window of proc)
                        if name of w contains "{title}" then
                            click (first button of w whose subrole is "AXMinimizeButton")
                            return "Minimized"
                        end if
                    end repeat
                end try
            end repeat
        end tell
        return "Window not found"
        """
        return _osa(script)

    def maximize_window(self, title: str) -> str:
        script = f"""
        tell application "System Events"
            repeat with proc in (every process whose visible is true)
                try
                    repeat with w in (every window of proc)
                        if name of w contains "{title}" then
                            click (first button of w whose subrole is "AXFullScreenButton")
                            return "Maximized"
                        end if
                    end repeat
                end try
            end repeat
        end tell
        return "Window not found"
        """
        return _osa(script)

    # -- Media --

    def media_play_pause(self) -> str:
        script = """
        try
            tell application "Spotify"
                if player state is playing then
                    pause
                else
                    play
                end if
            end tell
            return "Media: play/pause toggled (Spotify)"
        on error
            try
                tell application "Music"
                    playpause
                end tell
                return "Media: play/pause toggled (Music)"
            on error
                return "No media player running"
            end try
        end try
        """
        return _osa(script)

    def media_next(self) -> str:
        script = """
        try
            tell application "Spotify"
                next track
            end tell
            return "Media: next track (Spotify)"
        on error
            try
                tell application "Music"
                    next track
                end tell
                return "Media: next track (Music)"
            on error
                return "No media player running"
            end try
        end try
        """
        return _osa(script)

    def media_previous(self) -> str:
        script = """
        try
            tell application "Spotify"
                previous track
            end tell
            return "Media: previous track (Spotify)"
        on error
            try
                tell application "Music"
                    previous track
                end tell
                return "Media: previous track (Music)"
            on error
                return "No media player running"
            end try
        end try
        """
        return _osa(script)

    def media_now_playing(self) -> str:
        script = """
        set output to ""
        try
            tell application "System Events"
                set musicRunning to (exists process "Music")
                set spotifyRunning to (exists process "Spotify")
            end tell
            if spotifyRunning then
                tell application "Spotify"
                    set output to "Spotify: " & artist of current track & " - " & name of current track
                end tell
            else if musicRunning then
                tell application "Music"
                    set output to "Music: " & artist of current track & " - " & name of current track
                end tell
            else
                set output to "No media player running"
            end if
        on error
            set output to "No media playing"
        end try
        return output
        """
        r = _osa(script)
        return r or "No media playing"

    # -- Clipboard --

    def clipboard_read(self) -> str:
        r = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=5)
        return r.stdout

    def clipboard_write(self, text: str) -> str:
        subprocess.run(["pbcopy"], input=text.encode(), timeout=5)
        return "Text copied to clipboard"

    # -- Notifications --

    def notify(self, title: str, message: str) -> str:
        _osa(f'display notification "{message}" with title "{title}"')
        return f"Notification sent: {title}"

    # -- Applications --

    def list_apps(self) -> str:
        try:
            import psutil

            apps = []
            for p in psutil.process_iter(["pid", "name"]):
                apps.append({"pid": p.info["pid"], "name": p.info["name"]})
            return json.dumps(apps[:50])
        except ImportError:
            return _run(["ps", "aux"])

    def kill_app(self, name: str) -> str:
        return _run(["pkill", "-f", name])

    def focus_app(self, name: str) -> str:
        _osa(f'tell application "{name}" to activate')
        return f"Focused: {name}"

    # -- Files --

    def open_file(self, path: str) -> str:
        path = os.path.expanduser(path)
        _run(["open", path])
        return f"Opened: {path}"

    def reveal_in_file_manager(self, path: str) -> str:
        path = os.path.expanduser(path)
        _run(["open", "-R", path])
        return f"Revealed: {path}"

    def trash_file(self, path: str) -> str:
        path = os.path.expanduser(path)
        try:
            from send2trash import send2trash

            send2trash(path)
            return f"Moved to Trash: {path}"
        except ImportError:
            _osa(f'tell application "Finder" to delete POSIX file "{path}"')
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
            return json.dumps(info)
        except ImportError:
            return _run(
                ["system_profiler", "SPSoftwareDataType", "-detailLevel", "mini"]
            )
