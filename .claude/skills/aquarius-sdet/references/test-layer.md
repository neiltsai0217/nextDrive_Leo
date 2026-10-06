# Test 層規範

## 定位
`test_<module>.py` 是 Test Case 的可執行版本：只描述「測什麼、依什麼順序」，不含任何實作細節。

## 結構
- Test class 加上 `@allure.feature("<頁面>")` + `@allure.story("<主題>")`。
- 一個 Test Case 一個 test function：`@allure.title("TC-<Kiwi 編號>: <Kiwi 標題>")`。
- test function 依 Test Case Step 順序逐行呼叫 Flow step 方法；**一行對應一個 Step**。
- 操作方法回傳的值（例如 `started_at`）由 test 接住再傳給後面的 `verify_*`。

## 標準寫法
```python
@allure.feature("裝置")
@allure.story("Config 下發")
class TestDevicePage:

    @allure.title("TC-40140: [IoEP] Gateway 解關聯後，確認 config 是否正常送下去")
    def test_04_disconnect_gateway(self, devices_flow: DevicesFlow, gateway_disassociated_around_test):
        devices_flow.associate_gateway_via_api(var.GATEWAY_NAME)                # a. 透過 API 關聯閘道器
        started_at = devices_flow.disconnect_device()                           # b. 在 App 解除關聯閘道器
        devices_flow.verify_server_config_dispatch(started_at)                  # c. 驗證 server log 的 config 下發指令
        devices_flow.verify_config_json_empty()                                 # d. 驗證 config.json 為空
```
行尾註解標示 Step 編號，文字與 Flow 的 `@allure.step` 一致，方便人工比對。

## 空行格式（優先於 PEP 8）
- class（含 `@allure.feature` / `@allure.story` decorator）之前空 **3 行**。
- 同一 class 內，test 與 test 之間空 **2 行**；class 標頭與第一個 test 之間空 1 行。

## 前置與收尾
- 每個 case 用 fixture 各自建立 / 清除狀態，不依賴前一個 case 留下的狀態。
- fixture 的 docstring 說明「為什麼需要這個前置 / 收尾」，不重述它呼叫了什麼。

## 流水號命名規則
1. 測試函式名稱必須使用兩位數流水號：`test_01_*`、`test_02_*`、`test_03_*`。
2. 流水號依**同一 class 內**的案例執行順序排列，不可重複；同一檔案內不同 class 各自獨立起算。
3. 編號只加在 test 函式名稱；Flow 方法不得加入案例編號。

## 禁止事項
1. 禁止在 test 內撰寫 API 呼叫、資料轉換、時間區間組裝、讀取環境設定。
2. 禁止在 test 內撰寫 locator、斷言、`with allure.step(...)`（step 由 Flow 方法提供）。
3. 禁止在 test 之間透過 class 屬性或全域變數共享資料。
