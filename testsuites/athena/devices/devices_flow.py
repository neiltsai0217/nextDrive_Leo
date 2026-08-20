"""Devices 模組 Flow 層: 場景編排 + UI 斷言."""

from libs.assert_utils import assert_hidden, assert_text, assert_visible
from pages.add_device_type_page import AddDeviceTypePage
from pages.device_page import DevicePage
from pages.device_setup_page import DeviceSetupPage
from pages.home_page import HomePage
from testsuites.common.adb_v1_utils import press_wifi_association_button


class DevicesFlow:
    def __init__(self, driver, target_device_serial: str | None = None):
        self.driver = driver
        self._target_device_serial = target_device_serial
        self._home_page = HomePage(driver)
        self._device_page = DevicePage(driver)
        self._add_device_type_page = AddDeviceTypePage(driver)
        self._device_setup_page = DeviceSetupPage(driver)

    def connect_device(
        self,
        device_type: str,
        requirements: list,
        wifi_ssid: str,
        wifi_password: str,
        gateway_name: str,
    ) -> None:
        self._home_page.tap_device_tab()
        self._device_page.tap_add_device()
        self._add_device_type_page.select_device_type(device_type)
        self._device_setup_page.tap_next()

        # 真人操作是按 Athena 本體的 Wi-Fi 關聯實體按鈕開藍牙, 自動化改對這台硬體本體
        # (target_device_serial) 下 adb 指令模擬 sendevent 按鍵, 不是對跑 App 的模擬器/手機
        press_wifi_association_button(self._target_device_serial)

        for requirement in requirements:
            self._device_setup_page.check_requirement(requirement)

        self._device_setup_page.tap_next()
        self._device_setup_page.tap_pair()
        self._device_setup_page.tap_pair_confirm()

        self._device_setup_page.select_wifi_network(wifi_ssid)
        self._device_setup_page.input_wifi_password(wifi_password)
        self._device_setup_page.tap_wifi_connect()

        # 閘道器所在地是可選步驟, 跳過即可, 不影響裝置關聯完畢
        self._device_setup_page.tap_skip_gateway_location()

        self._device_setup_page.input_gateway_name(gateway_name)
        self._device_setup_page.tap_gateway_name_confirm()

        # 經銷商 ID 是可選步驟, 跳過即可
        self._device_setup_page.tap_skip_dealer_id()

        # 「設定完成」畫面按完成後, App 是停在「新增設備」畫面 (可以繼續加子裝置),
        # 不是直接回裝置分頁, 所以要再按左上角返回才會回到裝置清單
        self._device_setup_page.tap_setup_finish()
        self._add_device_type_page.tap_back()

    def disconnect_device(self) -> None:
        """解除關聯: 裝置卡片三個點 -> 設定選單「移除」-> 確認彈窗「移除」.

        移除是不可復原的操作 (會同步移除所有與此閘道器配對的裝置), 這裡當成
        teardown 用, 讓每輪測試跑完都回到未關聯的乾淨狀態。
        """
        self._home_page.tap_device_tab()
        self._device_page.tap_gateway_more()
        self._device_page.tap_settings_remove()
        self._device_page.tap_remove_confirm()

    def verify_setup_checklist_passed(self) -> None:
        assert_hidden(
            self.driver,
            self._device_setup_page.checklist_container_locator,
            "勾選需求並按 Next 後, Preparing for Setup 檢查清單畫面應該消失",
        )

    def verify_gateway_associated(self, expected_name: str) -> None:
        """驗證裝置分頁上出現剛才關聯的閘道器, 且名稱是命名時填的那個."""
        assert_text(
            self.driver,
            self._device_page.gateway_name_locator,
            expected_name,
            f"關聯完成後, 裝置分頁應顯示閘道器名稱「{expected_name}」",
            timeout=20,
            show_text=True,
        )

    def verify_gateway_removed(self) -> None:
        """驗證解除關聯後裝置分頁回到空狀態 (顯示「點擊以新增閘道器」)."""
        assert_visible(
            self.driver,
            self._device_page.empty_device_message_locator,
            "移除閘道器後, 裝置分頁應顯示新增閘道器的空狀態訊息",
            timeout=30,
        )
