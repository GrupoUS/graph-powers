#!/usr/bin/env python3
"""notify.py - Notification hook that works in WSL2, Linux, and macOS.
Reads JSON from stdin: { "message": "...", "title": "...", "notification_type": "..." }
"""
import json
import os
import platform
import subprocess
import sys
import typing



def read_input() -> dict[str, object]:
    try:
        raw = sys.stdin.read()
        return typing.cast(dict[str, object], json.loads(raw)) if raw.strip() else {}
    except Exception:
        return {}


def is_wsl() -> bool:
    if os.environ.get("WSL_DISTRO_NAME"):
        return True

    if os.path.exists("/proc/version"):
        try:
            with open("/proc/version", encoding="utf-8") as f:
                return "microsoft" in f.read().lower()
        except OSError:
            return False

    return False


def notify_wsl(title: str, message: str) -> bool:
    """Use PowerShell Windows Toast for WSL2."""
    safe_title = title.replace("'", "''")
    safe_message = message.replace("'", "''")
    ps_script = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
$textNodes = $template.GetElementsByTagName('text')
$textNodes.Item(0).AppendChild($template.CreateTextNode('{safe_title}')) | Out-Null
$textNodes.Item(1).AppendChild($template.CreateTextNode('{safe_message}')) | Out-Null
$toast = [Windows.UI.Notifications.ToastNotification]::new($template)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Claude Code').Show($toast)
"""
    try:
        result = _ = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


def notify_linux(title: str, message: str) -> bool:
    """Use notify-send for native Linux."""
    try:
        result = _ = subprocess.run(
            ["notify-send", "--app-name=Claude Code", title, message],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def notify_macos(title: str, message: str) -> bool:
    """Use osascript for macOS."""
    try:
        safe_title = title.replace("\\", "\\\\").replace('"', '\\"')
        safe_message = message.replace("\\", "\\\\").replace('"', '\\"')
        script = f'display notification "{safe_message}" with title "{safe_title}"'
        result = _ = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def main() -> None:
    data: dict[str, object] = read_input()
    title = str(data.get("title", "Claude Code"))
    message = str(data.get("message", "Your agent session needs attention"))

    if is_wsl():
        if notify_wsl(title, message):
            return

    current_os = platform.system()
    if current_os == "Darwin":
        if notify_macos(title, message):
            return
    elif current_os == "Linux":
        if notify_linux(title, message):
            return

    # Fallback: terminal bell
    print("\a", end="", flush=True)


if __name__ == "__main__":
    main()
    sys.exit(0)
