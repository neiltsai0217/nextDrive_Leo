"""Devices 模組的資料準備與預期值組裝(非 flow 編排):config 下發與閘道器關聯狀態."""

import time
from collections.abc import Callable

from libs.config_utils import get_config
from libs.date_utils import get_utc_iso_now
from testsuites.common.adb_v1_utils import get_config_json, get_gateway_pid
from testsuites.common.ioe_v1_api import get_gateways, get_single_devices, login_app
from testsuites.common.opensearch_api import search_gateway_config_dispatch
from testsuites.common.postgres_sql import get_gateway

# 一次完整的 config 下發依序是 wsync(版本核對)→ sendkey(金鑰交換)→ push(送出內容);
# 只看筆數 > 0 會漏掉做到一半就中斷的情況,所以三種都要出現
EXPECTED_COMMAND_TYPES = ["push", "sendkey", "wsync"]

# OpenSearch 索引延遲不固定(實測超過 20 秒),最多等 50 秒
_LOG_POLL_INTERVAL_SECONDS = 5
_LOG_POLL_MAX_ATTEMPTS = 10

_POLL_INTERVAL_SECONDS = 5
# api/v1/gateways 的 onlineStatus:1 = 上線,其餘視為離線(由實測變化推得,後端無文件)
_ONLINE_STATUS = 1


def _basic_user():
    return get_config(territory="tw", env="stage").users.basic_user


def get_access_token() -> str:
    """一般使用者(非 admin)的 access token;每次重新登入,不快取,避免長時間等待後過期."""
    user = _basic_user()
    return login_app(user.email, user.password)["access_token"]


# ---------- 閘道器關聯狀態 ----------

def is_gateway_associated() -> bool:
    """帳號底下是否有已關聯的閘道器;直接問後端,不受 App 畫面載入時機影響."""
    return bool(get_gateways(get_access_token()))


def find_gateway_dsn(serial: str | None) -> str | None:
    """
    用閘道器本機的 PID 對出解除註冊要用的 DSN;對不到時回傳 None.

    api/v1/gateways 沒有 dsn 欄位,要另外查 device-management 的裝置清單.
    """
    pid = get_gateway_pid(serial)
    devices = get_single_devices(get_access_token())
    matched = next((device for device in devices if device.get("pid") == pid), None)
    return matched.get("dsn") if matched else None


def is_gateway_online() -> bool:
    gateways = get_gateways(get_access_token())
    return bool(gateways) and gateways[0].get("onlineStatus") == _ONLINE_STATUS


def wait_for_gateway_online_status(
    expect_online: bool,
    timeout: int,
    on_poll: Callable[[], None] | None = None,
) -> bool:
    """
    輪詢到 server 判定的上線狀態符合預期或逾時,回傳最後一次查到的狀態.

    server 的離線判定有延遲(實測斷網後 108～128 秒),不能只看本機 WiFi 狀態.
    on_poll 在每次等待前呼叫,給呼叫端維持 Appium session 用.
    """
    elapsed = 0
    is_online = is_gateway_online()
    while is_online != expect_online and elapsed < timeout:
        if on_poll:
            on_poll()
        time.sleep(_POLL_INTERVAL_SECONDS)
        elapsed += _POLL_INTERVAL_SECONDS
        is_online = is_gateway_online()
    return is_online


def online_status_label(is_online: bool) -> str:
    return "上線" if is_online else "離線"


# ---------- server log 的 config 下發 ----------

def get_gateway_profile_id(serial: str | None) -> str:
    """閘道器的 profile_id,即 server log 裡的「gateway HW uuid」."""
    return get_gateway(get_gateway_pid(serial)).profile_id


def get_config_dispatch_command_types(profile_id: str, start_time: str) -> list[str]:
    """
    輪詢 start_time 之後「config 下發(device receive)」log 出現過的 command 種類,排序後回傳.

    用字串比對而非 json.loads:push 的 payload 很長,log 會被截斷成不合法的 json,
    但 command 欄位固定在最前面,不受截斷影響.
    查詢上限每次都取當下時間:後端可能在呼叫之後才送出下發,固定上限會永遠查不到.
    """
    seen_commands = set()
    for attempt in range(_LOG_POLL_MAX_ATTEMPTS):
        response = search_gateway_config_dispatch(profile_id, start_time, get_utc_iso_now())
        for hit in response.response.hits.hits:
            log_text = hit["_source"].get("log", "")
            seen_commands.update(
                command for command in EXPECTED_COMMAND_TYPES if f'"command":"{command}"' in log_text
            )
        if len(seen_commands) == len(EXPECTED_COMMAND_TYPES):
            break
        if attempt < _LOG_POLL_MAX_ATTEMPTS - 1:
            time.sleep(_LOG_POLL_INTERVAL_SECONDS)
    return sorted(seen_commands)


# ---------- 閘道器本機 config.json ----------

def wait_for_config_json(
    serial: str | None,
    is_ready: Callable[[dict], bool],
    timeout: int = 60,
) -> dict:
    """
    輪詢到 config.json 符合 is_ready 或逾時,回傳最後一次讀到的內容.

    App 操作幾秒就做完,但後端算好並送回閘道器需要時間,太快讀會讀到舊內容.
    """
    elapsed = 0
    config_json = get_config_json(serial)
    while not is_ready(config_json) and elapsed < timeout:
        time.sleep(_POLL_INTERVAL_SECONDS)
        elapsed += _POLL_INTERVAL_SECONDS
        config_json = get_config_json(serial)
    return config_json


def get_gateway_uuid(config_json: dict) -> str:
    return config_json.get("gateway", {}).get("gateway_uuid", "")


def get_modbus_config(config_json: dict) -> dict:
    return config_json.get("modbus", {})


def build_modbus_rtu_expected(modbus_device) -> dict:
    """裝置參數畫面輸入的值,整理成 config.json modbus.rtu 項目的對應欄位."""
    return {
        "serial_port": modbus_device.serial_port,
        "baud_rate": modbus_device.baud_rate,
        "terminal_settings": f"{modbus_device.data_bits}{modbus_device.parity}{modbus_device.stop_bit}",
        "modbus_id": modbus_device.modbus_id,
    }


def find_modbus_rtu(config_json: dict, modbus_device) -> dict | None:
    """在 config.json 的 modbus.rtu 找出參數與 modbus_device 相符的項目;找不到回傳 None."""
    expected = build_modbus_rtu_expected(modbus_device)
    for rtu in get_modbus_config(config_json).get("rtu", []):
        if all(str(rtu.get(key)) == value for key, value in expected.items()):
            return rtu
    return None


def get_modbus_rtu_settings(rtu: dict | None) -> dict | None:
    """只取出要比對的欄位並轉成字串,報告的「實際」才能跟「預期」逐欄對照."""
    if rtu is None:
        return None
    return {key: str(rtu.get(key)) for key in ("serial_port", "baud_rate", "terminal_settings", "modbus_id")}
