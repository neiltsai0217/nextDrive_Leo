from addict import Dict as AttrDict
http_status_code = AttrDict({
    "ok": 200,
    "unauthorized": 401,
    "forbidden": 403,
    "internal_server_error": 500
})

error_code_common = AttrDict({
    "ok": "0"
})

ble_protocol = "ble"

