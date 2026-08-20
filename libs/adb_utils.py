"""adb 指令執行的底層基礎設施.

只放通用的指令執行邏輯, 不放任何具體業務指令 (藍牙/Wi-Fi/重開機等).
具體指令封裝放在 `testsuites/common/v1_adb_utils.py`.
"""

import subprocess


def run(adb_code: str, **kwargs) -> subprocess.CompletedProcess:
    """執行一行完整的 adb 指令字串, 例如 run("adb reboot")."""
    kwargs.setdefault("shell", True)
    kwargs.setdefault("capture_output", True)
    kwargs.setdefault("text", True)
    kwargs.setdefault("check", True)
    return subprocess.run(adb_code, **kwargs)
