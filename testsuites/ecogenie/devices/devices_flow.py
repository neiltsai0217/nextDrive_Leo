import allure

from libs.appium_utils import keep_appium_session_alive
from libs.assert_utils import (
    assert_equal,
    assert_greater_than,
    assert_hidden,
    assert_not_equal,
    assert_text,
    assert_visible,
)
from libs.config_utils import get_config
from libs.date_utils import get_utc_iso_now
from pages.add_device_type_page import AddDeviceTypePage
from pages.advanced_devices_page import AdvancedDevicesPage
from pages.device_page import DevicePage
from pages.device_setup_page import DeviceSetupPage
from pages.home_page import HomePage
from testsuites.common.adb_v1_utils import (
    connect_wifi,
    get_config_json,
    get_gateway_pid,
    press_wifi_association_button,
    set_wifi_network_enabled,
    wait_for_device_reboot,
)
from testsuites.common.ioe_v1_api import register_device, unregister_device
from testsuites.ecogenie.devices.config_sync_suites import (
    EXPECTED_COMMAND_TYPES,
    build_modbus_rtu_expected,
    find_gateway_dsn,
    find_modbus_rtu,
    get_access_token,
    get_config_dispatch_command_types,
    get_gateway_profile_id,
    get_gateway_uuid,
    get_modbus_config,
    get_modbus_rtu_settings,
    is_gateway_associated,
    online_status_label,
    wait_for_config_json,
    wait_for_gateway_online_status,
)

# server 判定上線約 1 分鐘內完成;判定離線實測要 108～128 秒,所以離線另外給較長的上限
_ONLINE_TIMEOUT_SECONDS = 90
_OFFLINE_TIMEOUT_SECONDS = 240


