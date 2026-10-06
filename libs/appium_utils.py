"""Appium driver 相關的共用基礎設施 (跟具體業務無關)."""


def keep_appium_session_alive(driver) -> None:
    """對 driver 送一個無害的輕量指令 (讀視窗大小), 重置 newCommandTimeout 的
    閒置計時。

    長時間的純後端/adb 等待 (完全不碰 Appium driver) 一旦累積超過
    capabilities 設的 newCommandTimeout, Appium 會自己把 session 收掉,
    而且不會馬上報錯, 是等到後面真的要操作 UI 時才爆炸, 很難對應回真正的
    成因, 所以這種等待期間要定期呼叫這個方法。
    """
    driver.get_window_size()
