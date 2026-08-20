"""ecogenie App Device 分頁 (裝置列表) 的 Page Object."""

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

_PACKAGE = "io.nextdrive.ecogenie.stg"


class DevicePage(BasePage):
    _ADD_DEVICE_BUTTON = (AppiumBy.ID, f"{_PACKAGE}:id/opt_add_device_coach")

    # 已關聯的閘道器卡片
    _GATEWAY_NAME = (AppiumBy.ID, f"{_PACKAGE}:id/name")
    _GATEWAY_MORE_BUTTON = (AppiumBy.ID, f"{_PACKAGE}:id/more")

    # 三個點打開的「設定」bottom sheet: 一般 / 網路 / 所在地區 / 移除,
    # 四個項目共用 title_textView 這個 resource-id, 只能用文字區分
    _SETTINGS_REMOVE_ITEM = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        f'new UiSelector().resourceId("{_PACKAGE}:id/title_textView").text("移除")',
    )

    # 「移除閘道器？」確認彈窗的「移除」, 跟其他 App 彈窗共用主按鈕 id
    _REMOVE_CONFIRM_BUTTON = (
        AppiumBy.ID,
        f"{_PACKAGE}:id/arch_component_dialog_main_action_button",
    )

    # 沒有任何閘道器時顯示的空狀態訊息 (「點擊以新增閘道器」)
    _EMPTY_DEVICE_MESSAGE = (AppiumBy.ID, f"{_PACKAGE}:id/emptyDeviceMessage")

    @property
    def gateway_name_locator(self) -> tuple:
        return self._GATEWAY_NAME

    @property
    def empty_device_message_locator(self) -> tuple:
        return self._EMPTY_DEVICE_MESSAGE

    def tap_add_device(self) -> None:
        self._tap(self._ADD_DEVICE_BUTTON)

    def tap_gateway_more(self, timeout: int = 15) -> None:
        """點閘道器卡片右上角的三個點, 打開「設定」bottom sheet."""
        self._tap(self._GATEWAY_MORE_BUTTON, timeout)

    def tap_settings_remove(self, timeout: int = 10) -> None:
        """「設定」bottom sheet 的「移除」項目."""
        self._tap(self._SETTINGS_REMOVE_ITEM, timeout)

    def tap_remove_confirm(self, timeout: int = 10) -> None:
        """「移除閘道器？」確認彈窗的「移除」按鈕 (此動作無法復原)."""
        self._tap(self._REMOVE_CONFIRM_BUTTON, timeout)
