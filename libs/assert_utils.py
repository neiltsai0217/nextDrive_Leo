"""Readable assertions with lightweight Allure diagnostics (Appium / Selenium)."""

import json
from collections.abc import Mapping
from typing import Any, NoReturn

import allure
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from libs.log_utils import get_logger

_logger = get_logger(__name__)


SENSITIVE_KEYS = {
    "access_token",
    "authorization",
    "cookie",
    "password",
    "refresh_token",
    "token",
}

VERIFY_PASS = "PASS"
VERIFY_FAILED = "FAILED"


def _sanitize(value: Any, key: str = "") -> Any:
    """Recursively redact credentials before writing data to Allure."""
    if key.lower() in SENSITIVE_KEYS:
        return "***REDACTED***"
    if isinstance(value, Mapping):
        return {str(k): _sanitize(v, str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_sanitize(item) for item in value]
    return value


def _attach_result(
    expected: Any,
    actual: Any,
    passed: bool,
    context: Mapping[str, Any] | None = None,
) -> None:
    """
    每個斷言固定附一份「驗證結果」:預期 / 實際 / Verify,通過與失敗都附,
    讓報告不用對照程式也看得懂驗了什麼;context 放在「補充資訊」,不與預期 / 實際混在一起.
    """
    result: dict[str, Any] = {
        "預期": expected,
        "實際": actual,
        "Verify": VERIFY_PASS if passed else VERIFY_FAILED,
    }
    if context:
        result["補充資訊"] = _sanitize(context)
    allure.attach(
        json.dumps(result, ensure_ascii=False, indent=2, default=str),
        name="驗證結果",
        attachment_type=allure.attachment_type.JSON,
    )


def _current_screen_label(driver) -> str:
    """Android 可取得 current_activity 作為畫面上下文;iOS 無對應概念."""
    try:
        return f"current_activity={driver.current_activity}"
    except Exception:
        return "current_activity 無法取得(可能為 iOS 平台)"


def _attach_driver_failure(driver, error: Exception) -> None:
    allure.attach(
        _current_screen_label(driver),
        name="當前畫面",
        attachment_type=allure.attachment_type.TEXT,
    )
    allure.attach(
        str(error),
        name="Appium 原始錯誤",
        attachment_type=allure.attachment_type.TEXT,
    )


def _fail(
    assertion_name: str,
    expected: str,
    actual: str,
    original_error: Exception | None = None,
) -> NoReturn:
    message = (
        f"{assertion_name}失敗\n"
        f"預期結果:{expected}\n"
        f"實際結果:{actual}"
    )
    if original_error is None:
        raise AssertionError(message)
    raise AssertionError(message) from original_error


def _element_state(driver, locator) -> str:
    """Collect a quick diagnosis without introducing another long wait."""
    try:
        elements = driver.find_elements(*locator)
        if not elements:
            return "找不到元素"
        if len(elements) > 1:
            return f"找到 {len(elements)} 個元素，無法確認唯一目標"
        return "元素存在但不可見"
    except Exception:
        return "無法取得元素狀態，請查看 Appium 原始錯誤"


def _read_text(driver, locator) -> str | None:
    """立即讀取元素文字(不做等待);讀不到時回傳 None."""
    try:
        return driver.find_element(*locator).text.strip()
    except Exception:
        return None


def _display_text(text: str) -> str:
    """報告顯示用:空字串顯示為「(空白)」,避免「預期 / 實際」欄位一片空白看不懂."""
    return text if text else "（空白）"


def assert_visible(
    driver,
    locator: tuple,
    assertion_name: str,
    *,
    timeout: int = 10,
    context: Mapping[str, Any] | None = None,
    target: str | None = None,
) -> None:
    """
    驗證元素顯示;「實際」會一併帶出元素文字.

    target 為報告顯示用的目標名稱(例如「新增閘道器空狀態訊息」),「預期」會寫成「顯示「target」」,
    避免報告只寫「顯示」看不出要找的是什麼.
    """
    with allure.step(assertion_name):
        expected_display = f"顯示「{target}」" if target else "顯示"
        try:
            WebDriverWait(driver, timeout).until(EC.visibility_of_element_located(locator))
        except TimeoutException as error:
            actual = _element_state(driver, locator)
            _attach_result(expected_display, actual, False, context)
            _attach_driver_failure(driver, error)
            _fail(assertion_name, f"{expected_display}(等待 {timeout} 秒)", actual, error)
        text = _read_text(driver, locator)
        _attach_result(expected_display, f"顯示「{text}」" if text else expected_display, True, context)


def assert_hidden(
    driver,
    locator: tuple,
    assertion_name: str,
    *,
    timeout: int = 10,
    context: Mapping[str, Any] | None = None,
    target: str | None = None,
) -> None:
    """驗證元素不存在;target 為報告顯示用的目標名稱,「預期」會寫成「不顯示「target」」."""
    with allure.step(assertion_name):
        expected_display = f"不顯示「{target}」" if target else "不顯示"
        try:
            WebDriverWait(driver, timeout).until_not(EC.presence_of_element_located(locator))
        except TimeoutException as error:
            actual = f"仍然顯示「{target}」" if target else "仍然顯示"
            _attach_result(expected_display, actual, False, context)
            _attach_driver_failure(driver, error)
            _fail(assertion_name, f"{expected_display}(等待 {timeout} 秒)", actual, error)
        _attach_result(expected_display, expected_display, True, context)


def assert_text(
    driver,
    locator: tuple,
    expected_text: str,
    assertion_name: str,
    *,
    timeout: int = 10,
    context: Mapping[str, Any] | None = None,
) -> None:
    """驗證元素文字完全一致;實際文字一律寫進「驗證結果」."""
    with allure.step(assertion_name):
        expected_display = _display_text(expected_text)
        try:
            WebDriverWait(driver, timeout).until(lambda drv: _read_text(drv, locator) == expected_text)
        except TimeoutException as error:
            actual_text = _read_text(driver, locator)
            actual = _display_text(actual_text) if actual_text is not None else _element_state(driver, locator)
            _attach_result(expected_display, actual, False, context)
            _attach_driver_failure(driver, error)
            _fail(assertion_name, expected_display, actual, error)
        _attach_result(expected_display, expected_display, True, context)


def assert_attribute(
    driver,
    locator: tuple,
    attribute: str,
    expected_value: str,
    assertion_name: str,
    *,
    timeout: int = 10,
    context: Mapping[str, Any] | None = None,
) -> None:
    """驗證元素屬性;Android 常用 `content-desc` / `text`,iOS 常用 `name` / `value`."""
    with allure.step(assertion_name):
        expected_display = f"{attribute}=「{expected_value}」"

        def _attribute_matches(drv):
            try:
                element = drv.find_element(*locator)
            except NoSuchElementException:
                return False
            return element.get_attribute(attribute) == expected_value

        try:
            WebDriverWait(driver, timeout).until(_attribute_matches)
        except TimeoutException as error:
            try:
                actual = f"{attribute}=「{driver.find_element(*locator).get_attribute(attribute)}」"
            except Exception:
                actual = _element_state(driver, locator)
            _attach_result(expected_display, actual, False, context)
            _attach_driver_failure(driver, error)
            _fail(assertion_name, expected_display, actual, error)
        _attach_result(expected_display, expected_display, True, context)


def attach_screenshot(driver, name: str) -> None:
    """擷取當前畫面截圖並附加到 Allure 報告."""
    try:
        allure.attach(
            driver.get_screenshot_as_png(),
            name=name,
            attachment_type=allure.attachment_type.PNG,
        )
    except Exception as error:
        _logger.warning("無法擷取「%s」截圖:%s", name, error)


def attach_page_source(driver, name: str) -> None:
    """
    擷取當前畫面的 UI hierarchy (XML) 並附加到 Allure 報告.

    透過已連線的 Appium session 取得,不會像 adb shell uiautomator dump
    一樣跟同一個 UiAutomationService 搶註冊而失敗.
    """
    try:
        allure.attach(
            driver.page_source,
            name=name,
            attachment_type=allure.attachment_type.XML,
        )
    except Exception as error:
        _logger.warning("無法擷取「%s」page source:%s", name, error)


def assert_equal(
    actual: Any,
    expected: Any,
    assertion_name: str = "驗證數值相等",
    *,
    context: Mapping[str, Any] | None = None,
) -> None:
    with allure.step(assertion_name):
        passed = actual == expected
        _attach_result(expected, actual, passed, context)
        if not passed:
            _fail(
                assertion_name,
                f"{expected!r}({type(expected).__name__})",
                f"{actual!r}({type(actual).__name__})",
            )


def assert_not_equal(
    actual: Any,
    unexpected: Any,
    assertion_name: str,
    *,
    context: Mapping[str, Any] | None = None,
) -> None:
    """驗證兩個值不同(例如 gateway_uuid 不是空字串);報告「預期」顯示「不等於 X」."""
    with allure.step(assertion_name):
        passed = actual != unexpected
        _attach_result(f"不等於 {unexpected!r}", actual, passed, context)
        if not passed:
            _fail(assertion_name, f"不等於 {unexpected!r}", f"{actual!r}")


def assert_greater_than(
    actual: float,
    threshold: float,
    assertion_name: str = "驗證數值大於門檻",
    *,
    context: Mapping[str, Any] | None = None,
) -> None:
    """
    驗證 actual > threshold;用於防止"數量為 0"這類會讓 assert_equal(0, 0)
    誤判為通過的情境(例如畫面根本沒有渲染任何項目時,數量比對兩邊都是 0).
    """
    with allure.step(assertion_name):
        passed = actual > threshold
        _attach_result(f"大於 {threshold!r}", actual, passed, context)
        if not passed:
            _fail(assertion_name, f"大於 {threshold!r}", f"{actual!r}")
