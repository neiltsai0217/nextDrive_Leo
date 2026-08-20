"""Device 分頁測試案例.

這個模組所有 case 的前置條件都是「裝置已關聯完成」, 所以關聯/解除關聯寫成
module scope 的 autouse fixture: 整個模組只做一次關聯, 跑完所有 case 後再
解除關聯, 讓下一輪從乾淨狀態開始。
"""

import pytest

from libs.config_utils import get_config
from libs.log_utils import get_logger

from testsuites.athena.devices.devices_flow import DevicesFlow
from testsuites.common.postgres_sql import get_devices

from testsuites.athena.devices.devices_variables import var
_logger = get_logger(__name__)



class TestDevicePage:
    def test_01_ota(self, logged_in_driver, target_device_serial):
        _logger.info(get_devices("C0J111CAE3E700034"))
        # 測試升級

        
@pytest.fixture(scope="module", autouse=True)
def connect_and_disconnect_app(logged_in_driver, target_device_serial):
    wifi = get_config(territory="tw", env="stage").wifi
    flow = DevicesFlow(logged_in_driver, target_device_serial)
    flow.connect_device(
        var.DEVICE_TYPE_CUBE_J,
        var.CUBE_J_SETUP_REQUIREMENTS,
        wifi.ssid,
        wifi.password,
        var.GATEWAY_NAME,
    )
    flow.verify_gateway_associated(var.GATEWAY_NAME)

    yield flow

    flow.disconnect_device()
    flow.verify_gateway_removed()