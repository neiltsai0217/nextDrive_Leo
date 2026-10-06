import json
import os
import time

import allure

from libs.adb_utils import adb_execute, adb_execute_raw

# 這台硬體 (Yocto/QTI Linux) 沒有內建 sendevent, 是額外放進 /data/ 的自訂工具,
# 而 /data/sendevent 不會存活過重開機 (關聯流程本身就會讓裝置重開), 所以每次要
# 用之前都確認一下, 不在就從專案內的副本重新推上去。
_SENDEVENT_ON_DEVICE = "/data/sendevent"
_SENDEVENT_LOCAL = os.path.join(os.getcwd(), "apk", "sendevent")


@allure.step("切換 adb root 並等待裝置穩定連線")
def _ensure_adb_root(serial: str | None) -> None:
    """切換成 root 後這台硬體實測會斷線約 5-8 秒才重新連上 (比一般手機慢很多),
    所以另外用 wait-for-device 等它真的連回來, 避免下一行指令撲空.
    """
    adb_execute_raw("root", serial)
    adb_execute_raw("wait-for-device", serial, timeout=30)


@allure.step("設定藍牙開關")
def set_bluetooth_enabled(serial: str | None, enabled: bool) -> None:
    _ensure_adb_root(serial)
    action = "unblock" if enabled else "block"
    adb_execute(f"rfkill {action} bluetooth", serial)


@allure.step("設定 WiFi 開關")
def set_wifi_enabled(serial: str | None, enabled: bool) -> None:
    _ensure_adb_root(serial)
    action = "unblock" if enabled else "block"
    adb_execute(f"rfkill {action} wlan", serial)


@allure.step("確認裝置上有 sendevent 執行檔")
def _ensure_sendevent_binary(serial: str | None) -> None:
    """確保裝置上有 /data/sendevent, 不在就從專案的 apk/sendevent 推上去並給執行權限."""
    if adb_execute(f"test -x {_SENDEVENT_ON_DEVICE}", serial, check=False).returncode == 0:
        return

    if not os.path.exists(_SENDEVENT_LOCAL):
        raise FileNotFoundError(
            f"裝置上沒有 {_SENDEVENT_ON_DEVICE}, 專案內也找不到可推送的副本 "
            f"({_SENDEVENT_LOCAL})"
        )

    adb_execute_raw(f"push {_SENDEVENT_LOCAL} {_SENDEVENT_ON_DEVICE}", serial)
    adb_execute(f"chmod +x {_SENDEVENT_ON_DEVICE}", serial)


def _press_button(serial: str | None, hold_seconds: float) -> None:
    """對 Athena 硬體上唯一一顆實體按鈕 (keycode 158) 模擬按下/放開, 按住
    hold_seconds 秒。

    透過 /data/sendevent 對 /dev/input/event1 送出完整的按下/放開事件
    (EV_KEY down -> EV_SYN -> sleep -> EV_KEY up -> EV_SYN), 而非 Android 的
    input keyevent, 是因為此硬體上該按鍵沒有對應到標準 Android key event.
    直接開 /dev/input/event1 需要 root 權限 (實測確認 non-root 會
    Permission denied), 所以跟 set_bluetooth_enabled/set_wifi_enabled 一樣
    先 _ensure_adb_root。
    """
    _ensure_adb_root(serial)
    _ensure_sendevent_binary(serial)
    sendevent_code = (
        f"{_SENDEVENT_ON_DEVICE} /dev/input/event1 1 158 1; "
        f"{_SENDEVENT_ON_DEVICE} /dev/input/event1 0 0 0; "
        f"sleep {hold_seconds}; "
        f"{_SENDEVENT_ON_DEVICE} /dev/input/event1 1 158 0; "
        f"{_SENDEVENT_ON_DEVICE} /dev/input/event1 0 0 0"
    )
    adb_execute(sendevent_code, serial)


@allure.step("按下 Wi-Fi 關聯實體按鈕")
def press_wifi_association_button(serial: str | None) -> None:
    """短按 Athena 硬體上的實體按鈕, 觸發 Wi-Fi 關聯/藍牙配對模式."""
    _press_button(serial, hold_seconds=0.1)


@allure.step("長按實體按鈕觸發 factory reset")
def press_reset_button(serial: str | None) -> None:
    """長按同一顆實體按鈕觸發 factory reset (跟 press_wifi_association_button
    是同一顆鍵, 差別只在按住的秒數).

    實測 (用 gndctrl 的 log "Start to reset User Data" 判斷) 確認韌體內部
    門檻是按下後固定約 8.01 秒觸發, 不是等放開才判斷; 量測過 7/8 秒都不會
    觸發, 9/15/20 秒都會觸發。這裡抓 9 秒, 在門檻之上留一點緩衝, 同時把
    無謂等待時間降到最低。

    這是真的會清空裝置本機資料 (含 WiFi/關聯設定) 的操作: 裝置不會自動
    重新連回原本的網路, 之後必須重新走一次完整的實體配對流程才能恢復
    (見 DevicesFlow.connect_device() 對「閘道器已經關聯」情境的處理)。

    觸發後裝置會真的重開機, 呼叫端必須先呼叫 wait_for_device_online() 等
    它穩定連線, 才能繼續下任何 adb 指令 (實測確認過: 重開機還沒完成就接著
    下指令, `adb root` 會直接失敗)。
    """
    _press_button(serial, hold_seconds=9)


