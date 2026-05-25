import json
import os
import subprocess

from tools.system_control.base import SystemControlBase


def _ps(script: str, timeout: int = 10) -> str:
    r = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    out = r.stdout.strip()
    if r.returncode != 0 and r.stderr.strip():
        return f"Error: {r.stderr.strip()}"
    return out


def _run(cmd: list[str], timeout: int = 10) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        return f"Error: '{cmd[0]}' not found. Install it first."
    out = r.stdout.strip()
    if r.returncode != 0 and r.stderr.strip():
        return f"Error: {r.stderr.strip()}"
    return out


class WindowsSystemControl(SystemControlBase):

    # -- Display --

    def set_brightness(self, value: int) -> str:
        v = max(0, min(100, value))
        _ps(
            f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{v})"
        )
        return f"Brightness set to {v}%"

    def get_brightness(self) -> str:
        r = _ps(
            "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness"
        )
        return f"Brightness: {r}%"

    def set_dark_mode(self, enabled: bool) -> str:
        val = "0" if enabled else "1"
        _ps(
            f'Set-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" -Name "AppsUseLightTheme" -Value {val}'
        )
        _ps(
            f'Set-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" -Name "SystemUsesLightTheme" -Value {val}'
        )
        return f"Dark mode {'enabled' if enabled else 'disabled'}"

    def get_dark_mode(self) -> str:
        r = _ps(
            '(Get-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize").AppsUseLightTheme'
        )
        is_dark = r.strip() == "0"
        return f"Dark mode: {'on' if is_dark else 'off'}"

    # -- Audio --

    def set_volume(self, value: int) -> str:
        v = max(0, min(100, value))
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(v / 100.0, None)
            return f"Volume set to {v}%"
        except ImportError:
            _ps(f"""
            $obj = New-Object -ComObject WScript.Shell
            1..50 | ForEach-Object {{ $obj.SendKeys([char]174) }}
            1..{v // 2} | ForEach-Object {{ $obj.SendKeys([char]175) }}
            """)
            return f"Volume adjusted to ~{v}%"

    def get_volume(self) -> str:
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            level = volume.GetMasterVolumeLevelScalar()
            return f"Volume: {int(level * 100)}%"
        except ImportError:
            return "pycaw not installed"

    def set_mute(self, muted: bool) -> str:
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMute(1 if muted else 0, None)
            return f"Output {'muted' if muted else 'unmuted'}"
        except ImportError:
            return "pycaw not installed"

    def set_mic_mute(self, muted: bool) -> str:
        _ps("""
        $mic = Get-WmiObject Win32_SoundDevice | Select-Object -First 1
        # Fallback: toggle via SendKeys
        $shell = New-Object -ComObject WScript.Shell
        """)
        return f"Microphone {'muted' if muted else 'unmuted'} (best effort)"

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
            _ps(
                "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Screen]::PrimaryScreen | Out-Null"
            )
            return "mss not installed, install with: pip install mss"

    # -- Power --

    def lock_screen(self) -> str:
        import ctypes

        ctypes.windll.user32.LockWorkStation()
        return "Screen locked"

    def sleep(self) -> str:
        _run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
        return "Going to sleep"

    def shutdown(self) -> str:
        _run(["shutdown", "/s", "/t", "0"])
        return "Shutting down"

    def restart(self) -> str:
        _run(["shutdown", "/r", "/t", "0"])
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
            return _ps(
                "Get-WmiObject Win32_Battery | Select-Object EstimatedChargeRemaining, BatteryStatus | ConvertTo-Json"
            )

    # -- Network --

    def set_wifi(self, enabled: bool) -> str:
        action = "Enable" if enabled else "Disable"
        _ps(f"{action}-NetAdapter -Name 'Wi-Fi' -Confirm:$false")
        return f"Wi-Fi turned {'on' if enabled else 'off'}"

    def set_bluetooth(self, enabled: bool) -> str:
        action = "Enable" if enabled else "Disable"
        _ps(f"Get-PnpDevice -Class Bluetooth | {action}-PnpDevice -Confirm:$false")
        return f"Bluetooth turned {'on' if enabled else 'off'}"

    # -- Windows --

    def list_windows(self) -> str:
        try:
            import pywinctl

            wins = pywinctl.getAllWindows()
            items = [{"title": w.title, "app": ""} for w in wins if w.title.strip()]
            return json.dumps(items[:50])
        except ImportError:
            r = _ps(
                "Get-Process | Where-Object {$_.MainWindowTitle -ne ''} | Select-Object ProcessName, MainWindowTitle | ConvertTo-Json"
            )
            return r

    def focus_window(self, title: str) -> str:
        try:
            import pywinctl

            wins = pywinctl.getWindowsWithTitle(title)
            if wins:
                wins[0].activate()
                return f"Focused: {wins[0].title}"
            return f"Window not found: {title}"
        except ImportError:
            return "pywinctl not installed"

    def minimize_window(self, title: str) -> str:
        try:
            import pywinctl

            wins = pywinctl.getWindowsWithTitle(title)
            if wins:
                wins[0].minimize()
                return "Minimized"
            return "Window not found"
        except ImportError:
            return "pywinctl not installed"

    def maximize_window(self, title: str) -> str:
        try:
            import pywinctl

            wins = pywinctl.getWindowsWithTitle(title)
            if wins:
                wins[0].maximize()
                return "Maximized"
            return "Window not found"
        except ImportError:
            return "pywinctl not installed"

    # -- Media --

    def _send_media_key(self, vk_code: int) -> None:
        import ctypes

        KEYEVENTF_EXTENDEDKEY = 0x0001
        KEYEVENTF_KEYUP = 0x0002
        ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY, 0)
        ctypes.windll.user32.keybd_event(
            vk_code, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0
        )

    def media_play_pause(self) -> str:
        self._send_media_key(0xB3)
        return "Media: play/pause toggled"

    def media_next(self) -> str:
        self._send_media_key(0xB0)
        return "Media: next track"

    def media_previous(self) -> str:
        self._send_media_key(0xB1)
        return "Media: previous track"

    def media_now_playing(self) -> str:
        script = """
        Add-Type -AssemblyName System.Runtime.WindowsRuntime
        $null = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager, Windows.Media.Control, ContentType = WindowsRuntime]
        $asyncOp = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager]::RequestAsync()
        $sessManager = $asyncOp.GetAwaiter().GetResult()
        $session = $sessManager.GetCurrentSession()
        if ($session) {
            $mediaProps = $session.TryGetMediaPropertiesAsync().GetAwaiter().GetResult()
            "$($mediaProps.Artist) - $($mediaProps.Title)"
        } else {
            "No media playing"
        }
        """
        r = _ps(script)
        return r or "No media playing"

    # -- Clipboard --

    def clipboard_read(self) -> str:
        return _ps("Get-Clipboard")

    def clipboard_write(self, text: str) -> str:
        _ps(f"Set-Clipboard -Value '{text}'")
        return "Text copied to clipboard"

    # -- Notifications --

    def notify(self, title: str, message: str) -> str:
        _ps(f"""
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
        $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(0)
        $text = $template.GetElementsByTagName("text")
        $text.Item(0).AppendChild($template.CreateTextNode("{title}: {message}")) > $null
        $notif = [Windows.UI.Notifications.ToastNotification]::new($template)
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("AI Assistant").Show($notif)
        """)
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
            return _ps(
                "Get-Process | Select-Object -First 50 Id, ProcessName | ConvertTo-Json"
            )

    def kill_app(self, name: str) -> str:
        _run(["taskkill", "/IM", name, "/F"])
        return f"Killed: {name}"

    def focus_app(self, name: str) -> str:
        try:
            import pywinctl

            wins = pywinctl.getWindowsWithTitle(name)
            if wins:
                wins[0].activate()
                return f"Focused: {name}"
        except ImportError:
            pass
        return f"Could not focus: {name}"

    # -- Files --

    def open_file(self, path: str) -> str:
        path = os.path.expanduser(path)
        os.startfile(path)
        return f"Opened: {path}"

    def reveal_in_file_manager(self, path: str) -> str:
        path = os.path.expanduser(path)
        _run(["explorer", f"/select,{path}"])
        return f"Revealed: {path}"

    def trash_file(self, path: str) -> str:
        path = os.path.expanduser(path)
        try:
            from send2trash import send2trash

            send2trash(path)
            return f"Moved to Recycle Bin: {path}"
        except ImportError:
            _ps(f"""
            $shell = New-Object -ComObject Shell.Application
            $item = $shell.Namespace(0).ParseName("{path}")
            $item.InvokeVerb("delete")
            """)
            return f"Moved to Recycle Bin: {path}"

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
            return _ps(
                "Get-ComputerInfo | Select-Object CsProcessors, OsTotalVisibleMemorySize | ConvertTo-Json"
            )
