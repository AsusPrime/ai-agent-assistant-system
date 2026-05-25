"""
Manual test for DarwinSystemControl.
Run on macOS: cd src && python -m pytest ../tests/test_system_control_darwin.py -v -s
Or directly:  cd src && python ../tests/test_system_control_darwin.py

Skips destructive actions: shutdown, restart, sleep, lock_screen, trash_file, kill_app.
"""

import platform
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tools.system_control.darwin import DarwinSystemControl


def main():
    if platform.system() != "Darwin":
        print("SKIP: not macOS")
        return

    ctrl = DarwinSystemControl()
    results = {}

    # -- Display --
    print("\n=== DISPLAY ===")

    r = ctrl.get_brightness()
    results["get_brightness"] = r
    print(f"  get_brightness: {r}")

    r = ctrl.set_brightness(70)
    results["set_brightness"] = r
    print(f"  set_brightness(70): {r}")
    time.sleep(0.5)
    ctrl.set_brightness(50)

    r = ctrl.get_dark_mode()
    results["get_dark_mode"] = r
    print(f"  get_dark_mode: {r}")

    r = ctrl.set_dark_mode(True)
    results["set_dark_mode_on"] = r
    print(f"  set_dark_mode(True): {r}")
    time.sleep(1)

    r = ctrl.set_dark_mode(False)
    results["set_dark_mode_off"] = r
    print(f"  set_dark_mode(False): {r}")

    # -- Audio --
    print("\n=== AUDIO ===")

    r = ctrl.get_volume()
    results["get_volume"] = r
    print(f"  get_volume: {r}")

    r = ctrl.set_volume(40)
    results["set_volume"] = r
    print(f"  set_volume(40): {r}")
    time.sleep(0.3)
    ctrl.set_volume(60)

    r = ctrl.set_mute(True)
    results["set_mute_on"] = r
    print(f"  set_mute(True): {r}")
    time.sleep(0.3)

    r = ctrl.set_mute(False)
    results["set_mute_off"] = r
    print(f"  set_mute(False): {r}")

    r = ctrl.set_mic_mute(True)
    results["set_mic_mute_on"] = r
    print(f"  set_mic_mute(True): {r}")
    time.sleep(0.3)

    r = ctrl.set_mic_mute(False)
    results["set_mic_mute_off"] = r
    print(f"  set_mic_mute(False): {r}")

    # -- Screenshots --
    print("\n=== SCREENSHOTS ===")

    path = os.path.expanduser("~/Desktop/_test_screenshot.png")
    r = ctrl.screenshot(path)
    results["screenshot_full"] = r
    print(f"  screenshot(full): {r}")
    if os.path.exists(path):
        size = os.path.getsize(path)
        print(f"    file size: {size} bytes")
        os.remove(path)

    path2 = os.path.expanduser("~/Desktop/_test_screenshot_region.png")
    r = ctrl.screenshot(path2, region="0,0,200,200")
    results["screenshot_region"] = r
    print(f"  screenshot(region): {r}")
    if os.path.exists(path2):
        size = os.path.getsize(path2)
        print(f"    file size: {size} bytes")
        os.remove(path2)

    # -- Power (safe only) --
    print("\n=== POWER (safe) ===")

    r = ctrl.battery_info()
    results["battery_info"] = r
    print(f"  battery_info: {r}")

    # -- Network --
    print("\n=== NETWORK ===")

    r = ctrl.set_wifi(False)
    results["set_wifi_off"] = r
    print(f"  set_wifi(False): {r}")
    time.sleep(1)

    r = ctrl.set_wifi(True)
    results["set_wifi_on"] = r
    print(f"  set_wifi(True): {r}")

    r = ctrl.set_bluetooth(False)
    results["set_bluetooth_off"] = r
    print(f"  set_bluetooth(False): {r}")
    time.sleep(1)

    r = ctrl.set_bluetooth(True)
    results["set_bluetooth_on"] = r
    print(f"  set_bluetooth(True): {r}")

    # -- Windows --
    print("\n=== WINDOWS ===")

    r = ctrl.list_windows()
    results["list_windows"] = r[:200]
    print(f"  list_windows: {r[:200]}...")

    r = ctrl.focus_window("Finder")
    results["focus_window"] = r
    print(f"  focus_window('Finder'): {r}")

    r = ctrl.minimize_window("Finder")
    results["minimize_window"] = r
    print(f"  minimize_window('Finder'): {r}")

    r = ctrl.maximize_window("Finder")
    results["maximize_window"] = r
    print(f"  maximize_window('Finder'): {r}")

    # -- Media --
    print("\n=== MEDIA ===")

    r = ctrl.media_now_playing()
    results["media_now_playing"] = r
    print(f"  media_now_playing: {r}")

    r = ctrl.media_play_pause()
    results["media_play_pause"] = r
    print(f"  media_play_pause: {r}")
    time.sleep(1)

    r = ctrl.media_next()
    results["media_next"] = r
    print(f"  media_next: {r}")
    time.sleep(1)

    r = ctrl.media_previous()
    results["media_previous"] = r
    print(f"  media_previous: {r}")

    # -- Clipboard --
    print("\n=== CLIPBOARD ===")

    r = ctrl.clipboard_write("test_system_control_clipboard_123")
    results["clipboard_write"] = r
    print(f"  clipboard_write: {r}")

    r = ctrl.clipboard_read()
    results["clipboard_read"] = r
    print(f"  clipboard_read: {r}")
    assert "test_system_control_clipboard_123" in r, f"Clipboard mismatch: {r}"

    # -- Notifications --
    print("\n=== NOTIFICATIONS ===")

    r = ctrl.notify("Test", "System control test notification")
    results["notify"] = r
    print(f"  notify: {r}")

    # -- Applications --
    print("\n=== APPLICATIONS ===")

    r = ctrl.list_apps()
    results["list_apps"] = r[:200]
    print(f"  list_apps: {r[:200]}...")

    r = ctrl.focus_app("Finder")
    results["focus_app"] = r
    print(f"  focus_app('Finder'): {r}")

    # -- Files --
    print("\n=== FILES ===")

    test_file = os.path.expanduser("~/Desktop/_test_sys_ctrl.txt")
    with open(test_file, "w") as f:
        f.write("test")

    r = ctrl.open_file(test_file)
    results["open_file"] = r
    print(f"  open_file: {r}")
    time.sleep(1)

    r = ctrl.reveal_in_file_manager(test_file)
    results["reveal_in_file_manager"] = r
    print(f"  reveal_in_file_manager: {r}")

    os.remove(test_file)

    # -- System Info --
    print("\n=== SYSTEM INFO ===")

    r = ctrl.system_info()
    results["system_info"] = r
    print(f"  system_info: {r}")

    # -- Summary --
    print("\n=== SUMMARY ===")
    total = len(results)
    errors = [k for k, v in results.items() if v and "Error" in str(v)]
    print(f"  Total tests: {total}")
    print(f"  Errors: {len(errors)}")
    if errors:
        for e in errors:
            print(f"    FAIL: {e} → {results[e]}")
    else:
        print("  All passed!")


if __name__ == "__main__":
    main()
