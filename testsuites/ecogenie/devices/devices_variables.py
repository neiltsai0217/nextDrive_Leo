"""Devices 模組頁面文案.

zh-TW 已在實機 (Pixel 8a, site_stage_tw) 的 Preparing for Setup 畫面實測
確認過文案; en/ja 尚未實機切換語言驗證, 暫時沿用 en 文案佔位, 待實測後校正.
"""

from dataclasses import dataclass

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


@dataclass(frozen=True)
class ModbusDevice:
    """TC-40138 用的 Modbus 子裝置測試資料, 欄位對應裝置設定精靈裡的各個欄位.

    宣告成 dataclass (而不是 dict/SimpleNamespace) 是為了讓 IDE 可以直接
    ctrl-click 每個屬性跳到定義, 也有型別提示, 方便之後改欄位時能全域搜尋到
    使用的地方。
    """

    device_type: str
    gateway_name: str
    brand: str
    model: str
    serial_port: str
    data_bits: str
    parity: str
    stop_bit: str
    baud_rate: str
    modbus_id: str


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

    # TC-40138: Modbus 子裝置關聯測試用的資料, 是後端型錄的品牌/型號名稱跟
    # 測試填入的裝置參數, 每次測試都固定用這組值, 不是 App 的畫面文案, 所以
    # 不走多語系表, 直接包成一個物件方便 flow 方法整組傳遞。
    MODBUS_DEVICE = ModbusDevice(
        device_type="Modbus 裝置",
        gateway_name=GATEWAY_NAME,
        brand="Shihlin",
        model="Shihlin_SPM-3",
        serial_port="USB1",
        data_bits="8",
        parity="N",
        stop_bit="1",
        baud_rate="9600",
        modbus_id="30",
    )


var = _DevicesVariables()

