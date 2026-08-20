"""Devices 模組頁面文案.

zh-TW 已在實機 (Pixel 8a, site_stage_tw) 的 Preparing for Setup 畫面實測
確認過文案; en/ja 尚未實機切換語言驗證, 暫時沿用 en 文案佔位, 待實測後校正.
"""

from libs.config_utils import config

_DEFAULT_SITE_LANGUAGE = "zh-TW"

_WORDING = {
    "DEVICE_TYPE_CUBE_J": {
        "zh-TW": "Cube J",
        "en": "Cube J",
        "ja": "Cube J",
    },
    "REQUIREMENT_PLUG_IN_DEVICE": {
        "zh-TW": "將 Cube J 插上插座",
        "en": "Plug in your Cube J",
        "ja": "Plug in your Cube J",
    },
    "REQUIREMENT_TURN_ON_BLUETOOTH": {
        "zh-TW": "打開手機藍牙",
        "en": "Turn on your phone Bluetooth",
        "ja": "Turn on your phone Bluetooth",
    },
    "REQUIREMENT_CONNECT_WIFI": {
        "zh-TW": "連線至 Wi-Fi",
        "en": "Connect to Wi-Fi",
        "ja": "Connect to Wi-Fi",
    },
}

_language = config.services.accept_language
if _language not in ("zh-TW", "en", "ja"):
    _language = _DEFAULT_SITE_LANGUAGE


def _wording(key: str) -> str:
    return _WORDING[key][_language]


class _DevicesVariables:
    # 關聯時要填給閘道器的名稱, 不是 App 的文案, 所以不走多語系表
    GATEWAY_NAME = "Automation Cube"

    DEVICE_TYPE_CUBE_J = _wording("DEVICE_TYPE_CUBE_J")
    REQUIREMENT_PLUG_IN_DEVICE = _wording("REQUIREMENT_PLUG_IN_DEVICE")
    REQUIREMENT_TURN_ON_BLUETOOTH = _wording("REQUIREMENT_TURN_ON_BLUETOOTH")
    REQUIREMENT_CONNECT_WIFI = _wording("REQUIREMENT_CONNECT_WIFI")

    CUBE_J_SETUP_REQUIREMENTS = [
        REQUIREMENT_PLUG_IN_DEVICE,
        REQUIREMENT_TURN_ON_BLUETOOTH,
        REQUIREMENT_CONNECT_WIFI,
    ]


var = _DevicesVariables()
