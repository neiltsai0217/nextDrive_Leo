"""Pytest fixtures for Appium sessions (Android / iOS, emulator or real device).

裝置就緒檢查 (模擬器開機/apk 安裝) 由 ensure_device_ready 這個 session-scope
fixture 統一處理, driver fixture 只負責建立/收尾 Appium session.
driver / logged_in_driver 都是 module scope, 一個 test module 共用一個 session。
"""

import os
import platform
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import allure
import pytest
from appium import webdriver
from appium.options.android import UiAutomator2Options

from libs.assert_utils import attach_page_source, attach_screenshot
from libs.config_utils import config, get_capabilities, get_config
from libs.device_utils import (
    dismiss_android_compat_dialog,
    ensure_android_emulator_ready,
    find_target_device_serial,
)
from libs.log_utils import get_logger
from pages.sign_in_page import SignInPage

_logger = get_logger(__name__)

# 失敗分類規則(Allure「Categories」分頁);測試結束時複製進結果目錄
_ALLURE_CATEGORIES_SOURCE = Path(__file__).parent / "allure-config" / "categories.json"

APPIUM_SERVER_URL = os.environ.get("APPIUM_SERVER_URL", "http://127.0.0.1:4723")

# 開發/除錯時想讓 app 留在最後的畫面上手動接續操作, 設 KEEP_APP_OPEN=1 就會
# 跳過 session.quit(), app 不會被關掉 (Appium session 會留到 newCommandTimeout
# 逾時才自己收掉)。正常跑測試不要設, 否則 session 不會乾淨收尾。
KEEP_APP_OPEN = os.environ.get("KEEP_APP_OPEN") == "1"

# 給 pytest_runtest_makereport 失敗時撈畫面用: module scope 的 fixture chain
# (driver -> logged_in_driver -> devices_flow) 只要中途某個 fixture setup
# 失敗, pytest 就不會把已經成功的 driver/logged_in_driver 寫進
# item.funcargs (實測確認過, setup 階段失敗時 item.funcargs 只有
# pytest 內部的 fixture, 完全沒有這條 chain 上的任何東西), 所以另外用一個
# module 層級變數記住目前的 session, 不依賴 item.funcargs。
_current_driver_session = None


def _allure_results_dir(pytest_config):
    """取得 --alluredir 指定的結果目錄;沒開 allure 時回傳 None."""
    raw_dir = pytest_config.getoption("--alluredir", None)
    return Path(raw_dir) if raw_dir else None


def _git_value(*args):
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=Path(__file__).parent,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (subprocess.SubprocessError, OSError):
        return None


def _environment_entries(pytest_config):
    """組出 Allure 報告「Environment」區塊要顯示的欄位(不含 token、帳密等機敏資料)."""
    services = config.services
    capabilities = get_capabilities()
    app_path = capabilities.get("appium:app")
    entries = {
        "Site.Env": services.get("env"),
        "Site.Territory": services.get("territory"),
        "Site.Language": services.get("accept_language"),
        "Api.BaseUrl": services.get("ioe_api_url"),
        "Gateway.WifiSsid": config.wifi.get("ssid"),
        "Device.Platform": capabilities.get("platformName"),
        "Device.Name": capabilities.get("appium:deviceName"),
        "Device.PlatformVersion": capabilities.get("appium:platformVersion"),
        "App.File": os.path.basename(app_path) if app_path else None,
        "Appium.Server": APPIUM_SERVER_URL,
        "Pytest.MarkerExpression": pytest_config.option.markexpr or "(none)",
        "Pytest.TestPaths": " ".join(pytest_config.args) or "(default)",
        "Python": platform.python_version(),
        "Platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "Git.Branch": _git_value("rev-parse", "--abbrev-ref", "HEAD"),
        "Git.Commit": _git_value("rev-parse", "--short", "HEAD"),
        "Executed.At": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z"),
    }
    return {key: str(value) for key, value in entries.items() if value}


def _write_environment_properties(results_dir, pytest_config):
    """寫出 environment.properties,讓報告標示這次跑的是哪個環境 / 語系 / 手機."""
    lines = [f"{key}={value}" for key, value in _environment_entries(pytest_config).items()]
    try:
        (results_dir / "environment.properties").write_text(
            "\n".join(lines) + "\n", encoding="ascii", errors="replace"
        )
    except OSError as error:
        _logger.warning("無法寫入 environment.properties:%s", error)


def _copy_allure_categories(results_dir):
    """把失敗分類規則帶進結果目錄,報告才會有 Categories 分頁."""
    if not _ALLURE_CATEGORIES_SOURCE.exists():
        _logger.warning("找不到 %s,略過失敗分類設定。", _ALLURE_CATEGORIES_SOURCE)
        return
    try:
        shutil.copy(_ALLURE_CATEGORIES_SOURCE, results_dir / "categories.json")
    except OSError as error:
        _logger.warning("無法複製 categories.json:%s", error)


def pytest_sessionfinish(session, exitstatus):
    """
    測試結束後補齊 Allure 報告的中繼資料(Environment、Categories).

    在 sessionfinish 而非 sessionstart 執行:--clean-alluredir 會在 session 開始時清空結果目錄.
    """
    results_dir = _allure_results_dir(session.config)
    if results_dir is None or not results_dir.exists():
        return
    _write_environment_properties(results_dir, session.config)
    _copy_allure_categories(results_dir)


