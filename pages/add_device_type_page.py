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

    # 「進階裝置」是收合的分類, 裡面的 Modbus/藍牙裝置預設不在畫面上, 要先點這
    # 一整行展開才會出現。實測 dump 確認 id/title 本身 clickable=false, 是外層
    # 可點擊 ViewGroup 的子節點 (跟 typeModelName/select_device_type() 是同一種
    # 結構), 直接點文字節點座標即可, 觸控事件會冒泡到外層容器觸發展開。
    #
    # 這個分類在畫面最下面 (閘道器/感測器與家電之後), 剛進畫面時還沒捲到那裡,
    # 元件根本不在 accessibility tree 裡 (不是單純「看不到」), 直接找會
    # NoSuchElementError; 用 UiScrollable.scrollIntoView() 包起來, 讓
    # UiAutomator2 自己把畫面捲到該元件出現為止, 不用寫死座標去滑動。
    _ADVANCED_DEVICES_ROW = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiScrollable(new UiSelector().scrollable(true)).scrollIntoView('
        f'new UiSelector().resourceId("{_PACKAGE}:id/title").text("進階裝置"))',
    )

    def _device_type_locator(self, device_type: str) -> tuple:
        return (
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiScrollable(new UiSelector().scrollable(true)).scrollIntoView('
            f'new UiSelector().resourceId("{_PACKAGE}:id/typeModelName")'
            f'.text("{device_type}"))',
        )

    def select_device_type(self, device_type: str) -> None:
        self._tap(self._device_type_locator(device_type))

    def tap_advanced_devices(self, timeout: int = 10) -> None:
        """展開「進階裝置」分類 (Modbus/藍牙裝置藏在裡面, 預設收合)."""
        self._tap(self._ADVANCED_DEVICES_ROW, timeout)
