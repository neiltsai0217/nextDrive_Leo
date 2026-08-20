"""業務層 Device Management Service (DMS) API 封裝 (Wrapper).

備用/重設用途: 當裝置需要重新關聯時, 直接呼叫這隻 API 在後端建立
「這個 DSN 屬於這個帳號」的關聯紀錄, 純粹是後端資料庫寫入, 不會連線到
裝置本身、也不會開關裝置的藍牙 (裝置藍牙開關請走
testsuites/common/v1_adb_utils.py 的 set_bluetooth_enabled)。
"""

from libs.http_utils import ioe_api_post_request
from variables.api import ble_protocol


def associate_device_via_ble(
    dsn: str,
    name: str,
    model: str,
    mac_address: str,
    access_token: str,
):
    """關聯裝置並取得 device_uuid (associationUuid)。

    dsn: 裝置的 DSN (例如 Cube J 的 ND8FOX0677203)
    name: BLE 廣播名稱
    model: 裝置的 model code (需與後端定義的實際值一致, 不可憑空猜測)
    mac_address: 裝置的藍牙 MAC address
    access_token: 一般使用者 (非 admin) 的 access token
    """
    body = {
        "singleDeviceDsn": dsn,
        "name": name,
        "model": model,
        "connectionInfo": {"macAddress": mac_address},
    }
    return ioe_api_post_request(
        f"/device-management/v1/associations/protocols/{ble_protocol}",
        json=body,
        access_token=access_token,
    )
