"""ecogenie App 裝置設定精靈 (Device Setup Wizard) 的 Page Object.

Setup 介紹頁、Preparing for Setup 檢查清單等步驟共用同一個
device_setup_nav_host_fragment 與 Next 按鈕 (resource-id 相同), 所以合併在
同一個 Page Object 裡, 用方法名稱區分操作的是哪個步驟.
"""

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

_PACKAGE = "io.nextdrive.ecogenie.stg"


class DeviceSetupPage(BasePage):
    _NEXT_BUTTON = (AppiumBy.ID, f"{_PACKAGE}:id/deviceSetupNextButton")
    _CHECKLIST_CONTAINER = (AppiumBy.ID, f"{_PACKAGE}:id/deviceSetupChecklist")
    _PAIR_BUTTON = (AppiumBy.ID, f"{_PACKAGE}:id/next_button")
    _WIFI_PASSWORD_INPUT = (AppiumBy.CLASS_NAME, "android.widget.EditText")

    # 步驟5之6 為閘道器命名: 輸入框沒有 resource-id (畫面上只有這一個 EditText),
    # 但兩顆按鈕有專屬 id
    _GATEWAY_NAME_INPUT = (AppiumBy.CLASS_NAME, "android.widget.EditText")
    _GATEWAY_NAME_CONFIRM_BUTTON = (
        AppiumBy.ID,
        f"{_PACKAGE}:id/deviceNameConfirmButton",
    )

    # 步驟6之6 輸入經銷商 ID (可選, 直接跳過)
    _DEALER_ID_SKIP_BUTTON = (AppiumBy.ID, f"{_PACKAGE}:id/skipButton")

    # 設定完成畫面: deviceName 顯示剛才命名的名稱, 「完成」沿用 deviceSetupNextButton
    _SETUP_DONE_DEVICE_NAME = (AppiumBy.ID, f"{_PACKAGE}:id/deviceName")
    _SETUP_DONE_FINISH_BUTTON = _NEXT_BUTTON

    @property
    def checklist_container_locator(self) -> tuple:
        return self._CHECKLIST_CONTAINER

    def _requirement_checkbox_locator(self, requirement: str) -> tuple:
        return (
            AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiSelector().text("{requirement}")'
            f'.fromParent(new UiSelector().resourceId("{_PACKAGE}:id/item_checked"))',
        )

    def check_requirement(self, requirement: str) -> None:
        self._tap(self._requirement_checkbox_locator(requirement))

    def tap_next(self) -> None:
        self._tap(self._NEXT_BUTTON)

    def tap_pair(self) -> None:
        """Cube J LED 指示燈 bottom sheet 的「開始配對」按鈕."""
        self._tap(self._PAIR_BUTTON)

    def tap_pair_confirm(self, timeout: int = 15) -> None:
        """搜尋裝置完成後跳出的「可配對裝置」bottom sheet, 點選找到的裝置旁
        的「配對」按鈕確認配對. 跟 tap_pair() 用的是同一顆 resource-id
        (next_button, App 端這兩個 bottom sheet 共用同一個元件), 但兩個
        bottom sheet 不會同時出現, 所以沿用同一個 locator 個別等待/點擊沒問題.
        timeout 給長一點是因為要等 BLE 掃描完成裝置才會出現。
        """
        self._tap(self._PAIR_BUTTON, timeout)

    def select_wifi_network(self, ssid: str, timeout: int = 20) -> None:
        """步驟3之6「連線至 Wi-Fi」: 從裝置本體掃到的鄰近 Wi-Fi 清單點選指定
        SSID. 沒有專屬 resource-id, 直接用文字比對; timeout 給長一點是因為
        清單要等掃描完成才會出現。
        """
        locator = (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{ssid}")')
        self._tap(locator, timeout)

    def input_wifi_password(self, password: str) -> None:
        """點選 SSID 後跳出的密碼輸入 dialog. 密碼欄位沒有 resource-id, 用
        class name 定位 (畫面上只有這一個 EditText)。點下欄位常常會跳出
        Google Password Manager 的「使用已儲存密碼」建議蓋住整個畫面 (是系統
        autofill overlay, 不是 App 的 view, 點 X 或估座標常點不準), 用
        driver.back() 關閉最可靠。
        """
        password_input = self._wait_visible(self._WIFI_PASSWORD_INPUT)
        password_input.click()
        self.driver.back()
        password_input = self._wait_visible(self._WIFI_PASSWORD_INPUT)
        password_input.send_keys(password)

    def tap_wifi_connect(self, timeout: int = 10) -> None:
        """密碼輸入 dialog 的「連線」按鈕, 跟其他 App 內部彈窗共用同一顆
        arch_component_dialog_main_action_button (繼承自 BasePage)。
        """
        self._tap(self._ERROR_DIALOG_OK_BUTTON, timeout)

    def tap_skip_gateway_location(self, timeout: int = 20) -> None:
        """Wi-Fi 連線成功後的步驟4之6「閘道器的所在地」(可選), 按「稍後再說」
        跳過。timeout 給長一點是因為要等裝置真的連上 Wi-Fi 拿到 IP 後才會
        進到這個畫面。
        """
        locator = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("稍後再說")')
        self._tap(locator, timeout)

    def input_gateway_name(self, name: str, timeout: int = 20) -> None:
        """步驟5之6「為閘道器命名」: 填入閘道器名稱.

        名稱欄位沒有專屬 resource-id, 用 class name 定位 (畫面上只有這一個
        EditText)。填完用 IME 的 Enter (打勾) 收鍵盤, 不要用 driver.back() —
        實測 back 會直接退出整個畫面, 不是只關鍵盤。
        """
        name_input = self._wait_visible(self._GATEWAY_NAME_INPUT, timeout)
        name_input.click()
        name_input.send_keys(name)
        self.driver.press_keycode(66)  # KEYCODE_ENTER, 收起軟鍵盤

    def tap_gateway_name_confirm(self, timeout: int = 10) -> None:
        """步驟5之6 命名畫面的「確定」按鈕 (沒填名稱前是 disabled 的)."""
        self._tap(self._GATEWAY_NAME_CONFIRM_BUTTON, timeout)

    def tap_skip_dealer_id(self, timeout: int = 15) -> None:
        """步驟6之6「輸入經銷商 ID」(可選), 按「稍後再說」跳過."""
        self._tap(self._DEALER_ID_SKIP_BUTTON, timeout)

    def tap_setup_finish(self, timeout: int = 15) -> None:
        """設定完成畫面的「完成」按鈕, 按完會離開設定精靈."""
        self._tap(self._SETUP_DONE_FINISH_BUTTON, timeout)
