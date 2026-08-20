"""Android 模擬機 (Emulator) Appium Desired Capabilities.

啟動前請先在 Android Studio (AVD Manager) 建立好對應的模擬機,
並用 `emulator -list-avds` 確認 `appium:avd` / `appium:deviceName` 是否一致.

APK 放在專案的 `apk/` 目錄下 (已加入 .gitignore, 不會被提交進版控),
執行測試時會依 `appium:app` 指定的路徑自動安裝/更新到模擬機上.
"""

import os

_PROJECT_ROOT = os.getcwd()
_APK_PATH = os.path.join(
    _PROJECT_ROOT, "apk", "ecogenie_staging_v1.5.2003.apk"
)

capabilities = {
    "platformName": "Android",
    "appium:automationName": "UiAutomator2",

    "appium:deviceName": "Pixel_10_Pro_XL",
    "appium:avd": "Pixel_10_Pro_XL",

    "appium:platformVersion": "17",

    "appium:app": _APK_PATH,

    "appium:noReset": False,
    "appium:autoGrantPermissions": True,
    "appium:newCommandTimeout": 120,
}
