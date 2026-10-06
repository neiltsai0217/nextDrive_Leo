# Suites 層規範

## 定位
`testsuites/<product>/<module>/<module>_suites.py` 負責該模組的資料準備與預期值組裝（非 flow 編排）。

## 職責
1. dataclass 預期值結構、`build_*_expected()` 組裝函式。
2. API / DB / adb 回應的解析與格式化（例如從 `config.json` 取出 `gateway_uuid`、找出符合的 modbus.rtu 項目）。
3. 輪詢等待：`wait_for_*()` 輪詢到條件成立或逾時，**回傳最後一次查到的結果**，不自己判定成敗，由 flow 用斷言比對。
4. 取出要比對的欄位時轉成跟預期值相同的型別與結構，報告的「實際」才能跟「預期」逐欄對照。

## 範例
```python
def wait_for_gateway_online_status(expect_online: bool, timeout: int, on_poll=None) -> bool:
    """輪詢到 server 判定的上線狀態符合預期或逾時,回傳最後一次查到的狀態."""
    elapsed = 0
    is_online = is_gateway_online()
    while is_online != expect_online and elapsed < timeout:
        if on_poll:
            on_poll()
        time.sleep(_POLL_INTERVAL_SECONDS)
        elapsed += _POLL_INTERVAL_SECONDS
        is_online = is_gateway_online()
    return is_online
```

## 禁止事項
1. 禁止在 suites 內呼叫 `assert_*`、操作 Page。
2. 禁止在 suites 內拼寫 HTTP request（應透過 `testsuites/common/` API wrapper）。
3. 輪詢間隔、逾時等常數要有名稱，並用一行註解說明數值的依據。
