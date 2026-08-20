"""Android emulator/device readiness helpers (adb + aapt), used by conftest.py."""

import os
import re
import subprocess
import time

from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By

from libs.log_utils import get_logger

_logger = get_logger(__name__)


def _adb_command(serial: str | None, *args: str) -> list:
    """組 adb 指令 (list 形式, 給裝置就緒檢查這種需要精確控制參數的場合用);
    有帶 serial 時用 `-s serial` 明確指定裝置, 避免同時接了實體機 + 模擬器時
    adb 因為裝置不只一台而報錯. 具體業務指令請走
    `testsuites/common/v1_adb_utils.py`, 不要在這裡加.
    """
    cmd = ["adb"]
    if serial:
        cmd += ["-s", serial]
    cmd += list(args)
    return cmd


def _find_aapt() -> str:
    android_home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if not android_home:
        raise RuntimeError("ANDROID_HOME/ANDROID_SDK_ROOT 未設定, 無法定位 aapt")

    build_tools_dir = os.path.join(android_home, "build-tools")
    versions = sorted(os.listdir(build_tools_dir))
    if not versions:
        raise RuntimeError(f"{build_tools_dir} 底下沒有任何 build-tools 版本")

    return os.path.join(build_tools_dir, versions[-1], "aapt")


def inspect_apk(apk_path: str) -> tuple[str, str]:
    """回傳 (package_name, launcher_activity)."""
    aapt = _find_aapt()
    output = subprocess.run(
        [aapt, "dump", "badging", apk_path],
        capture_output=True,
        text=True,
        check=True,
    ).stdout

    package_match = re.search(r"package: name='([^']+)'", output)
    activity_match = re.search(r"launchable-activity: name='([^']+)'", output)
    if not package_match or not activity_match:
        raise RuntimeError(f"無法從 {apk_path} 解析出 package/activity")

    return package_match.group(1), activity_match.group(1)


def _list_emulator_serials() -> set:
    result = subprocess.run(["adb", "devices"], capture_output=True, text=True, check=True)
    serials = set()
    for line in result.stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) == 2 and parts[0].startswith("emulator-") and parts[1] == "device":
            serials.add(parts[0])
    return serials


def find_emulator_serial() -> str | None:
    """回傳目前有在跑的模擬器 serial (例如 emulator-5554); 沒有就回傳 None."""
    serials = _list_emulator_serials()
    return sorted(serials)[0] if serials else None


def find_target_device_serial(exclude_serial: str | None = None) -> str | None:
    """回傳目前透過 USB 接上、且不是 exclude_serial 的實體裝置 serial.

    這台是待測的硬體本體 (例如 Cube J), 不是跑 App 的手機/模擬器. 用
    exclude_serial (跑 App 的手機/模擬器 serial) 排除, 而不是只排除
    emulator-*, 是因為之後改跑實體機測試時, 跑 App 的手機本身也會是一個
    「非模擬器」的 serial, 只排除 emulator-* 會誤把手機當成目標裝置.
    沒有其他裝置時回傳 None.
    """
    result = subprocess.run(["adb", "devices"], capture_output=True, text=True, check=True)
    for line in result.stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 2 or parts[1] != "device":
            continue
        serial = parts[0]
        if serial == exclude_serial:
            continue
        return serial
    return None


def is_emulator_running() -> bool:
    return find_emulator_serial() is not None


