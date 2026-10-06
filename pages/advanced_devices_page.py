"""ecogenie App「進階裝置」清單畫面的 Page Object.

從裝置分頁的閘道器卡片下方點「進階裝置」導覽進來, 列出掛在該閘道器下的
Modbus/藍牙等子裝置, 每個裝置各自有一顆「設定」按鈕可以移除。
"""

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

_PACKAGE = "io.nextdrive.ecogenie.stg"


class AdvancedDevicesPage(BasePage):
    _DEVICE_NAME = f"{_PACKAGE}:id/deviceName"
    _SETTINGS_BUTTON = f"{_PACKAGE}:id/settingsButton"

    def _device_settings_button_locator(self, device_name: str) -> tuple:
        return (
            AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiSelector().resourceId("{self._DEVICE_NAME}").text("{device_name}")'
            f'.fromParent(new UiSelector().resourceId("{self._SETTINGS_BUTTON}"))',
        )

    def tap_device_settings(self, device_name: str, timeout: int = 10) -> None:
        """點指定裝置那一列的「設定」按鈕, 打開「設定」bottom sheet."""
        self._tap(self._device_settings_button_locator(device_name), timeout)

    def tap_settings_remove(self, timeout: int = 10) -> None:
        """「設定」bottom sheet 的「移除」項目, 跟閘道器設定選單共用同一種
        結構 (繼承自 BasePage)。
        """
        self.tap_settings_menu_item("移除", timeout)

    def tap_remove_confirm(self, timeout: int = 10) -> None:
        """「移除 XXX？」確認彈窗的「移除」按鈕 (此動作無法復原), 跟其他
        App 內部彈窗共用同一顆主按鈕 (繼承自 BasePage)。
        """
        self.tap_confirm_dialog_main_action(timeout)
