# UI 層規範（Page/Screen Object + 定位器 + 多語系文案）

## 定位器優先序
Accessibility ID（iOS `accessibility id` / Android `content-desc`，對應 `AppiumBy.ACCESSIBILITY_ID`）> Android `resource-id`（`AppiumBy.ID`，即 `new UiSelector().resourceId()`）> iOS Predicate String（`AppiumBy.IOS_PREDICATE`）> User-facing 屬性（`text`/`label` 部分比對，如 Android `AppiumBy.ANDROID_UIAUTOMATOR` 的 `.textContains()`）。

**絕對禁止**：
1. 使用絕對座標點擊（x/y coordinate tap）——不同機型、解析度下完全不可靠。
2. 使用索引式 XPath（如 `//android.widget.Button[3]`）——畫面結構稍有變動即失效，效能也差。

## 斷言風格
必須透過 `libs/assert_utils.py` 封裝好的輪詢斷言函式（`assert_visible`、`assert_hidden`、`assert_text`、`assert_attribute` 等），底層以 Selenium `WebDriverWait` + `expected_conditions` 實作。禁止在 flow 層直接寫裸的 `driver.find_element(...)` 後接 `assert`。`assert_text` 比對的是完全一致的文字；`assert_visible` / `assert_hidden` 要傳 `target=` 說明目標。報告呈現與斷言命名規則見 `flow-layer.md`。

## Page/Screen Object 慣例
1. `pages/` 只暴露 locator（`@property`，型別為 `(AppiumBy, value)` tuple）與操作（`open_*`、`tap_*`、`input_*`），繼承 `pages/base_page.py` 的 `BasePage`。
2. 禁止在 `pages/` 內呼叫 `assert_*`、`verify_*`。
3. 禁止在 `pages/` 內呼叫 API 或組裝業務預期值。
4. 若 Android／iOS 定位器不同，一律在 Page/Screen Object 內以平台分流（例如依 `self.driver.capabilities["platformName"]` 挑選對應 locator），禁止把平台判斷邏輯外洩到 flow 層。

## 頁面文字（Wording）多語系規範
所有頁面文字必須提取至模組對應的 `_variables.py`，且一律支援 **zh-TW / en / ja** 三語系，不可寫死單一語言字串。

標準作法（參考 `devices_variables.py`）：
1. 建立 `_WORDING = {"文案常數名稱": {"zh-TW": ..., "en": ..., "ja": ...}}`，key 為文案常數名稱、value 為三語系譯文組成的 dict（key 在外層、語言在內層，不是語言在外層）。
2. 依 `config.services.accept_language`（找不到則 fallback 到 `_DEFAULT_SITE_LANGUAGE = "zh-TW"`）決定要取哪個語言。
3. 模組的 Variables class 屬性一律從 `_WORDING["KEY"][language]` 取值，例如：
   ```python
   CUMULATIVE_GRID_SUPPLY_TITLE = _WORDING["CUMULATIVE_GRID_SUPPLY_TITLE"][_language]
   ```
4. 僅與語言無關的固定值（數字門檻、API property 名稱等）可直接寫成類別屬性常數，不需要進 `_WORDING`。
5. 若某語言尚未實機驗證過文案，暫時沿用已驗證語言的文案佔位，並在檔案開頭註明哪個語言尚待確認，不可憑空猜測翻譯。
