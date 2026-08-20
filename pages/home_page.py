"""ecogenie App 登入後首頁 (MainActivity) 的 Page Object."""

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

_PACKAGE = "io.nextdrive.ecogenie.stg"


class HomePage(BasePage):
    _DEVICE_TAB = (AppiumBy.ID, f"{_PACKAGE}:id/nav_bottom_tab_device")
    _HOME_TAB = (AppiumBy.ID, f"{_PACKAGE}:id/nav_bottom_tab_home")
    _ENERGY_USAGE_TAB = (AppiumBy.ID, f"{_PACKAGE}:id/nav_bottom_tab_energy_usage")
    _SERVICE_TAB = (AppiumBy.ID, f"{_PACKAGE}:id/nav_bottom_tab_service")
    _ACCOUNT_TAB = (AppiumBy.ID, f"{_PACKAGE}:id/nav_bottom_tab_account")

    def tap_device_tab(self) -> None:
        self._tap(self._DEVICE_TAB)
