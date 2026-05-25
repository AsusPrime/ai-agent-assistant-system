from abc import ABC, abstractmethod


class SystemControlBase(ABC):

    # -- Display --

    @abstractmethod
    def set_brightness(self, value: int) -> str: ...

    @abstractmethod
    def get_brightness(self) -> str: ...

    @abstractmethod
    def set_dark_mode(self, enabled: bool) -> str: ...

    @abstractmethod
    def get_dark_mode(self) -> str: ...

    # -- Audio --

    @abstractmethod
    def set_volume(self, value: int) -> str: ...

    @abstractmethod
    def get_volume(self) -> str: ...

    @abstractmethod
    def set_mute(self, muted: bool) -> str: ...

    @abstractmethod
    def set_mic_mute(self, muted: bool) -> str: ...

    # -- Screenshots --

    @abstractmethod
    def screenshot(self, path: str, region: str | None = None) -> str: ...

    # -- Power --

    @abstractmethod
    def lock_screen(self) -> str: ...

    @abstractmethod
    def sleep(self) -> str: ...

    @abstractmethod
    def shutdown(self) -> str: ...

    @abstractmethod
    def restart(self) -> str: ...

    @abstractmethod
    def battery_info(self) -> str: ...

    # -- Network --

    @abstractmethod
    def set_wifi(self, enabled: bool) -> str: ...

    @abstractmethod
    def set_bluetooth(self, enabled: bool) -> str: ...

    # -- Windows --

    @abstractmethod
    def list_windows(self) -> str: ...

    @abstractmethod
    def focus_window(self, title: str) -> str: ...

    @abstractmethod
    def minimize_window(self, title: str) -> str: ...

    @abstractmethod
    def maximize_window(self, title: str) -> str: ...

    # -- Media --

    @abstractmethod
    def media_play_pause(self) -> str: ...

    @abstractmethod
    def media_next(self) -> str: ...

    @abstractmethod
    def media_previous(self) -> str: ...

    @abstractmethod
    def media_now_playing(self) -> str: ...

    # -- Clipboard --

    @abstractmethod
    def clipboard_read(self) -> str: ...

    @abstractmethod
    def clipboard_write(self, text: str) -> str: ...

    # -- Notifications --

    @abstractmethod
    def notify(self, title: str, message: str) -> str: ...

    # -- Applications --

    @abstractmethod
    def list_apps(self) -> str: ...

    @abstractmethod
    def kill_app(self, name: str) -> str: ...

    @abstractmethod
    def focus_app(self, name: str) -> str: ...

    # -- Files --

    @abstractmethod
    def open_file(self, path: str) -> str: ...

    @abstractmethod
    def reveal_in_file_manager(self, path: str) -> str: ...

    @abstractmethod
    def trash_file(self, path: str) -> str: ...

    # -- System Info --

    @abstractmethod
    def system_info(self) -> str: ...
