import allure
"""業務層 Device Management Service (DMS) API 封裝 (Wrapper).

備用/重設用途: 當裝置需要重新關聯時, 直接呼叫這隻 API 在後端建立
「這個 DSN 屬於這個帳號」的關聯紀錄, 純粹是後端資料庫寫入, 不會連線到
裝置本身、也不會開關裝置的藍牙 (裝置藍牙開關請走
testsuites/common/v1_adb_utils.py 的 set_bluetooth_enabled)。
"""

from libs.http_utils import (
    eg3_app_api_get_request,
    eg3_app_api_post_request,
    ioe_api_delete_request,
    ioe_api_get_request,
    ioe_api_post_request,
)
from testsuites.common.common_utils import check_restful_response
from variables.api import ble_protocol

# App 登入時帶的裝置識別碼, App 本地用 UUID.randomUUID() 產生、存在本機、只有
# 清資料/重裝才會變 (反查 App bytecode 確認呼叫了 UUID.randomUUID(), 並用登出
# 再登入比對過同一次安裝內這個值不會變); 實測也確認 server 端沒有驗證這個值
# 要對應到已註冊裝置, 所以這裡固定用一組, 不用每次呼叫都重新產生。
APP_LOGIN_CLIENT_ID = "4lmvkrpfbpurass53hv0vglr0r"
APP_FIXED_UUID = "6488f2ec-e610-43b5-ba9e-0e57e34a3255"


@allure.step("call Login API")
def login_app(
    email: str,
    password: str,
    client_id: str = APP_LOGIN_CLIENT_ID,
    app_uuid: str = APP_FIXED_UUID,
    error=None,
):
    """呼叫 ecogenie App 本身走的登入 API (跟手動在 App 上登入同一條路), 取得 token.

    error: 預期錯誤碼 (例如驗證帳密錯誤應該回 401), None 表示預期登入成功。
    """
    response = eg3_app_api_post_request(
        "/api/account/v1/users/app/login",
        json={
            "email": email,
            "password": password,
            "clientId": client_id,
            "appUuid": app_uuid,
        },
    )
    data = check_restful_response(response, error).get("data", {})
    return {
        "access_token": data.get("accessToken"),
        "refresh_token": data.get("refreshToken"),
        "user_uuid": data.get("userUuid"),
    }


@allure.step("call Get Gateways API")
def get_gateways(access_token: str, error=None) -> list:
    """查詢目前帳號底下已關聯的閘道器清單 (api/v1/gateways), 拿來直接問後端
    「有沒有關聯」, 比看 App UI 有沒有渲染出閘道器名稱更準確 (不受畫面
    載入時機影響)。

    注意: 這個清單裡的項目沒有 dsn 欄位 (只有 uuid/pid 等), 需要 dsn 的話
    (例如要呼叫 unregister_device()) 要另外用 get_single_devices() 查。

    access_token: 一般使用者 (非 admin) 的 access token
    error: 預期錯誤碼, None 表示預期成功
    """
    response = eg3_app_api_get_request("/api/v1/gateways", access_token=access_token)
    return check_restful_response(response, error).get("gateways", [])


@allure.step("call Get Single Devices API")
def get_single_devices(access_token: str, error=None) -> list:
    """查詢目前帳號底下的裝置清單 (device-management/v1/devices), 每筆都帶
    dsn/pid/hardwareId, 用來把 pid 對應到 unregister_device() 需要的 dsn。

    access_token: 一般使用者 (非 admin) 的 access token
    error: 預期錯誤碼, None 表示預期成功
    """
    response = ioe_api_get_request("/device-management/v1/devices", access_token=access_token)
    return check_restful_response(response, error).get("data", {}).get("singleDevices", [])


@allure.step("call Associate Device via BLE API")
def associate_device_via_ble(
    dsn: str,
    name: str,
    model: str,
    mac_address: str,
    access_token: str,
    error=None,
):
    """關聯裝置並取得 device_uuid (associationUuid)。

    dsn: 裝置的 DSN (例如 Cube J 的 ND8FOX0677203)
    name: BLE 廣播名稱
    model: 裝置的 model code (需與後端定義的實際值一致, 不可憑空猜測)
    mac_address: 裝置的藍牙 MAC address
    access_token: 一般使用者 (非 admin) 的 access token
    error: 預期錯誤碼, None 表示預期成功
    """
    body = {
        "singleDeviceDsn": dsn,
        "name": name,
        "model": model,
        "connectionInfo": {"macAddress": mac_address},
    }
    response = ioe_api_post_request(
        f"/device-management/v1/associations/protocols/{ble_protocol}",
        json=body,
        access_token=access_token,
    )
    return check_restful_response(response, error)


@allure.step("call Register Device API")
def register_device(pid: str, name: str, access_token: str, error=None):
    """註冊裝置到後端 (device-management/v1/registrations)。

    pid: 裝置的 PID (例如 Cube J 的 C0J111CAE3E700034)
    name: 裝置顯示名稱
    access_token: 一般使用者 (非 admin) 的 access token
    error: 預期錯誤碼 (例如驗證「重複註冊應該被拒絕」時傳 403), None 表示
        預期註冊成功
    """
    body = {
        "pid": pid,
        "name": name,
    }
    response = ioe_api_post_request(
        "/device-management/v1/registrations",
        json=body,
        access_token=access_token,
    )
    return check_restful_response(response, error)


@allure.step("call Unregister Device API")
def unregister_device(dsn: str, access_token: str, error=None):
    """解除裝置註冊 (device-management/v1/registrations/:dsn)。

    dsn: 裝置的 DSN/PID
    access_token: 一般使用者 (非 admin) 的 access token
    error: 預期錯誤碼 (例如驗證「解除未註冊裝置應該被拒絕」時傳 403), None
        表示預期解除成功
    """
    response = ioe_api_delete_request(
        f"/device-management/v1/registrations/{dsn}",
        access_token=access_token,
    )
    return check_restful_response(response, error)
