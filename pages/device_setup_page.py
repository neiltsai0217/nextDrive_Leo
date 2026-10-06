"""ecogenie App 裝置設定精靈 (Device Setup Wizard) 的 Page Object.

Setup 介紹頁、Preparing for Setup 檢查清單等步驟共用同一個
device_setup_nav_host_fragment 與 Next 按鈕 (resource-id 相同), 所以合併在
同一個 Page Object 裡, 用方法名稱區分操作的是哪個步驟.
"""

import time

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

_PACKAGE = "io.nextdrive.ecogenie.stg"


class DeviceSetupPage(BasePage):
    _NEXT_BUTTON = (AppiumBy.ID, f"{_PACKAGE}:id/deviceSetupNextButton")
    _CHECKLIST_CONTAINER = (AppiumBy.ID, f"{_PACKAGE}:id/deviceSetupChecklist")
    _CHECKLIST_ITEM_CHECKED = f"{_PACKAGE}:id/item_checked"
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

    # Modbus 子裝置精靈的「裝置名稱」畫面 (步驟5之5), 跟閘道器命名畫面共用
    # deviceNameConfirmButton, 但多了一顆可以直接跳過的「稍後再說」
    _DEVICE_NAME_SKIP_BUTTON = (AppiumBy.ID, f"{_PACKAGE}:id/deviceNameSkipButton")

    # 設定完成畫面: deviceName 顯示剛才命名的名稱, 「完成」沿用 deviceSetupNextButton
    _SETUP_DONE_DEVICE_NAME = (AppiumBy.ID, f"{_PACKAGE}:id/deviceName")
    _SETUP_DONE_FINISH_BUTTON = _NEXT_BUTTON

    # Modbus 子裝置設定精靈: 品牌選擇/產品型號選擇畫面共用同一顆 nextButton
    # (跟閘道器精靈的 deviceSetupNextButton 是不同的 resource-id, 實測確認過)
    _BRAND_MODEL_NEXT_BUTTON = (AppiumBy.ID, f"{_PACKAGE}:id/nextButton")

    # 品牌/型號清單項目共用同一個 resource-id (id/name), 用文字比對區分
    _LIST_ITEM_NAME = f"{_PACKAGE}:id/name"

    # 打勾檢查清單後跳出的「配對閘道器」bottom sheet: 選擇要把這個 Modbus
    # 子裝置掛在哪一台已關聯的閘道器上, 「下一步」跟品牌/型號畫面共用同一顆
    # nextButton (實測 dump 確認過)
    _GATEWAY_CHOICE_NAME = f"{_PACKAGE}:id/nameTextView"
    _GATEWAY_CHOICE_TITLE = (AppiumBy.ID, f"{_PACKAGE}:id/title")

    # Modbus 精靈每個畫面共用同一組 resource-id 顯示標題跟「步驟X之Y」,
    # 用來驗證畫面文字是否符合預期 (準備設定/品牌選擇/產品型號/裝置參數)
    _STEP_TITLE = (AppiumBy.ID, f"{_PACKAGE}:id/main_headline_textView")
    _STEP_COUNTER = (AppiumBy.ID, f"{_PACKAGE}:id/deviceSetupSteps")

    # 裝置參數畫面 (序列埠/Data Bits/Parity/Stop Bit/鮑率) 都是同一種 NumberPicker
    # bottom sheet, 共用 doneButton/numberpicker_input
    _SERIAL_PORT_FIELD = (AppiumBy.ID, f"{_PACKAGE}:id/serialPortView")
    _DATA_BITS_FIELD = (AppiumBy.ID, f"{_PACKAGE}:id/dataBits")
    _PARITY_FIELD = (AppiumBy.ID, f"{_PACKAGE}:id/parity")
    _STOP_BIT_FIELD = (AppiumBy.ID, f"{_PACKAGE}:id/stopBit")
    _BAUD_RATE_FIELD = (AppiumBy.ID, f"{_PACKAGE}:id/baudRateView")
    _NUMBER_PICKER_INPUT = (AppiumBy.ID, "android:id/numberpicker_input")
    _NUMBER_PICKER_CONTAINER = (AppiumBy.CLASS_NAME, "android.widget.NumberPicker")
    _NUMBER_PICKER_ROW_BUTTON = (AppiumBy.CLASS_NAME, "android.widget.Button")
    _NUMBER_PICKER_DONE_BUTTON = (AppiumBy.ID, f"{_PACKAGE}:id/doneButton")

    # Modbus ID 是自由輸入的文字欄位, 沒有專屬 resource-id, 但外層容器
    # modbusIdView 有, 用 childSelector 從容器往下找唯一的 EditText
    _MODBUS_ID_INPUT = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        f'new UiSelector().resourceId("{_PACKAGE}:id/modbusIdView")'
        '.childSelector(new UiSelector().className("android.widget.EditText"))',
    )

    @property
    def checklist_container_locator(self) -> tuple:
        return self._CHECKLIST_CONTAINER

    @property
    def step_title_locator(self) -> tuple:
        return self._STEP_TITLE

    @property
    def step_counter_locator(self) -> tuple:
        return self._STEP_COUNTER

    @property
    def gateway_choice_title_locator(self) -> tuple:
        return self._GATEWAY_CHOICE_TITLE

    def _requirement_checkbox_locator(self, requirement: str) -> tuple:
        return (
            AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiSelector().text("{requirement}")'
            f'.fromParent(new UiSelector().resourceId("{self._CHECKLIST_ITEM_CHECKED}"))',
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

    def select_wifi_network(self, ssid: str, timeout: int = 40) -> None:
        """步驟3之6「連線至 Wi-Fi」: 從裝置本體掃到的鄰近 Wi-Fi 清單點選指定
        SSID. 沒有專屬 resource-id, 直接用文字比對; timeout 給長一點是因為
        清單要等掃描完成才會出現 (實測掃描偶爾會超過 20 秒才跑出目標 SSID)。
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

    def tap_skip_device_name(self, timeout: int = 10) -> None:
        """Modbus 子裝置精靈的「裝置名稱」畫面 (可選), 按「稍後再說」跳過."""
        self._tap(self._DEVICE_NAME_SKIP_BUTTON, timeout)

    def tap_setup_finish(self, timeout: int = 15) -> None:
        """設定完成畫面的「完成」按鈕, 按完會離開設定精靈."""
        self._tap(self._SETUP_DONE_FINISH_BUTTON, timeout)

    def check_all_requirements(self) -> None:
        """勾選檢查清單目前顯示的所有項目.

        跟 check_requirement() 不同: 不假設項目文案跟數量 (Modbus 子裝置的
        checklist 項目跟 Cube J 閘道器不一樣), 直接把畫面上所有 item_checked
        checkbox 都點掉, 不特定比對文字。
        """
        checkboxes = self.driver.find_elements(AppiumBy.ID, self._CHECKLIST_ITEM_CHECKED)
        for checkbox in checkboxes:
            checkbox.click()

    def _list_item_locator(self, name: str) -> tuple:
        return (
            AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiSelector().resourceId("{self._LIST_ITEM_NAME}").text("{name}")',
        )

    def _gateway_choice_locator(self, gateway_name: str) -> tuple:
        return (
            AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiSelector().resourceId("{self._GATEWAY_CHOICE_NAME}").text("{gateway_name}")',
        )

    def select_gateway_to_pair(self, gateway_name: str) -> None:
        """「配對閘道器」bottom sheet: 選擇要掛載 Modbus 子裝置的閘道器
        (id/nameTextView 本身 clickable=false, 跟品牌/型號清單同一種機制,
        點文字座標會冒泡到外層可點擊容器)。
        """
        self._tap(self._gateway_choice_locator(gateway_name))

    def select_brand(self, brand: str) -> None:
        """品牌選擇畫面: 點選清單裡指定品牌 (id/name 本身 clickable=false,
        但點擊其座標範圍會透過觸控事件冒泡到外層可點擊的容器, 跟
        select_device_type() 的機制相同, 實測確認可行)。
        """
        self._tap(self._list_item_locator(brand))

    def select_model(self, model: str) -> None:
        """產品型號畫面: 點選清單裡指定型號, 跟 select_brand() 共用同一種
        清單項目結構 (id/name)。
        """
        self._tap(self._list_item_locator(model))

    def tap_brand_model_next(self, timeout: int = 10) -> None:
        """品牌選擇/產品型號畫面共用的「下一步」按鈕 (nextButton)."""
        self._tap(self._BRAND_MODEL_NEXT_BUTTON, timeout)

    def _select_number_picker_value(self, target_value: str, max_scrolls: int = 40) -> None:
        """NumberPicker bottom sheet 通用選值邏輯.

        實測發現直接點擊清單裡的目標值只會把它捲到置中, 不會套用也不會關閉
        bottom sheet, 必須再點「完成」才會真正套用到欄位上。

        置中值上下最多會各出現一顆同樣是 android.widget.Button、沒有專屬
        resource-id 的按鈕 (分別代表往前/往後一格)。實測發現用 UiSelector
        字串 (NumberPicker.childSelector(Button)) 找這種「同一種 class 有
        多個 sibling」的結構, find_elements 每次只會回傳其中一個 (實測確認
        固定回傳上面那顆「往前」按鈕), 不會回傳全部符合的按鈕, 導致永遠找
        不到「下面」那顆而誤判成已經到底。改成先定位 NumberPicker 容器本身,
        再用 element.find_elements() 在該容器底下找所有 Button, 才能真的
        拿到兩顆都算, 之後用 y 座標篩出置中值下面那顆, 確保永遠往同一個
        方向 (往後) 捲動。
        """
        picker_container = self._wait_visible(self._NUMBER_PICKER_CONTAINER)

        for _ in range(max_scrolls):
            picker_input = self._wait_visible(self._NUMBER_PICKER_INPUT)
            if picker_input.text == target_value:
                self._tap(self._NUMBER_PICKER_DONE_BUTTON)
                return

            input_y = picker_input.location["y"]
            buttons = picker_container.find_elements(*self._NUMBER_PICKER_ROW_BUTTON)
            below_buttons = [b for b in buttons if b.location["y"] > input_y]
            if not below_buttons:
                raise ValueError(
                    f"目前值 {picker_input.text!r} 下面已經沒有可以再往後捲的按鈕,"
                    f" 但還沒捲到目標值 {target_value!r} (可能已經是最大值)"
                )
            below_buttons[0].click()
            time.sleep(0.3)

        raise TimeoutError(f"捲動 {max_scrolls} 次仍未捲到目標值 {target_value!r}")

    def select_serial_port(self, value: str) -> None:
        self._tap(self._SERIAL_PORT_FIELD)
        self._select_number_picker_value(value)

    def select_data_bits(self, value: str) -> None:
        self._tap(self._DATA_BITS_FIELD)
        self._select_number_picker_value(value)

    def select_parity(self, value: str) -> None:
        self._tap(self._PARITY_FIELD)
        self._select_number_picker_value(value)

    def select_stop_bit(self, value: str) -> None:
        self._tap(self._STOP_BIT_FIELD)
        self._select_number_picker_value(value)

    def select_baud_rate(self, value: str) -> None:
        self._tap(self._BAUD_RATE_FIELD)
        self._select_number_picker_value(value)

    def input_modbus_id(self, modbus_id: str) -> None:
        self._input_text(self._MODBUS_ID_INPUT, modbus_id)
