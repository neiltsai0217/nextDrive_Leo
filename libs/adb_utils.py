"""adb 指令執行的底層基礎設施.

只放通用的指令執行邏輯, 不放任何具體業務指令 (藍牙/Wi-Fi/重開機等).
具體指令封裝放在 `testsuites/common/v1_adb_utils.py`.
"""

import logging
import subprocess
import time

_logger = logging.getLogger(__name__)


def run(adb_code: str, **kwargs) -> subprocess.CompletedProcess:
    """執行一行完整的 adb 指令字串, 例如 run("adb reboot").

    實測確認 (透過背景監控 adb 連線狀態逐秒記錄比對) 部分硬體 (Cube J 走 USB
    連線) 的 adb 連線會週期性閃斷 (每隔十幾到三十秒左右斷線幾秒), 不是「重開機
    後一段時間就會穩定」這種一次性延遲, 單一指令偶爾會剛好撞上斷線瞬間而失敗。
    所以預設 (check=True 時) 加上短暫重試, 只有重試多次仍失敗才真的 raise;
    若呼叫端明確傳入 check=False (例如只是想檢查指令本身是否成功, 不當作連線
    問題處理), 則維持原樣單次執行、不重試。
    """
    kwargs.setdefault("shell", True)
    kwargs.setdefault("capture_output", True)
    kwargs.setdefault("text", True)
    check = kwargs.pop("check", True)
    # 指令含密碼等機敏資料時,呼叫端傳 log_as 指定寫進 log / 錯誤訊息的遮罩版本
    display_code = kwargs.pop("log_as", adb_code)

    _logger.info("adb 指令: %s", display_code)

    if not check:
        return subprocess.run(adb_code, check=False, **kwargs)

    # 實測過閃斷期間有些長達 10 幾秒, 3 次*2 秒 (共約 4 秒) 的重試視窗不夠,
    # 拉長到 10 次*3 秒 (共約 27 秒) 才扛得住觀察到的較長斷線區間。
    retries = kwargs.pop("retries", 10)
    retry_delay = kwargs.pop("retry_delay", 3)

    result = None
    for attempt in range(retries):
        result = subprocess.run(adb_code, check=False, **kwargs)
        if result.returncode == 0:
            return result
        _logger.info(
            "adb 指令失敗 (第 %d/%d 次): %s (stderr: %s)",
            attempt + 1,
            retries,
            display_code,
            result.stderr.strip(),
        )
        if attempt < retries - 1:
            time.sleep(retry_delay)

    raise subprocess.CalledProcessError(
        result.returncode,
        f"{display_code} (stderr: {result.stderr.strip()!r})",
        output=result.stdout,
        stderr=result.stderr,
    )


def _with_serial(serial: str | None) -> str:
    """組出 adb 指令的 `-s <serial>` 前綴, serial 為 None 時省略
    (讓 adb 用預設/唯一連接的裝置)。"""
    return f"adb -s {serial}" if serial else "adb"


def adb_execute(command: str, serial: str | None = None, **kwargs) -> subprocess.CompletedProcess:
    """組出並執行一行 `adb [-s <serial>] shell "<command>"`.

    例如 adb_execute("getprop ro.build.version.release", serial)。
    """
    if "log_as" in kwargs:
        kwargs["log_as"] = f'{_with_serial(serial)} shell "{kwargs["log_as"]}"'
    return run(f'{_with_serial(serial)} shell "{command}"', **kwargs)


def adb_execute_raw(args: str, serial: str | None = None, **kwargs) -> subprocess.CompletedProcess:
    """組出並執行一行「非 shell」的 adb 子指令, 例如 root/reboot/push/wait-for-device.

    例如 adb_execute_raw("reboot", serial)。
    """
    return run(f"{_with_serial(serial)} {args}", **kwargs)