class DevicesFlow:
    """裝置分頁的閘道器 / 子裝置關聯操作,以及關聯變動後的 config 下發驗證."""

    def __init__(self, driver, target_device_serial: str | None = None):
        self.driver = driver
        # 待測閘道器本體的 adb serial,不是跑 App 的手機
        self._target_device_serial = target_device_serial
        self._home_page = HomePage(driver)
        self._device_page = DevicePage(driver)
        self._add_device_type_page = AddDeviceTypePage(driver)
        self._device_setup_page = DeviceSetupPage(driver)
        self._advanced_devices_page = AdvancedDevicesPage(driver)

    # ---------- 閘道器關聯 / 解除關聯 ----------

    @allure.step("在 App 關聯閘道器")
    def connect_device(self, device_type: str, requirements: list, gateway_name: str) -> str:
        """走 App 的新增閘道器精靈完成關聯,回傳操作開始時間(查 server log 的時間下限)."""
        started_at = get_utc_iso_now()
        wifi = get_config(territory="tw", env="stage").wifi

        self._home_page.tap_device_tab()
        if self._device_page.is_gateway_associated():
            # 閘道器本體被 reset 過時 server 的關聯紀錄還在,要先清掉,否則精靈走到一半才會被擋下
            self.disconnect_device()

        self._start_pairing(device_type, requirements)

        self._device_setup_page.select_wifi_network(wifi.ssid)
        self._device_setup_page.input_wifi_password(wifi.password)
        self._device_setup_page.tap_wifi_connect()

        # 所在地與經銷商 ID 都是選填,跳過不影響關聯
        self._device_setup_page.tap_skip_gateway_location()
        self._device_setup_page.input_gateway_name(gateway_name)
        self._device_setup_page.tap_gateway_name_confirm()
        self._device_setup_page.tap_skip_dealer_id()

        # 「設定完成」按完成後停在「新增設備」畫面,要再返回才回到裝置清單
        self._device_setup_page.tap_setup_finish()
        self._add_device_type_page.tap_back()
        return started_at

    def _start_pairing(self, device_type: str, requirements: list) -> None:
        self._home_page.tap_device_tab()
        self._device_page.tap_add_device()
        self._add_device_type_page.select_device_type(device_type)
        self._device_setup_page.tap_next()

        # 真人是按閘道器本體的實體按鈕開藍牙配對,自動化改用 adb 對閘道器送按鍵事件
        press_wifi_association_button(self._target_device_serial)

        for requirement in requirements:
            self._device_setup_page.check_requirement(requirement)

        self._device_setup_page.tap_next()
        self._device_setup_page.tap_pair()
        self._device_setup_page.tap_pair_confirm()

    @allure.step("透過 API 關聯閘道器")
    def associate_gateway_via_api(self, gateway_name: str) -> str:
        """讓閘道器連上 WiFi 後直接打註冊 API,不走 App 精靈;回傳操作開始時間."""
        started_at = get_utc_iso_now()
        wifi = get_config(territory="tw", env="stage").wifi
        connect_wifi(self._target_device_serial, wifi.ssid, wifi.password)

        # 註冊 API 不是冪等的:同一個 PID 重複註冊會回 403,所以已關聯就不再註冊
        if not is_gateway_associated():
            register_device(get_gateway_pid(self._target_device_serial), gateway_name, get_access_token())
        return started_at

    @allure.step("透過 API 解除關聯閘道器")
    def disassociate_gateway_via_api(self) -> None:
        """帳號底下沒有關聯時直接略過,讓 setup / teardown 可以無條件呼叫."""
        if not is_gateway_associated():
            return

        dsn = find_gateway_dsn(self._target_device_serial)
        assert_not_equal(
            dsn, None,
            "確認已關聯的閘道器對得到 DSN(對不到代表帳號關聯的不是這台待測閘道器,需人工處理)",
        )
        unregister_device(dsn, get_access_token())

        # 線上的閘道器解除關聯後會自己重開機,等它開完才回傳,否則下一個動作的 adb 指令會撞上重開機
        wait_for_device_reboot(self._target_device_serial)

    @allure.step("在 App 解除關聯閘道器")
    def disconnect_device(self) -> str:
        """裝置卡片「更多」→「移除」→ 確認;回傳操作開始時間."""
        started_at = get_utc_iso_now()

        self._home_page.tap_device_tab()
        self._device_page.tap_gateway_more()
        self._device_page.tap_settings_remove()
        self._device_page.tap_remove_confirm()

        wait_for_device_reboot(self._target_device_serial)
        return started_at

    # ---------- Modbus 子裝置 ----------

    @allure.step("關聯 Modbus 子裝置")
    def connect_modbus_device(self, modbus_device) -> str:
        """
        走「新增設備」精靈在已關聯的閘道器下新增 Modbus 子裝置,回傳操作開始時間.

        只驗證 App → 後端 → 閘道器的 config 派送,不需要接上實體 Modbus 裝置.
        """
        started_at = get_utc_iso_now()

        self._home_page.tap_device_tab()
        # 閘道器若是透過 API 關聯,App 顯示的是教學版的新增按鈕;tap_add_device() 兩種都認得
        self._device_page.tap_add_device()
        self._add_device_type_page.tap_advanced_devices()
        self._add_device_type_page.select_device_type(modbus_device.device_type)
        self._device_setup_page.tap_next()

        self._verify_wizard_step("步驟1之5", "準備設定")
        self._device_setup_page.check_all_requirements()
        self._device_setup_page.tap_next()

        assert_text(self.driver, self._device_setup_page.gateway_choice_title_locator, "配對閘道器",
                    "驗證配對閘道器畫面標題")
        self._device_setup_page.select_gateway_to_pair(modbus_device.gateway_name)
        self._device_setup_page.tap_brand_model_next()

        self._verify_wizard_step("步驟2之5", "品牌選擇")
        self._device_setup_page.select_brand(modbus_device.brand)
        self._device_setup_page.tap_brand_model_next()

        self._verify_wizard_step("步驟3之5", "產品型號")
        self._device_setup_page.select_model(modbus_device.model)
        self._device_setup_page.tap_brand_model_next()

        self._verify_wizard_step("步驟4之5", "裝置參數")
        self._device_setup_page.select_serial_port(modbus_device.serial_port)
        self._device_setup_page.select_data_bits(modbus_device.data_bits)
        self._device_setup_page.select_parity(modbus_device.parity)
        self._device_setup_page.select_stop_bit(modbus_device.stop_bit)
        self._device_setup_page.select_baud_rate(modbus_device.baud_rate)
        self._device_setup_page.input_modbus_id(modbus_device.modbus_id)
        self._device_setup_page.tap_next()

        self._verify_wizard_step("步驟5之5", "裝置名稱")
        self._device_setup_page.tap_skip_device_name()

        self._device_setup_page.tap_setup_finish()
        self._add_device_type_page.tap_back()
        return started_at

    def _verify_wizard_step(self, expected_step: str, expected_title: str) -> None:
        """每個精靈畫面都驗證文字:走錯畫面但元件剛好點得到時,光看沒有例外不會發現."""
        assert_text(self.driver, self._device_setup_page.step_counter_locator, expected_step,
                    f"驗證設定精靈步驟「{expected_title}」的步驟編號")
        assert_text(self.driver, self._device_setup_page.step_title_locator, expected_title,
                    f"驗證設定精靈步驟「{expected_title}」的標題")

    @allure.step("解除關聯 Modbus 子裝置")
    def disconnect_modbus_device(self, device_name: str) -> str:
        """裝置分頁 →「進階裝置」→ 該裝置的「設定」→「移除」→ 確認;回傳操作開始時間."""
        started_at = get_utc_iso_now()

        self._home_page.tap_device_tab()
        self._device_page.tap_advanced_devices_footer()
        self._advanced_devices_page.tap_device_settings(device_name)
        self._advanced_devices_page.tap_settings_remove()
        self._advanced_devices_page.tap_remove_confirm()
        # 移除最後一個子裝置後 Toolbar 返回鍵會失效,用系統返回鍵回到裝置分頁,
        # 否則同一個 session 的下一個 case 找不到底部分頁列
        self._advanced_devices_page.press_back()
        return started_at

    # ---------- 閘道器上線 / 離線 ----------

    @allure.step("讓閘道器離線")
    def take_gateway_offline(self) -> str:
        """
        停用閘道器的 WiFi 連線讓它真的斷網,等 server 判定離線後回傳斷網開始時間.

        用 wpa_supplicant 層級的 wifi off:rfkill 不會觸發 server 的離線偵測,
        factory reset 則會清掉關聯設定.
        """
        # 剛關聯完 server 還沒標成上線,這時斷網會立刻被當成「已離線」,閘道器其實沒離線過
        self._verify_gateway_online_status(expect_online=True, timeout=_ONLINE_TIMEOUT_SECONDS)

        started_at = get_utc_iso_now()
        set_wifi_network_enabled(self._target_device_serial, False)
        self._verify_gateway_online_status(expect_online=False, timeout=_OFFLINE_TIMEOUT_SECONDS)
        return started_at

    @allure.step("讓閘道器重新上線")
    def bring_gateway_online(self) -> None:
        """wifi off 沒有清掉儲存的網路設定,打開後閘道器會自己連回去,不用重新關聯."""
        set_wifi_network_enabled(self._target_device_serial, True)
        self._verify_gateway_online_status(expect_online=True, timeout=_ONLINE_TIMEOUT_SECONDS)

    @allure.step("恢復閘道器 WiFi 連線")
    def restore_gateway_wifi(self) -> None:
        """teardown 用:case 在斷網期間失敗時,確保閘道器不會停在 WiFi 關閉的狀態."""
        set_wifi_network_enabled(self._target_device_serial, True)

    def _verify_gateway_online_status(self, expect_online: bool, timeout: int) -> None:
        is_online = wait_for_gateway_online_status(
            expect_online, timeout, on_poll=self._keep_appium_session_alive
        )
        assert_equal(
            online_status_label(is_online),
            online_status_label(expect_online),
            f"等待 server 判定閘道器{online_status_label(expect_online)}",
            context={"等待上限(秒)": timeout},
        )

    def _keep_appium_session_alive(self) -> None:
        """長時間只打 API / adb 時定期呼叫,避免 Appium session 因 newCommandTimeout 被收掉."""
        keep_appium_session_alive(self.driver)

    # ---------- 驗證:App 畫面 ----------

    @allure.step("驗證 準備設定檢查清單 已消失")
    def verify_setup_checklist_passed(self) -> None:
        assert_hidden(self.driver, self._device_setup_page.checklist_container_locator,
                      "驗證準備設定檢查清單已消失", target="準備設定檢查清單")

    @allure.step("驗證 裝置分頁 閘道器名稱")
    def verify_gateway_associated(self, expected_name: str) -> None:
        assert_text(self.driver, self._device_page.gateway_name_locator, expected_name,
                    "驗證裝置分頁的閘道器名稱", timeout=20)

    @allure.step("驗證 裝置分頁 空狀態訊息")
    def verify_gateway_removed(self) -> None:
        assert_visible(self.driver, self._device_page.empty_device_message_locator,
                       "驗證裝置分頁回到未關聯的空狀態", target="新增閘道器的空狀態訊息", timeout=30)

    # ---------- 驗證:config 下發 ----------

    @allure.step("驗證 server log 的 config 下發指令")
    def verify_server_config_dispatch(self, started_at: str) -> None:
        """started_at 之後的 websocket log 要同時出現 wsync / sendkey / push,缺一代表下發不完整."""
        self._keep_appium_session_alive()
        profile_id = get_gateway_profile_id(self._target_device_serial)
        command_types = get_config_dispatch_command_types(profile_id, started_at)
        self._keep_appium_session_alive()

        assert_equal(
            command_types,
            EXPECTED_COMMAND_TYPES,
            "驗證 server log 出現的 config 下發指令",
            context={"gateway_profile_id": profile_id, "查詢起始時間(UTC)": started_at},
        )

    @allure.step("驗證 config.json 有內容")
    def verify_config_json_not_empty(self) -> None:
        config_json = get_config_json(self._target_device_serial)
        assert_greater_than(
            len(config_json), 0,
            "驗證閘道器本機 config.json 的區塊數量",
            context={"config.json 區塊": list(config_json.keys())},
        )

    @allure.step("驗證 config.json 的 gateway_uuid")
    def verify_gateway_uuid(self) -> None:
        """後端曾在關聯後又推一份 gateway_uuid 為空字串的 config 蓋掉正確版本,只驗非空抓不到."""
        config_json = get_config_json(self._target_device_serial)
        assert_not_equal(
            get_gateway_uuid(config_json), "",
            "驗證閘道器本機 config.json 的 gateway_uuid 有值",
            context={"config.json gateway": config_json.get("gateway")},
        )

    @allure.step("驗證 config.json 為空")
    def verify_config_json_empty(self) -> None:
        config_json = wait_for_config_json(self._target_device_serial, lambda content: content == {})
        assert_equal(config_json, {}, "驗證閘道器本機 config.json 已清空")

    @allure.step("驗證 config.json 的 modbus 欄位為空")
    def verify_modbus_config_empty(self) -> None:
        config_json = wait_for_config_json(
            self._target_device_serial, lambda content: get_modbus_config(content) == {}
        )
        assert_equal(get_modbus_config(config_json), {}, "驗證閘道器本機 config.json 的 modbus 欄位為空")

    @allure.step("驗證 config.json 的 modbus.rtu 參數")
    def verify_modbus_rtu_settings(self, modbus_device) -> None:
        config_json = wait_for_config_json(
            self._target_device_serial, lambda content: find_modbus_rtu(content, modbus_device) is not None
        )
        assert_equal(
            get_modbus_rtu_settings(find_modbus_rtu(config_json, modbus_device)),
            build_modbus_rtu_expected(modbus_device),
            "驗證閘道器本機 config.json 的 modbus.rtu 參數與裝置參數畫面輸入的一致",
            context={"config.json modbus": get_modbus_config(config_json)},
        )

    @allure.step("驗證 config.json 的 modbus device_uuid")
    def verify_modbus_device_uuid(self, modbus_device) -> None:
        """device_uuid 有值代表後端有配發子裝置身份,不是只把參數原樣送回."""
        config_json = get_config_json(self._target_device_serial)
        rtu = find_modbus_rtu(config_json, modbus_device) or {}
        assert_not_equal(
            rtu.get("device_uuid", ""), "",
            "驗證閘道器本機 config.json 的 modbus.rtu 項目有 device_uuid",
            context={"config.json modbus.rtu 項目": rtu},
        )