@pytest.fixture(autouse=True)
def _label_allure_environment():
    """
    在 Allure 報告標上執行環境與語系:parent_suite 讓報告依環境分組,
    parameter 會納入 historyId,不同環境 / 語系的同名 test 才不會被合併成「重試」.
    """
    env = config.services.get("env")
    language = config.services.get("accept_language")
    allure.dynamic.parent_suite(f"環境:{env}({language})")
    allure.dynamic.parameter("環境", env)
    allure.dynamic.parameter("語系", language)
    allure.dynamic.tag(f"環境:{env}")
    allure.dynamic.tag(f"語系:{language}")
    yield


@pytest.fixture(scope="session", autouse=True)
def ensure_device_ready():
    """跑第一個測試前, 確保裝置/apk/app 都已就緒, 全 session 只執行一次.

    回傳目前使用中的模擬器 serial (沒有則 None), 給 driver fixture 設定
    appium:udid, 避免同時接了實體機時 adb/Appium 分不清要操作哪一台.
    """
    capabilities = get_capabilities()
    if capabilities.get("platformName") == "Android":
        return ensure_android_emulator_ready(capabilities)
    return None


@pytest.fixture(scope="module")
def driver(ensure_device_ready):
    """建立/收尾 Appium session, 一個 test module 共用一個 session.

    scope 是 module 而不是 function, 是因為各模組的前置狀態 (例如 devices
    模組要先把裝置關聯完成) 會寫成 module scope 的 setup fixture, 而
    module scope 的 fixture 不能依賴 function scope 的 driver (ScopeMismatch);
    共用同一個 session 也讓整個 module 只開一次 app, 不用每個 case 重跑一次
    登入與前置流程。模組之間仍互相隔離 (換 module 就換一個新 session,
    capabilities 帶 noReset=False, Appium 會清掉 app 資料重新冷啟動)。
    """
    capabilities = dict(get_capabilities())
    if ensure_device_ready:
        capabilities["appium:udid"] = ensure_device_ready

    if KEEP_APP_OPEN:
        # 跳過 session.quit() 還不夠: 測試結束後沒有指令進來, Appium 會在
        # newCommandTimeout 到點時自己收掉 session 並把 app 關掉, 所以一併把
        # 這個 timeout 拉長, app 才會真的留在畫面上。
        capabilities["appium:newCommandTimeout"] = 3600

    options = UiAutomator2Options()
    options.load_capabilities(capabilities)

    # capabilities 帶 appium:app + noReset=False, 所以 Appium 在建 session 時
    # 就會自己清掉 app 資料並冷啟動到 Splash, 每個 module 剛好啟動一次。
    # 這裡不再額外 activate_app, 否則同一個 module 內會多開關 app 一輪。
    session = webdriver.Remote(APPIUM_SERVER_URL, options=options)

    global _current_driver_session
    _current_driver_session = session

    dismiss_android_compat_dialog(session)
    yield session

    _current_driver_session = None

    if KEEP_APP_OPEN:
        return
    session.quit()


@pytest.fixture(scope="session")
def target_device_serial(ensure_device_ready):
    """待測的實體裝置 (例如 Cube J 硬體本體) 的 adb serial, 不是跑 App 的手機/模擬器.

    真人操作時是按裝置上的實體按鈕 (例如開藍牙), 自動化時改對這台裝置下 adb
    指令模擬.

    優先讀環境設定的 gateway_ip: 實測環境常同時接了多台 Cube J (例如 USB 的
    221 加上無線 adb 的另一台), 純粹「排除跑 App 的手機後取第一台」會因為
    `adb devices` 的順序不固定而挑錯裝置, 所以指定要用哪一台。沒設定時才
    fallback 用排除法自動找, 都找不到時回傳 None。
    """
    gateway_ip = get_config(territory="tw", env="stage").users.basic_user.gateway_ip
    if gateway_ip:
        return gateway_ip

    return find_target_device_serial(exclude_serial=ensure_device_ready)


@pytest.fixture(scope="module")
def logged_in_driver(driver):
    """開啟 app 並用 variables/site_stage_tw.py 的 basic_user 完成登入後回傳 driver.

    跟 driver 一樣是 module scope: 一個 module 只登入一次, 供該模組的 setup
    fixture 與所有 case 共用。
    """
    basic_user = get_config(territory="tw", env="stage").users.basic_user

    sign_in_page = SignInPage(driver)
    sign_in_page.sign_in(basic_user.email, basic_user.password)

    return driver


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    # 不限制 report.when: setup 階段的 fixture 出錯 (例如 module fixture 裡的
    # connect_device() 失敗) 一樣要留下截圖跟 page source, 不然排錯時只有
    # exception 文字, 沒有畫面可以對照。
    if not report.failed:
        return

    session = (
        item.funcargs.get("driver")
        or item.funcargs.get("logged_in_driver")
        or _current_driver_session
    )
    if session is not None:
        attach_screenshot(session, "測試失敗畫面")
        attach_page_source(session, "測試失敗畫面 page source")