def start_emulator(avd_name: str, boot_timeout: int = 120) -> str:
    """啟動模擬器, 回傳開機完成後的 adb serial (例如 emulator-5554)."""
    _logger.info(f"啟動模擬器 avd={avd_name}")
    before = _list_emulator_serials()
    subprocess.Popen(
        ["emulator", "-avd", avd_name, "-netdelay", "none", "-netspeed", "full"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    deadline = time.time() + boot_timeout
    serial = None
    while time.time() < deadline:
        new_serials = _list_emulator_serials() - before
        if new_serials:
            serial = sorted(new_serials)[0]
            break
        time.sleep(1)
    if not serial:
        raise TimeoutError(f"模擬器 {avd_name} 在 {boot_timeout} 秒內未出現在 adb devices")

    deadline = time.time() + boot_timeout
    while time.time() < deadline:
        result = subprocess.run(
            _adb_command(serial, "shell", "getprop", "sys.boot_completed"),
            capture_output=True,
            text=True,
        )
        if result.stdout.strip() == "1":
            _logger.info(f"模擬器 {avd_name} 開機完成 (serial={serial})")
            return serial
        time.sleep(2)

    raise TimeoutError(f"模擬器 {avd_name} 在 {boot_timeout} 秒內未完成開機")


def is_app_installed(package_name: str, serial: str | None = None) -> bool:
    result = subprocess.run(
        _adb_command(serial, "shell", "pm", "list", "packages"),
        capture_output=True,
        text=True,
        check=True,
    )
    return f"package:{package_name}" in result.stdout.splitlines()


def install_apk(apk_path: str, serial: str | None = None) -> None:
    _logger.info(f"安裝 apk: {apk_path}")
    subprocess.run(_adb_command(serial, "install", "-r", apk_path), check=True)


def ensure_android_emulator_ready(capabilities: dict) -> str | None:
    """依 capabilities 內容, 確保模擬器開機且 apk 已安裝.

    只處理 capabilities 帶 appium:avd (模擬器設定) 的情境; 真機 (帶 appium:udid)
    不做開機檢查, 交由使用者自行確保裝置已連接.
    回傳目前使用中的模擬器 serial (例如 emulator-5554, 沒有則 None), 供呼叫端
    設定 appium:udid, 避免同時接了實體機時 adb/Appium 分不清要操作哪一台.

    這裡刻意「不」啟動 app: app 的生命週期一律交給 Appium 掌管 (capabilities
    帶 appium:app + noReset=False, Appium 每建一個 session 就會自動清資料並
    冷啟動一次)。這個 fixture 是 session scope 只跑一次, 若在這裡也啟動一次,
    每個 test case 反而會多開關 app 一輪。
    """
    avd_name = capabilities.get("appium:avd")
    serial = None
    if avd_name:
        serial = find_emulator_serial()
        if serial:
            _logger.info(f"模擬器已開機, 略過啟動步驟 (serial={serial})")
        else:
            _logger.info("模擬器未開機, 啟動中")
            serial = start_emulator(avd_name)

    # 真機沒有 avd, serial 在上面維持 None; 這裡 fallback 用 capabilities 帶的
    # appium:udid, 讓下面 apk 安裝的 adb 指令能用 -s 精確指定裝置, 避免
    # 同時接了其他實體裝置 (例如待測硬體本體) 時 adb 因為裝置不只一台而報錯.
    serial = serial or capabilities.get("appium:udid")

    apk_path = capabilities.get("appium:app")
    if not apk_path:
        return serial

    package_name, _ = inspect_apk(apk_path)

    if is_app_installed(package_name, serial):
        _logger.info(f"{package_name} 已安裝, 略過安裝步驟")
    else:
        install_apk(apk_path, serial)

    return serial


def dismiss_android_compat_dialog(driver) -> bool:
    """檢查並關閉 Android 系統的 16KB page size 相容性警告.

    這個系統彈窗出現的時機不固定 (可能延遲, 也可能在任一個新 Activity 出現),
    所以設計成無論何時呼叫都只檢查「當下這一刻」有沒有跳出來, 讓呼叫端
    (例如 pages/base_page.py 的 _wait_visible) 在自己的元素等不到時重試呼叫.
    回傳這次呼叫是否有真的關掉彈窗.
    """
    locator = (By.ID, "android:id/button1")
    try:
        driver.find_element(*locator).click()
        _logger.info("已關閉 16KB 相容性警告彈窗")
        return True
    except (NoSuchElementException, StaleElementReferenceException):
        return False
