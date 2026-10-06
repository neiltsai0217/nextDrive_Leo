"""Android 實體手機 (Real Device) Appium Desired Capabilities.

手機需先用 USB 或 `adb tcpip` 切成無線 adb 連上, 用 `adb devices` 確認下面的
appium:udid 是否為目前這台手機的 serial (`adb devices` 第一欄).

APK 放在專案的 `apk/` 目錄下 (已加入 .gitignore, 不會被提交進版控),
執行測試時會依 `appium:app` 指定的路徑自動安裝/更新到手機上.
"""

import os

_PROJECT_ROOT = os.getcwd()
_APK_PATH = os.path.join(
    _PROJECT_ROOT, "apk", "ecogenie_staging_v1.5.2003.apk"
)

capabilities = {
    "platformName": "Android",
    "appium:automationName": "UiAutomator2",

    "appium:deviceName": "Pixel 8a",
    "appium:udid": "192.168.8.125:5555",

    "appium:platformVersion": "16",

    "appium:app": _APK_PATH,

    "appium:noReset": False,
    "appium:autoGrantPermissions": True,
    "appium:newCommandTimeout": 120,
}