def wait_for_device_online(
    serial: str | None, timeout: int = 60, poll_interval: int = 3, stable_checks: int = 2
) -> None:
    """reboot 後等待裝置真正穩定連線, 不是只等 `wait-for-device` 成功一次.

    實測發現: 這台硬體 reboot 後, adb 連線會有一段閃斷/不穩定期 ——
    `adb wait-for-device` 成功一次之後, 緊接著下一個指令仍可能因為連線又
    斷掉而失敗。所以改用實際指令 (`echo ok`) 輪詢, 且要「連續 stable_checks
    次成功」才視為真正穩定, 避免剛好在閃斷的空窗期誤判成已經上線。

    timeout 預設拉到 60 秒 (比一般 reboot 更長), 因為 factory reset 除了
    重開機, 還要清空/重建使用者資料分割區, 實測比純軟體 reboot 花更久。
    """
    elapsed = 0
    consecutive_success = 0
    while elapsed < timeout:
        result = adb_execute("echo ok", serial, check=False)
        consecutive_success = consecutive_success + 1 if result.returncode == 0 else 0
        if consecutive_success >= stable_checks:
            return
        time.sleep(poll_interval)
        elapsed += poll_interval
    raise TimeoutError(f"等待 {timeout} 秒, 裝置仍未穩定連線 (adb 連線持續閃斷)")


def _get_uptime_seconds(serial: str | None) -> int | None:
    """讀裝置開機至今的秒數;adb 連不上(例如正在重開機)時回傳 None."""
    result = adb_execute("cut -d. -f1 /proc/uptime", serial, check=False)
    output = result.stdout.strip()
    return int(output) if result.returncode == 0 and output.isdigit() else None


@allure.step("等待裝置因解除關聯而重開機完成")
def wait_for_device_reboot(
    serial: str | None, detect_timeout: int = 40, poll_interval: int = 2
) -> bool:
    """
    等線上的裝置在解除關聯後重開機完成,回傳是否真的偵測到重開機.

    以開機秒數變小(或 adb 斷線)判斷:wait_for_device_online() 只確認「現在連得上」,
    在重開機開始前呼叫會直接通過(實測解除關聯後約 13 秒內才重開).
    裝置離線時收不到通知、不會重開機,detect_timeout 內沒偵測到就回傳 False,不視為錯誤.
    """
    uptime_before = _get_uptime_seconds(serial)
    elapsed = 0
    while elapsed < detect_timeout:
        uptime_now = _get_uptime_seconds(serial)
        if uptime_now is None or (uptime_before is not None and uptime_now < uptime_before):
            wait_for_device_online(serial, timeout=120)
            return True
        time.sleep(poll_interval)
        elapsed += poll_interval
    return False


@allure.step("切換 WiFi 連線開關(wpa_supplicant 層級,保留已儲存的網路設定)")
def set_wifi_network_enabled(serial: str | None, enabled: bool) -> None:
    """
    用 /etc/wifi.env 的 wifi on / off 啟用或停用已儲存網路的連線.

    跟 set_wifi_enabled() 的 rfkill 不同層級:rfkill 斷網不會觸發 server 的離線偵測,
    這裡的 wifi off 會(實測 108～128 秒),而且不動已儲存的 WiFi / 關聯設定,
    wifi on 之後裝置會自己連回去.
    """
    _ensure_adb_root(serial)
    action = "on" if enabled else "off"
    adb_execute(f"source /etc/wifi.env; wifi {action}", serial)


@allure.step("讓裝置直接連上 WiFi")
def connect_wifi(serial: str | None, ssid: str, password: str) -> None:
    """
    對裝置下 adb 指令直接連上 WiFi,不走 App 的 WiFi 選擇畫面;已連上時重複呼叫是安全的.

    密碼不寫進 log 與 Allure 報告.
    """
    _ensure_adb_root(serial)
    adb_execute(
        f'source /etc/wifi.env; wifi connect "{ssid}" "{password}"',
        serial,
        log_as=f'source /etc/wifi.env; wifi connect "{ssid}" "***"',
    )


@allure.step("讀取裝置 device_pid")
def get_gateway_pid(serial: str | None) -> str:
    result = adb_execute("getprop persist.device_pid", serial)
    return result.stdout.strip()


@allure.step("讀取 gateway 本機 config.json")
def get_config_json(serial: str | None) -> dict:
    """
        讀取 gateway 上 /data/cfg_mgmt/config.json 的內容並解析成 dict.
    """
    _ensure_adb_root(serial)
    result = adb_execute("cat /data/cfg_mgmt/config.json", serial)
    return json.loads(result.stdout)

