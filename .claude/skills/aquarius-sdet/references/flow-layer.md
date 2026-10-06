# Flow 層規範

## 定位
`testsuites/<product>/<module>/<module>_flow.py` 負責操作編排與斷言。資料準備、API 解析、輪詢等待放同模組的 `<module>_suites.py`。

## 結構：一步一 Function
- Test Case 的每個 Step 對應一個公開方法，並加上 `@allure.step("<Step 文字>")`，文字與 test 行尾註解一致（不含 a/b/c 編號，避免重用時編號錯亂）。
- 方法命名：
  - 操作：`connect_device()`、`disconnect_modbus_device()`、`take_gateway_offline()`
  - 驗證：`verify_<對象>()`，**一個方法只驗證一個對象的一個面向**（server log 指令、`config.json` 有內容、`gateway_uuid` 分開成三個方法）
- 預期值與操作開始時間以**參數 / 回傳值傳遞**，不存在 `self`：操作方法回傳 `started_at`，由 test 傳給 `verify_*(started_at)`。step 之間不得有「必須先呼叫 A 才能呼叫 B」的隱性相依。
- 私有 helper（`_xxx`）不加 `@allure.step`，避免報告出現多餘巢狀步驟。

## 範例
```python
class DevicesFlow:
    """裝置分頁的閘道器 / 子裝置關聯操作,以及關聯變動後的 config 下發驗證."""

    @allure.step("解除關聯 Modbus 子裝置")
    def disconnect_modbus_device(self, device_name: str) -> str:
        """裝置分頁 →「進階裝置」→ 該裝置的「設定」→「移除」→ 確認;回傳操作開始時間."""
        started_at = get_utc_iso_now()
        self._home_page.tap_device_tab()
        ...
        return started_at

    @allure.step("驗證 server log 的 config 下發指令")
    def verify_server_config_dispatch(self, started_at: str) -> None:
        profile_id = get_gateway_profile_id(self._target_device_serial)
        command_types = get_config_dispatch_command_types(profile_id, started_at)
        assert_equal(
            command_types,
            EXPECTED_COMMAND_TYPES,
            "驗證 server log 出現的 config 下發指令",
            context={"gateway_profile_id": profile_id, "查詢起始時間(UTC)": started_at},
        )
```

## 斷言
- 一律使用 `libs/assert_utils.py`（`assert_visible`、`assert_hidden`、`assert_text`、`assert_attribute`、`assert_equal`、`assert_not_equal`、`assert_greater_than`）。每個斷言會自動附一份「驗證結果」，通過與失敗都有：
  ```json
  {"預期": ["push", "sendkey", "wsync"], "實際": ["push", "sendkey", "wsync"], "Verify": "PASS"}
  ```
- **報告可讀性規則**：
  - 把「預期」與「實際」直接交給斷言比對，不要先自己算出差集或布林值再比（例如比對 `command_types == EXPECTED_COMMAND_TYPES`，不要比對 `missing == set()`），報告才看得出應該是什麼、實際是什麼。
  - 使用 `assert_visible` / `assert_hidden` 時一律傳 `target="<目標名稱>"`，報告「預期」會顯示「顯示「目標」」，不可只寫「顯示」。
  - 能比對文字就用 `assert_text`（完全一致），不要用 `assert_visible`。
  - 「有值就好」用 `assert_not_equal(actual, "", ...)`；「至少一筆」用 `assert_greater_than(count, 0, ...)`。
  - `context` 只放補充說明（例如查詢的 profile_id、等待上限），會顯示在「補充資訊」；不要把預期值塞進 `context`。
  - 斷言名稱（第 3 個參數）描述驗證對象，以「驗證」開頭，例如「驗證閘道器本機 config.json 的 gateway_uuid 有值」。
  - 不要用 `log()` 另外附預期 / 實際值，「驗證結果」已經有了。
- 每個 `verify_*` 至少一個斷言。

## 錯誤表示
- flow 不得 `raise RuntimeError` / `TimeoutError`。等待逾時、前提不成立一律用斷言表示，報告才看得到預期與實際：
  - 等待狀態：suites 回傳最後查到的狀態，flow 用 `assert_equal(實際狀態, 預期狀態, "等待 server 判定閘道器離線", context={"等待上限(秒)": timeout})`。
  - 前提檢查：斷言名稱以「確認」開頭並寫明不成立時代表什麼，例如「確認已關聯的閘道器對得到 DSN(對不到代表帳號關聯的不是這台待測閘道器,需人工處理)」。
- 斷言名稱的開頭決定失敗分類（`allure-config/categories.json`）：「驗證 server log…」「驗證閘道器本機 config.json…」歸產品缺陷，「等待…」「確認…」歸前置狀態未就緒。新增斷言時沿用這些開頭，或同步補上分類規則。
- suites 找不到資料時 `raise AssertionError("<中文說明>")`；`libs/`、`testsuites/common/` 的底層工具維持原生例外。

## 註解
- 只寫「為什麼」，不寫「做了什麼」，也不寫實測過程的流水帳；實測得到的結論濃縮成一句（例如「server 判定離線實測要 108～128 秒」）。
- docstring 一行為原則，句尾用 `.`；需要補充時空一行再寫。
- 與程式不符或過期的註解要一併更新或刪除。

## 禁止事項
1. 禁止在 flow 內撰寫 locator 字串（透過 Page Object 取得）。
2. 禁止在 flow 內拼寫 HTTP request、解析 API 回應、做時間區間組裝（放 suites / API wrapper）。
3. 禁止一個 step 方法驗證多個不相關對象。
4. 禁止 `time.sleep` 與輪詢迴圈（放 suites，flow 只對結果做斷言）。
