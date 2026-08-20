import os

from libs.adb_utils import run

# 這台硬體 (Yocto/QTI Linux) 沒有內建 sendevent, 是額外放進 /data/ 的自訂工具,
# 而 /data/sendevent 不會存活過重開機 (關聯流程本身就會讓裝置重開), 所以每次要
# 用之前都確認一下, 不在就從專案內的副本重新推上去。
_SENDEVENT_ON_DEVICE = "/data/sendevent"
_SENDEVENT_LOCAL = os.path.join(os.getcwd(), "apk", "sendevent")


def _ensure_adb_root(serial: str | None) -> None:
    """切換成 root 後這台硬體實測會斷線約 5-8 秒才重新連上 (比一般手機慢很多),
    所以另外用 wait-for-device 等它真的連回來, 避免下一行指令撲空.
    """
    root_code = f"adb -s {serial} root" if serial else "adb root"
    run(root_code)

    wait_code = f"adb -s {serial} wait-for-device" if serial else "adb wait-for-device"
    run(wait_code, timeout=30)


def set_bluetooth_enabled(serial: str | None, enabled: bool) -> None:
    _ensure_adb_root(serial)
    action = "unblock" if enabled else "block"
    adb_code = (
        f"adb -s {serial} shell rfkill {action} bluetooth"
        if serial
        else f"adb shell rfkill {action} bluetooth"
    )
    run(adb_code)


def set_wifi_enabled(serial: str | None, enabled: bool) -> None:
    _ensure_adb_root(serial)
    action = "unblock" if enabled else "block"
    adb_code = (
        f"adb -s {serial} shell rfkill {action} wlan"
        if serial
        else f"adb shell rfkill {action} wlan"
    )
    run(adb_code)


def _ensure_sendevent_binary(serial: str | None) -> None:
    """確保裝置上有 /data/sendevent, 不在就從專案的 apk/sendevent 推上去並給執行權限."""
    check_code = (
        f'adb -s {serial} shell "test -x {_SENDEVENT_ON_DEVICE}"'
        if serial
        else f'adb shell "test -x {_SENDEVENT_ON_DEVICE}"'
    )
    if run(check_code, check=False).returncode == 0:
        return

    if not os.path.exists(_SENDEVENT_LOCAL):
        raise FileNotFoundError(
            f"裝置上沒有 {_SENDEVENT_ON_DEVICE}, 專案內也找不到可推送的副本 "
            f"({_SENDEVENT_LOCAL})"
        )

    push_code = (
        f"adb -s {serial} push {_SENDEVENT_LOCAL} {_SENDEVENT_ON_DEVICE}"
        if serial
        else f"adb push {_SENDEVENT_LOCAL} {_SENDEVENT_ON_DEVICE}"
    )
    run(push_code)

    chmod_code = (
        f"adb -s {serial} shell chmod +x {_SENDEVENT_ON_DEVICE}"
        if serial
        else f"adb shell chmod +x {_SENDEVENT_ON_DEVICE}"
    )
    run(chmod_code)


def press_wifi_association_button(serial: str | None) -> None:
    """模擬按下 Athena 硬體上的 Wi-Fi 關聯實體按鈕 (keycode 158).

    透過 /data/sendevent 對 /dev/input/event1 送出一組完整的按下/放開事件
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
        "sleep 0.1; "
        f"{_SENDEVENT_ON_DEVICE} /dev/input/event1 1 158 0; "
        f"{_SENDEVENT_ON_DEVICE} /dev/input/event1 0 0 0"
    )
    adb_code = (
        f'adb -s {serial} shell "{sendevent_code}"'
        if serial
        else f'adb shell "{sendevent_code}"'
    )
    run(adb_code)


def set_reboot(serial: str | None = None) -> None:
    adb_code = f"adb -s {serial} reboot" if serial else "adb reboot"
    run(adb_code)
