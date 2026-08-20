"""Shared base class for Appium screen objects (Page Object layer).

子類別只能暴露 locator (`@property`) 與操作方法 (`open_*`/`tap_*`/`input_*`),
禁止在此撰寫斷言, 斷言一律交給 flow 層透過 `libs/assert_utils.py` 完成.
"""

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from libs.device_utils import dismiss_android_compat_dialog

_PACKAGE = "io.nextdrive.ecogenie.stg"


class BasePage:
    _ERROR_DIALOG_OK_BUTTON = (
        AppiumBy.ID,
        f"{_PACKAGE}:id/arch_component_dialog_main_action_button",
    )

    def __init__(self, driver):
        self.driver = driver

    def _find(self, locator: tuple, timeout: int = 10):
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator)
        )

    def _wait_visible(self, locator: tuple, timeout: int = 10):
        """等元素可見; 若逾時, 檢查是否被系統的 16KB 相容性彈窗擋住, 有就關掉後重試一次."""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
        except TimeoutException:
            if not dismiss_android_compat_dialog(self.driver):
                raise
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )

    def _tap(self, locator: tuple, timeout: int = 10) -> None:
        self._wait_visible(locator, timeout).click()

    def _input_text(self, locator: tuple, text: str, timeout: int = 10) -> None:
        element = self._wait_visible(locator, timeout)
        element.clear()
        element.send_keys(text)

    def _wait_hidden(self, locator: tuple, timeout: int = 10) -> None:
        WebDriverWait(self.driver, timeout).until_not(
            EC.visibility_of_element_located(locator)
        )

    def dismiss_error_dialog_if_shown(self, timeout: int = 3) -> bool:
        """關閉 App 通用的錯誤彈窗 (arch_component_dialog_*).

        已知情境: onboarding 最後一頁按「開啟通知」時, 使用者還沒登入沒有
        access token, App 會呼叫 notifications/subscribe 收到 401, 進而跳出
        「發生錯誤 (900)」蓋在登入入口畫面上面。這是後端預期內的回應, App
        端把它當成錯誤彈給使用者看是已知問題 (已回報 RD), 這裡先按掉讓自動化
        能繼續往下走, 彈窗沒出現不視為錯誤。
        """
        try:
            self._tap(self._ERROR_DIALOG_OK_BUTTON, timeout)
            return True
        except TimeoutException:
            return False
