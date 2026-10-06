"""ecogenie App Device 分頁 (裝置列表) 的 Page Object."""

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException

from pages.base_page import BasePage

_PACKAGE = "io.nextdrive.ecogenie.stg"


class DevicePage(BasePage):
    # 裝置分頁完全沒有任何閘道器時, 新手引導用的「+」按鈕 (只出現一次)
    _ADD_DEVICE_BUTTON = (AppiumBy.ID, f"{_PACKAGE}:id/opt_add_device_coach")

    # 已經有至少一台閘道器之後, 工具列常駐的「+」按鈕 (跟上面的 coach 版本
    # 是不同的 resource-id, 實測 dump 確認過; 新增子裝置時要用這顆, 不是
    # coach 版本)
    _ADD_DEVICE_TOOLBAR_BUTTON = (AppiumBy.ID, f"{_PACKAGE}:id/opt_add_device")

    # 已關聯的閘道器卡片
    _GATEWAY_NAME = (AppiumBy.ID, f"{_PACKAGE}:id/name")
    _GATEWAY_MORE_BUTTON = (AppiumBy.ID, f"{_PACKAGE}:id/more")

    # 沒有任何閘道器時顯示的空狀態訊息 (「點擊以新增閘道器」)
    _EMPTY_DEVICE_MESSAGE = (AppiumBy.ID, f"{_PACKAGE}:id/emptyDeviceMessage")

    # 閘道器卡片下方的「進階裝置」收合列, 點下去會導覽到獨立的進階裝置清單畫面
    # (不是在原地展開, 實測 dump 確認過)
    _ADVANCED_DEVICES_FOOTER = (AppiumBy.ID, f"{_PACKAGE}:id/accessoryListFooter")

    @property
    def gateway_name_locator(self) -> tuple:
        return self._GATEWAY_NAME

    @property
    def empty_device_message_locator(self) -> tuple:
        return self._EMPTY_DEVICE_MESSAGE

    def tap_add_device(self, timeout: int = 10) -> None:
        """新增第一台閘道器的「+」.

        coach 版按鈕只在這個帳號「從來沒加過任何裝置」時出現一次, 之後
        (即使裝置清單重新變空, 例如解除關聯後又要重新關聯) 就固定顯示
        工具列常駐版, 不會再變回 coach 版 (實測確認: TC-40140 解除關聯閘道器
        後想再次呼叫 connect_device() 重新關聯, 這時仍然是常駐版, 找 coach
        版會逾時)。這裡先短暫嘗試 coach 版, 找不到就改用常駐版, 讓這個方法
        不論帳號是否第一次使用都能用。
        """
        try:
            self._tap(self._ADD_DEVICE_BUTTON, timeout=3)
        except TimeoutException:
            self._tap(self._ADD_DEVICE_TOOLBAR_BUTTON, timeout)

    def tap_add_device_toolbar_button(self, timeout: int = 10) -> None:
        """已有至少一台閘道器時, 用工具列的「+」新增子裝置 (跟 tap_add_device()
        的新手引導按鈕是不同元件)。
        """
        self._tap(self._ADD_DEVICE_TOOLBAR_BUTTON, timeout)

    def is_gateway_associated(self, timeout: int = 3) -> bool:
        """快速檢查裝置分頁目前是否已經有關聯中的閘道器 (short timeout,
        不等太久), 供關聯前先判斷要不要清掉舊關聯用, 不當斷言使用."""
        try:
            self._wait_visible(self._GATEWAY_NAME, timeout)
            return True
        except TimeoutException:
            return False

    def tap_gateway_more(self, timeout: int = 15) -> None:
        """點閘道器卡片右上角的三個點, 打開「設定」bottom sheet.

        實測發現偶爾第一次點擊沒有反應 (推測是卡片畫面當下還在動畫/更新中,
        點擊被吃掉), 但點擊本身不會拋例外, 只有底下真的接著找不到「移除」
        才會發現選單沒打開。這裡點完後改用「移除」選項有沒有出現來確認
        選單真的打開, 沒開就重點一次。
        """
        self._tap(self._GATEWAY_MORE_BUTTON, timeout)
        try:
            self._wait_visible(self._settings_menu_item_locator("移除"), timeout=3)
        except TimeoutException:
            self._tap(self._GATEWAY_MORE_BUTTON, timeout)

    def tap_settings_remove(self, timeout: int = 10) -> None:
        """「設定」bottom sheet 的「移除」項目."""
        self.tap_settings_menu_item("移除", timeout)

    def tap_remove_confirm(self, timeout: int = 10) -> None:
        """「移除閘道器？」確認彈窗的「移除」按鈕 (此動作無法復原)."""
        self.tap_confirm_dialog_main_action(timeout)

    def tap_advanced_devices_footer(self, timeout: int = 10) -> None:
        """點「進階裝置」收合列, 導覽到進階裝置清單畫面."""
        self._tap(self._ADVANCED_DEVICES_FOOTER, timeout)
