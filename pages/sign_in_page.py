"""ecogenie App 登入畫面 (SignInActivity) 的 Page Object."""

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException

from pages.base_page import BasePage

_PACKAGE = "io.nextdrive.ecogenie.stg"


class SignInPage(BasePage):
    _ALREADY_HAVE_ACCOUNT_BUTTON = (AppiumBy.ID, f"{_PACKAGE}:id/signin_button")
    _SIGN_UP_BUTTON = (AppiumBy.ID, f"{_PACKAGE}:id/signup_button")
    _ONBOARDING_TURN_ON_BUTTON = (AppiumBy.ID, f"{_PACKAGE}:id/requestPermit")
    _EMAIL_INPUT = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        f'new UiSelector().resourceId("{_PACKAGE}:id/username")'
        '.childSelector(new UiSelector().className("android.widget.EditText"))',
    )
    _PASSWORD_INPUT = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        f'new UiSelector().resourceId("{_PACKAGE}:id/password")'
        '.childSelector(new UiSelector().className("android.widget.EditText"))',
    )
    _SIGN_IN_BUTTON = (AppiumBy.ID, f"{_PACKAGE}:id/signIn")

    def skip_onboarding_if_shown(self, max_swipes: int = 3) -> None:
        """首次安裝後啟動 App 會先跳出 3 頁 onboarding 輪播 (無 Skip 按鈕),
        最後一頁才有 Turn On 按鈕. 若已經跳過 onboarding (入口畫面的
        Already Have an Account 或 Sign Up 任一顆按鈕已經顯示) 則直接
        return, 不當成錯誤, 也不用再滑三次.
        """
        if self._is_present(self._ALREADY_HAVE_ACCOUNT_BUTTON) or self._is_present(
            self._SIGN_UP_BUTTON
        ):
            return

        for _ in range(max_swipes):
            if self._is_present(self._ONBOARDING_TURN_ON_BUTTON):
                self._tap(self._ONBOARDING_TURN_ON_BUTTON)
                self.dismiss_error_dialog_if_shown()
                return
            self._swipe_left()

    def _is_present(self, locator: tuple, timeout: int = 2) -> bool:
        try:
            self._wait_visible(locator, timeout)
            return True
        except TimeoutException:
            return False

    def _swipe_left(self) -> None:
        """輪播往下一頁: 用視窗寬高的相對比例算座標, 不寫死絕對像素,
        避免不同模擬器/裝置解析度不同時滑動位置對不上.
        """
        size = self.driver.get_window_size()
        start_x = int(size["width"] * 0.8)
        end_x = int(size["width"] * 0.2)
        y = int(size["height"] * 0.5)
        self.driver.swipe(start_x, y, end_x, y, 200)

    def tap_already_have_account(self, timeout: int = 5) -> None:
        """SignInActivity 一進入是入口畫面 (Already Have an Account / Sign Up),
        要先點這裡才會進到 email/password 表單. 若已經在表單頁 (略過入口畫面
        的情境) 就直接跳過, 不視為錯誤.
        """
        try:
            self._tap(self._ALREADY_HAVE_ACCOUNT_BUTTON, timeout)
        except TimeoutException:
            pass

    def input_email(self, email: str) -> None:
        self._input_text(self._EMAIL_INPUT, email)

    def input_password(self, password: str) -> None:
        self._input_text(self._PASSWORD_INPUT, password)

    def tap_sign_in(self) -> None:
        self._tap(self._SIGN_IN_BUTTON)

    def sign_in(self, email: str, password: str, timeout: int = 20) -> None:
        self.skip_onboarding_if_shown()
        self.tap_already_have_account()
        self.input_email(email)
        self.input_password(password)
        self.tap_sign_in()
        # 登入成功後畫面會離開 SignInActivity, 用 email 輸入框消失確認轉場完成
        self._wait_hidden(self._EMAIL_INPUT, timeout)
        # 登入成功後首次會跳出「Biometric Login is Available」提示 (問要不要開
        # 生物辨識登入), 用的是跟 arch_component_dialog_* 一樣的通用元件 (按鈕
        # 文字是「確定」不是英文 "OK", 之前寫死英文 "OK" 一直沒真的關到這個彈窗),
        # 之後登入不會再出現, 沒出現時不視為錯誤.
        self.dismiss_error_dialog_if_shown()
