import allure
import pytest

from testsuites.ecogenie.devices.devices_flow import DevicesFlow
from testsuites.ecogenie.devices.devices_variables import var

# 每個 case 各自用 API 建立 / 清除關聯狀態,不依賴前一個 case 留下的狀態;
# 只有 TC-40137 要驗證「上線」這個事件本身,所以走 App 關聯



@allure.feature("裝置")
@allure.story("Config 下發")
class TestDevicePage:

    @allure.title("TC-40138: [IoEP] 關聯任意裝置後，確認 config 是否正常送下去")
    def test_02_connect_devices(self, devices_flow: DevicesFlow, gateway_disassociated_around_test):
        devices_flow.associate_gateway_via_api(var.GATEWAY_NAME)                # a. 透過 API 關聯閘道器
        devices_flow.verify_modbus_config_empty()                               # b. 驗證 config.json 的 modbus 欄位為空
        started_at = devices_flow.connect_modbus_device(var.MODBUS_DEVICE)      # c. 關聯 Modbus 子裝置
        devices_flow.verify_server_config_dispatch(started_at)                  # d. 驗證 server log 的 config 下發指令
        devices_flow.verify_modbus_rtu_settings(var.MODBUS_DEVICE)              # e. 驗證 config.json 的 modbus.rtu 參數
        devices_flow.verify_modbus_device_uuid(var.MODBUS_DEVICE)               # f. 驗證 config.json 的 modbus device_uuid


    @allure.title("TC-40139: [IoEP] 解關聯任意裝置後，確認 config 是否正常送下去")
    def test_03_disconnect_devices(self, devices_flow: DevicesFlow, gateway_disassociated_around_test):
        devices_flow.associate_gateway_via_api(var.GATEWAY_NAME)                # a. 透過 API 關聯閘道器
        devices_flow.connect_modbus_device(var.MODBUS_DEVICE)                   # b. 關聯 Modbus 子裝置
        started_at = devices_flow.disconnect_modbus_device(var.MODBUS_DEVICE.model)  # c. 解除關聯 Modbus 子裝置
        devices_flow.verify_server_config_dispatch(started_at)                  # d. 驗證 server log 的 config 下發指令
        devices_flow.verify_modbus_config_empty()                               # e. 驗證 config.json 的 modbus 欄位為空


    @allure.title("TC-40140: [IoEP] Gateway 解關聯後，確認 config 是否正常送下去")
    def test_04_disconnect_gateway(self, devices_flow: DevicesFlow, gateway_disassociated_around_test):
        devices_flow.associate_gateway_via_api(var.GATEWAY_NAME)                # a. 透過 API 關聯閘道器
        started_at = devices_flow.disconnect_device()                           # b. 在 App 解除關聯閘道器
        devices_flow.verify_server_config_dispatch(started_at)                  # c. 驗證 server log 的 config 下發指令
        devices_flow.verify_config_json_empty()                                 # d. 驗證 config.json 為空


    @allure.title("TC-40137: [IoEP] Gateway 上線後，確認 config 是否正常送下去")
    def test_05_after_gateway_connect_verify_server_log(
        self, devices_flow: DevicesFlow, gateway_disassociated_around_test
    ):
        started_at = devices_flow.connect_device(                               # a. 在 App 關聯閘道器
            var.DEVICE_TYPE_CUBE_J, var.CUBE_J_SETUP_REQUIREMENTS, var.GATEWAY_NAME
        )
        devices_flow.verify_server_config_dispatch(started_at)                  # b. 驗證 server log 的 config 下發指令
        devices_flow.verify_config_json_not_empty()                             # c. 驗證 config.json 有內容
        devices_flow.verify_gateway_uuid()                                      # d. 驗證 config.json 的 gateway_uuid


    @allure.title("TC-61088: [IoEP] Gateway 離線後，確認 config 是否正常送下去")
    def test_06_gateway_offline(self, devices_flow: DevicesFlow, gateway_associated_before_test):
        started_at = devices_flow.take_gateway_offline()                        # a. 讓閘道器離線
        devices_flow.bring_gateway_online()                                     # b. 讓閘道器重新上線
        devices_flow.verify_server_config_dispatch(started_at)                  # c. 驗證 server log 的 config 下發指令
        devices_flow.verify_gateway_uuid()                                      # d. 驗證 config.json 的 gateway_uuid



@pytest.fixture(scope="module", autouse=True)
def devices_flow(logged_in_driver, target_device_serial) -> DevicesFlow:
    return DevicesFlow(logged_in_driver, target_device_serial)


@pytest.fixture(scope="function")
def gateway_disassociated_around_test(devices_flow: DevicesFlow):
    """
    case 開始前與結束後都解除關聯:開始前清掉上一輪失敗留下的殘留狀態,
    結束後不論成敗都還原,讓下一個 case 從未關聯的乾淨狀態開始.
    解除閘道器關聯會連帶清掉底下的子裝置,不用另外移除 Modbus 裝置.
    """
    devices_flow.disassociate_gateway_via_api()
    yield
    devices_flow.disassociate_gateway_via_api()


@pytest.fixture(scope="function")
def gateway_associated_before_test(devices_flow: DevicesFlow):
    """
    TC-61088 的前置條件是「已關聯 gateway」,先用 API 關聯好.
    結束後先把 WiFi 開回來再解除關聯:case 若在斷網期間失敗,閘道器會停在 WiFi 關閉的狀態.
    """
    devices_flow.associate_gateway_via_api(var.GATEWAY_NAME)
    yield
    devices_flow.restore_gateway_wifi()
    devices_flow.disassociate_gateway_via_api()
