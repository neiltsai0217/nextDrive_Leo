# 完整範例：Devices（config 下發）

實際程式在 `testsuites/ecogenie/devices/`，新模組照這個分工寫。

```text
testsuites/ecogenie/devices/
  devices_variables.py      # 文案（多語系）、測試資料
  config_sync_suites.py     # 資料準備：API / DB / adb 解析、輪詢等待、build expected
  devices_flow.py           # 操作編排 + 斷言（一步一 function）
  test_device_page.py       # 一行一 Step
```

```python
# test_device_page.py：只描述順序,接住操作回傳的 started_at 再傳給驗證
@allure.title("TC-61088: [IoEP] Gateway 離線後，確認 config 是否正常送下去")
def test_06_gateway_offline(self, devices_flow: DevicesFlow, gateway_associated_before_test):
    started_at = devices_flow.take_gateway_offline()                        # a. 讓閘道器離線
    devices_flow.bring_gateway_online()                                     # b. 讓閘道器重新上線
    devices_flow.verify_server_config_dispatch(started_at)                  # c. 驗證 server log 的 config 下發指令
    devices_flow.verify_gateway_uuid()                                      # d. 驗證 config.json 的 gateway_uuid

# config_sync_suites.py：輪詢與解析,回傳結果,不做斷言
def wait_for_gateway_online_status(expect_online: bool, timeout: int, on_poll=None) -> bool:
    ...

def get_gateway_uuid(config_json: dict) -> str:
    return config_json.get("gateway", {}).get("gateway_uuid", "")

# devices_flow.py：操作回傳開始時間;等待逾時用斷言表示,不 raise
@allure.step("讓閘道器離線")
def take_gateway_offline(self) -> str:
    # 剛關聯完 server 還沒標成上線,這時斷網會立刻被當成「已離線」,閘道器其實沒離線過
    self._verify_gateway_online_status(expect_online=True, timeout=_ONLINE_TIMEOUT_SECONDS)

    started_at = get_utc_iso_now()
    set_wifi_network_enabled(self._target_device_serial, False)
    self._verify_gateway_online_status(expect_online=False, timeout=_OFFLINE_TIMEOUT_SECONDS)
    return started_at

def _verify_gateway_online_status(self, expect_online: bool, timeout: int) -> None:
    is_online = wait_for_gateway_online_status(expect_online, timeout, on_poll=self._keep_appium_session_alive)
    assert_equal(
        online_status_label(is_online),
        online_status_label(expect_online),
        f"等待 server 判定閘道器{online_status_label(expect_online)}",
        context={"等待上限(秒)": timeout},
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
```

對應的報告：
```text
讓閘道器離線
  等待 server 判定閘道器上線     預期 上線 / 實際 上線 / PASS
  等待 server 判定閘道器離線     預期 離線 / 實際 離線 / PASS
讓閘道器重新上線
  等待 server 判定閘道器上線     預期 上線 / 實際 上線 / PASS
驗證 server log 的 config 下發指令
  驗證 server log 出現的 config 下發指令   預期 [push, sendkey, wsync] / 實際 [push, sendkey, wsync] / PASS
驗證 config.json 的 gateway_uuid
  驗證閘道器本機 config.json 的 gateway_uuid 有值   預期 不等於 '' / 實際 2a93b0c9-… / PASS
```
