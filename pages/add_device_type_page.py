"""ecogenie App「Add Device」裝置類型選擇畫面的 Page Object."""

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

_PACKAGE = "io.nextdrive.ecogenie.stg"


class AddDeviceTypePage(BasePage):
    # 「新增設備」畫面左上角的返回鍵: 是 Material toolbar 的 navigation-up 按鈕,
    # 沒有 resource-id, 只能用 content-desc 定位 (實測 dump 確認為「向上瀏覽」)
    _BACK_BUTTON = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        f'new UiSelector().packageName("{_PACKAGE}")'
        '.className("android.widget.ImageButton").description("向上瀏覽")',
    )

    def tap_back(self, timeout: int = 10) -> None:
        """按左上角返回, 從「新增設備」回到裝置分頁."""
        self._tap(self._BACK_BUTTON, timeout)

    def _device_type_locator(self, device_type: str) -> tuple:
        return (
            AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiSelector().resourceId("{_PACKAGE}:id/typeModelName")'
            f'.text("{device_type}")',
        )

    def select_device_type(self, device_type: str) -> None:
        self._tap(self._device_type_locator(device_type))
