# nextDrive_Leo

## 環境設置

### 1. Python 依賴（App / API 測試）

```bash
pip install -r requirements.txt
```

### 2. Appium Server（iOS / Android 原生 App 測試）

`requirements.txt` 只包含 Appium 的 Python client，實際執行測試還需要安裝 Appium Server 與對應平台 driver：

```bash
npm install -g appium
appium driver install uiautomator2   # Android
appium driver install xcuitest       # iOS
```

啟動 Appium Server：

```bash
appium
```

平台額外需求：
- **Android**：安裝 Android SDK（`ANDROID_HOME` 環境變數）、`adb` 可用
- **iOS**：macOS + Xcode + `xcrun simctl`，需安裝 [WebDriverAgent](https://github.com/appium/WebDriverAgent) 相關憑證（實機測試）

## 執行測試

```bash
pytest --alluredir=./allure-results
```

## 查看報告

```bash
allure serve ./allure-results
```




# 參考 Test case: https://oakiwitcms.nextdrive.io/runs/7503/