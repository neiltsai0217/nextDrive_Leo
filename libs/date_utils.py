from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from libs.config_utils import config

_DEFAULT_TZ = "Asia/Taipei"
_DEFAULT_LANGUAGE = "zh-TW"

_YESTERDAY_LABEL_PREFIX = {
    "zh-TW": "前一日",
    "en": "Yesterday",
    "ja": "前日",
}

_LAST_WEEK_LABEL_CONFIG = {
    "zh-TW": {"prefix": "上週", "weekdays": ["一", "二", "三", "四", "五", "六", "日"], "joiner": "", "suffix": ""},
    "en": {"prefix": "Last", "weekdays": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], "joiner": " ", "suffix": ""},
    "ja": {"prefix": "前週", "weekdays": ["月", "火", "水", "木", "金", "土", "日"], "joiner": "", "suffix": "曜日"},
}

_LAST_MONTH_LABEL_PREFIX = {
    "zh-TW": "上個月",
    # 實測確認(en 語系測試失敗訊息的 aria snapshot):en 站台實際顯示小寫的
    # 「Last month」,並非原先假設的「Last Month」.
    "en": "Last month",
    "ja": "前月",
}

_SAME_MONTH_LAST_YEAR_LABEL_PREFIX = {
    "zh-TW": "去年同月",
    # 實測確認(en 語系測試失敗訊息的 aria snapshot):en 站台實際顯示「Same month」,
    # 與去年同時段(_LAST_YEAR_LABEL_PREFIX)的「Same period」不同命名,不可比照套用.
    "en": "Same month",
    "ja": "昨年同月",
}

_LAST_YEAR_LABEL_PREFIX = {
    "zh-TW": "去年同時段",
    # 實測確認(en 語系測試失敗訊息的 aria snapshot):en 站台實際顯示
    # 「Same period 2025」,並非原先假設的「Last Year 2025」.
    "en": "Same period",
    "ja": "昨年同時期",
}


def _resolve_language(lang: str | None) -> str:
    if lang:
        return lang
    return config.services.accept_language


def _to_utc_iso(dt: datetime) -> str:
    """將 aware datetime 轉成 UTC ISO8601 字串,例如 2026-07-13T16:00:00.000Z."""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def get_utc_iso_now() -> str:
    """取得當下時刻的 UTC ISO8601 字串,供查詢 log 系統 (例如 OpenSearch)
    的時間區間下限/上限使用."""
    return _to_utc_iso(datetime.now(timezone.utc))


def get_day_time_range(target_date: date, tz: str = _DEFAULT_TZ) -> dict:
    """取得指定日期(當地時區)的起迄時間區間."""
    local_tz = ZoneInfo(tz)
    start_local = datetime.combine(target_date, datetime.min.time(), tzinfo=local_tz)
    end_local = start_local + timedelta(days=1)

    return {
        "start": _to_utc_iso(start_local),
        "end": _to_utc_iso(end_local),
    }


def get_today_time_range(tz: str = _DEFAULT_TZ) -> dict:
    """
    取得指定時區今天的時間區間,以 UTC ISO8601 字串回傳.

    Args:
        tz: IANA 時區名稱,預設為 Asia/Taipei.例如 UTC、Asia/Tokyo、America/Los_Angeles.

    Returns:
        dict: {"start": "...", "end": "..."}
        例如 tz=Asia/Taipei 且今天為 2026-07-14 時:
        {
            "start": "2026-07-13T16:00:00.000Z",
            "end": "2026-07-14T16:00:00.000Z",
        }
    """
    today = datetime.now(ZoneInfo(tz)).date()
    return get_day_time_range(today, tz)


def get_today_date(tz: str = _DEFAULT_TZ) -> date:
    """取得指定時區的「今天」日期物件,供需要 date(而非時間區間字串)的情境使用."""
    return datetime.now(ZoneInfo(tz)).date()


def get_yesterday_date(tz: str = _DEFAULT_TZ) -> date:
    """取得指定時區的「昨天」日期物件,供需要 date(而非時間區間字串)的情境使用."""
    return datetime.now(ZoneInfo(tz)).date() - timedelta(days=1)


def get_previous_month_date(tz: str = _DEFAULT_TZ) -> date:
    """取得「上個月」的代表日期(該月第一天),供需要 date 物件的情境使用."""
    return _add_months(_first_of_month(datetime.now(ZoneInfo(tz)).date()), -1)


def get_previous_year_date(tz: str = _DEFAULT_TZ) -> date:
    """取得「去年」的代表日期(去年 1/1),供需要 date 物件的情境使用."""
    this_year = datetime.now(ZoneInfo(tz)).date().year
    return date(this_year - 1, 1, 1)


def get_yesterday_time_range(
    tz: str = _DEFAULT_TZ, reference_date: date | None = None
) -> dict:
    """
    取得指定時區、相對於 reference_date(預設今天)前一天的時間區間,以 UTC ISO8601 字串回傳.

    reference_date 讓呼叫端可算出「畫面選取日期的前一日」,而不只是「今天的前一日」
    (例如畫面切換到昨天後,前一日比較列要對齊的是前天).

    Args:
        tz: IANA 時區名稱,預設為 Asia/Taipei.
        reference_date: 作為基準的日期,預設為今天.

    Returns:
        dict: {"start": "...", "end": "..."}
        例如 tz=Asia/Taipei 且 reference_date 為 2026-07-14 時:
        {
            "start": "2026-07-12T16:00:00.000Z",
            "end": "2026-07-13T16:00:00.000Z",
        }
    """
    base = reference_date or datetime.now(ZoneInfo(tz)).date()
    yesterday = base - timedelta(days=1)
    return get_day_time_range(yesterday, tz)


def get_last_week_today_time_range(
    tz: str = _DEFAULT_TZ, reference_date: date | None = None
) -> dict:
    """
    取得指定時區、相對於 reference_date(預設今天)「上週同一天」的時間區間,以 UTC ISO8601 字串回傳.

    reference_date 讓呼叫端可算出「畫面選取日期的上週同日」,而不只是「今天的上週同日」.

    Args:
        tz: IANA 時區名稱,預設為 Asia/Taipei.
        reference_date: 作為基準的日期,預設為今天.

    Returns:
        dict: {"start": "...", "end": "..."}
        例如 tz=Asia/Taipei 且 reference_date 為 2026-07-14(週二)時,回傳上週二:
        {
            "start": "2026-07-06T16:00:00.000Z",
            "end": "2026-07-07T16:00:00.000Z",
        }
    """
    base = reference_date or datetime.now(ZoneInfo(tz)).date()
    last_week_today = base - timedelta(days=7)
    return get_day_time_range(last_week_today, tz)


def _first_of_month(target_date: date) -> date:
    return date(target_date.year, target_date.month, 1)


def _add_months(target_date: date, months: int) -> date:
    """取得指定日期所在月份往前／往後偏移 months 個月後,該月第一天的日期."""
    month_index = target_date.year * 12 + (target_date.month - 1) + months
    return date(month_index // 12, month_index % 12 + 1, 1)


def get_full_month_time_range(target_date: date, tz: str = _DEFAULT_TZ) -> dict:
    """
    取得 target_date 所在月份的完整月份時間區間.

    用於畫面月粒度下導覽至已結束(非本月)的月份時對帳:該月份已完整結束,
    主數值與比較列皆為完整整月總量,不像進行中的本月只到當下時刻／已完整經過天數
    (參見 [[get_current_month_time_range]] / [[get_last_month_until_now_time_range]]).
    """
    local_tz = ZoneInfo(tz)
    month_start = _first_of_month(target_date)
    next_month_start = _add_months(month_start, 1)
    start_local = datetime.combine(month_start, datetime.min.time(), tzinfo=local_tz)
    end_local = datetime.combine(next_month_start, datetime.min.time(), tzinfo=local_tz)

    return {
        "start": _to_utc_iso(start_local),
        "end": _to_utc_iso(end_local),
    }


def get_full_month_before_time_range(target_date: date, tz: str = _DEFAULT_TZ) -> dict:
    """取得 target_date 所在月份的「上個月」完整月份時間區間."""
    month_before = _add_months(_first_of_month(target_date), -1)
    return get_full_month_time_range(month_before, tz)


def get_full_same_month_last_year_time_range(target_date: date, tz: str = _DEFAULT_TZ) -> dict:
    """取得 target_date 所在月份的「去年同月」完整月份時間區間."""
    same_month_last_year = _add_months(_first_of_month(target_date), -12)
    return get_full_month_time_range(same_month_last_year, tz)


def get_full_year_time_range(target_date: date, tz: str = _DEFAULT_TZ) -> dict:
    """
    取得 target_date 所在年份的完整年份時間區間.

    用於畫面年粒度下導覽至已結束(非今年)的年度時對帳:該年度已完整結束,
    主數值與比較列皆為完整整年總量,不像進行中的今年只到當下時刻／已完整經過天數
    (參見 [[get_current_year_time_range]] / [[get_last_year_until_now_time_range]]).
    """
    local_tz = ZoneInfo(tz)
    year_start = date(target_date.year, 1, 1)
    year_end = date(target_date.year + 1, 1, 1)
    start_local = datetime.combine(year_start, datetime.min.time(), tzinfo=local_tz)
    end_local = datetime.combine(year_end, datetime.min.time(), tzinfo=local_tz)

    return {
        "start": _to_utc_iso(start_local),
        "end": _to_utc_iso(end_local),
    }


def get_full_year_before_time_range(target_date: date, tz: str = _DEFAULT_TZ) -> dict:
    """取得 target_date 所在年份的「前一年」完整年份時間區間."""
    year_before = date(target_date.year - 1, 1, 1)
    return get_full_year_time_range(year_before, tz)


def get_current_year_time_range(tz: str = _DEFAULT_TZ) -> dict:
    """
    取得今年 1/1 00:00 至當下同一時刻的時間區間.

    今年尚未結束,故對齊 UI 年粒度「今年」卡片主數值顯示的區間(進行中年度、非整年).
    """
    local_tz = ZoneInfo(tz)
    now_local = datetime.now(local_tz)
    year_start = date(now_local.year, 1, 1)
    start_local = datetime.combine(year_start, datetime.min.time(), tzinfo=local_tz)

    return {
        "start": _to_utc_iso(start_local),
        "end": _to_utc_iso(now_local.replace(microsecond=0)),
    }


def get_last_year_until_now_time_range(tz: str = _DEFAULT_TZ) -> dict:
    """
    取得去年 1/1 00:00 至「本月月初往前 12 個月」隔日 00:01 的時間區間.

    實測攔截前端實際發出的請求後確認:UI 年粒度的「去年同時段」比較列是以「月」為單位
    截斷(即今年已完整經過的月數,不含進行中的本月),而非精確到天;
    呼叫端須改用 [[energy_overview_suites.get_historical_totals_kwh]](historical-data API、
    MONTH 粒度)查詢此區間,直接對 /v1/fields/totals 查詢會得到不同的總量.
    """
    local_tz = ZoneInfo(tz)
    today_local = datetime.now(local_tz).date()
    this_month_start = _first_of_month(today_local)
    last_year_start = date(today_local.year - 1, 1, 1)
    target_month_start = _add_months(this_month_start, -12)

    start_local = datetime.combine(last_year_start, datetime.min.time(), tzinfo=local_tz)
    end_local = datetime.combine(
        target_month_start, datetime.min.time(), tzinfo=local_tz
    ) + timedelta(minutes=1)

    return {
        "start": _to_utc_iso(start_local),
        "end": _to_utc_iso(end_local),
    }


def _elapsed_time_range_within_month(month_start: date, tz: str) -> dict:
    """
    取得指定月份第一天 00:00 至「與當下同一天期與時刻」的時間區間;
    若該月天數不足以達到當下日期(例如當下是 31 號但該月只有 30 天),則以該月最後一天同一時刻封頂.
    """
    local_tz = ZoneInfo(tz)
    now_local = datetime.now(local_tz)
    days_in_month = (_add_months(month_start, 1) - month_start).days
    day_of_month = min(now_local.day, days_in_month)
    end_date = month_start + timedelta(days=day_of_month - 1)

    start_local = datetime.combine(month_start, datetime.min.time(), tzinfo=local_tz)
    end_local = datetime.combine(
        end_date, now_local.time().replace(microsecond=0), tzinfo=local_tz
    )

    return {
        "start": _to_utc_iso(start_local),
        "end": _to_utc_iso(end_local),
    }


def get_current_month_time_range(tz: str = _DEFAULT_TZ) -> dict:
    """
    取得本月 1 號 00:00 至當下同一時刻的時間區間.

    本月尚未結束,故對齊 UI 月粒度「這個月」卡片主數值顯示的區間(進行中月份、非整月).
    """
    this_month_start = _first_of_month(datetime.now(ZoneInfo(tz)).date())
    return _elapsed_time_range_within_month(this_month_start, tz)


def get_current_month_full_time_range(tz: str = _DEFAULT_TZ) -> dict:
    """
    取得本月完整月份區間:1 號 00:00 至下月 1 號 00:00,不論本月是否已結束.

    實測發現:全域總覽地圖切換為「本月」粒度時,查詢區間是完整的本月曆月
    (而非像 [[get_current_month_time_range]] 那樣只到當下時刻),
    未發生的天數自然沒有資料,故直接查整月即可.
    """
    this_month_start = _first_of_month(datetime.now(ZoneInfo(tz)).date())
    next_month_start = _add_months(this_month_start, 1)
    local_tz = ZoneInfo(tz)
    start_local = datetime.combine(this_month_start, datetime.min.time(), tzinfo=local_tz)
    end_local = datetime.combine(next_month_start, datetime.min.time(), tzinfo=local_tz)
    return {
        "start": _to_utc_iso(start_local),
        "end": _to_utc_iso(end_local),
    }


def get_current_year_full_time_range(tz: str = _DEFAULT_TZ) -> dict:
    """
    取得今年完整年份區間:1/1 00:00 至明年 1/1 00:00,不論今年是否已結束.

    理由同 [[get_current_month_full_time_range]]:全域總覽地圖「今年」粒度查詢的是完整曆年.
    """
    local_tz = ZoneInfo(tz)
    this_year = datetime.now(local_tz).date().year
    start_local = datetime.combine(date(this_year, 1, 1), datetime.min.time(), tzinfo=local_tz)
    end_local = datetime.combine(date(this_year + 1, 1, 1), datetime.min.time(), tzinfo=local_tz)
    return {
        "start": _to_utc_iso(start_local),
        "end": _to_utc_iso(end_local),
    }


def _shift_months_clamped(target_date: date, months: int) -> date:
    """
    將 target_date 平移 months 個月,日序數(day-of-month)沿用原日期;
    若目標月份天數不足則以該月最後一天封頂(例如 1/31 平移 1 個月得到 2/28 或 2/29).
    """
    month_index = target_date.year * 12 + (target_date.month - 1) + months
    year, month = month_index // 12, month_index % 12 + 1
    next_month_index = month_index + 1
    days_in_target_month = (
        date(next_month_index // 12, next_month_index % 12 + 1, 1)
        - date(year, month, 1)
    ).days
    day = min(target_date.day, days_in_target_month)
    return date(year, month, day)


def _month_comparison_time_range(months_back: int, tz: str = _DEFAULT_TZ) -> dict:
    """
    取得畫面月粒度下「上個月／去年同月」比較列的時間區間:
    起:本月往前 months_back 個月的第一天 00:00;
    迄:今天往前 months_back 個月的同一日期,隔日 00:01.

    實測攔截前端實際發出的請求後確認:此區間並非「已完整經過天數」或「完整整月」,
    而是精確對齊到「今天」平移 months_back 個月後再加 1 分鐘(前端請求裡固定的 1 分鐘偏移,
    推測是為避免邊界時刻的資料遺漏);呼叫端須改用
    [[energy_overview_suites.get_historical_totals_kwh]](historical-data API、DAY 粒度)查詢,
    直接對 /v1/fields/totals 查詢會得到不同的總量.
    """
    local_tz = ZoneInfo(tz)
    today_local = datetime.now(local_tz).date()
    this_month_start = _first_of_month(today_local)
    target_month_start = _add_months(this_month_start, -months_back)
    target_end_date = _shift_months_clamped(today_local, -months_back)

    start_local = datetime.combine(target_month_start, datetime.min.time(), tzinfo=local_tz)
    end_local = datetime.combine(
        target_end_date, datetime.min.time(), tzinfo=local_tz
    ) + timedelta(minutes=1)

    return {
        "start": _to_utc_iso(start_local),
        "end": _to_utc_iso(end_local),
    }


def get_last_month_until_now_time_range(tz: str = _DEFAULT_TZ) -> dict:
    """取得「上個月」比較列的時間區間,詳見 [[_month_comparison_time_range]]."""
    return _month_comparison_time_range(1, tz)


def get_same_month_last_year_until_now_time_range(tz: str = _DEFAULT_TZ) -> dict:
    """取得「去年同月」比較列的時間區間,詳見 [[_month_comparison_time_range]]."""
    return _month_comparison_time_range(12, tz)


def _get_day_until_now_time_range(target_date: date, tz: str) -> dict:
    """取得指定日期 00:00 至「當下同一時刻」的時間區間(對齊 UI 比較區間)."""
    local_tz = ZoneInfo(tz)
    now_local = datetime.now(local_tz)
    start_local = datetime.combine(target_date, datetime.min.time(), tzinfo=local_tz)
    end_local = datetime.combine(
        target_date, now_local.time().replace(microsecond=0), tzinfo=local_tz
    )

    return {
        "start": _to_utc_iso(start_local),
        "end": _to_utc_iso(end_local),
    }


def get_yesterday_until_now_time_range(tz: str = _DEFAULT_TZ) -> dict:
    """取得前一日 00:00 至當下同一時刻的時間區間."""
    yesterday = datetime.now(ZoneInfo(tz)).date() - timedelta(days=1)
    return _get_day_until_now_time_range(yesterday, tz)


def get_last_week_today_until_now_time_range(tz: str = _DEFAULT_TZ) -> dict:
    """取得上週同星期 00:00 至當下同一時刻的時間區間."""
    last_week_today = datetime.now(ZoneInfo(tz)).date() - timedelta(days=7)
    return _get_day_until_now_time_range(last_week_today, tz)


def format_slash_date(target_date: date) -> str:
    """將日期格式化為 YYYY/MM/DD."""
    return target_date.strftime("%Y/%m/%d")


def format_slash_year_month(target_date: date) -> str:
    """將日期格式化為 YYYY/MM(月份粒度,不含日)."""
    return target_date.strftime("%Y/%m")


def get_yesterday_display_label(
    tz: str = _DEFAULT_TZ, lang: str | None = None, reference_date: date | None = None
) -> str:
    """
    UI 前一日標籤,依語言顯示,例如:前一日 2026/07/13、Yesterday 2026/07/13.

    reference_date 預設為今天;傳入畫面目前選取的日期,可算出該日的前一日標籤.
    """
    language = _resolve_language(lang)
    prefix = _YESTERDAY_LABEL_PREFIX.get(
        language, _YESTERDAY_LABEL_PREFIX[_DEFAULT_LANGUAGE]
    )
    base = reference_date or datetime.now(ZoneInfo(tz)).date()
    yesterday = base - timedelta(days=1)
    return f"{prefix} {format_slash_date(yesterday)}"


def get_last_week_today_display_label(
    tz: str = _DEFAULT_TZ, lang: str | None = None, reference_date: date | None = None
) -> str:
    """
    UI 上週同日標籤,依語言顯示,例如:上週二 2026/07/07、Last Tue 2026/07/07.

    reference_date 預設為今天;傳入畫面目前選取的日期,可算出該日的上週同日標籤.
    """
    language = _resolve_language(lang)
    cfg = _LAST_WEEK_LABEL_CONFIG.get(
        language, _LAST_WEEK_LABEL_CONFIG[_DEFAULT_LANGUAGE]
    )
    base = reference_date or datetime.now(ZoneInfo(tz)).date()
    last_week_today = base - timedelta(days=7)
    weekday_label = cfg["weekdays"][last_week_today.weekday()]
    return (
        f"{cfg['prefix']}{cfg['joiner']}{weekday_label}{cfg['suffix']} "
        f"{format_slash_date(last_week_today)}"
    )


def get_last_month_display_label(
    tz: str = _DEFAULT_TZ, lang: str | None = None, reference_date: date | None = None
) -> str:
    """
    UI 上個月標籤,依語言顯示,例如:上個月 2026/06、Last Month 2026/06.

    reference_date 預設為今天;傳入畫面目前選取月份所在的任一日期,可算出該月的上個月標籤.
    """
    language = _resolve_language(lang)
    prefix = _LAST_MONTH_LABEL_PREFIX.get(
        language, _LAST_MONTH_LABEL_PREFIX[_DEFAULT_LANGUAGE]
    )
    base = reference_date or datetime.now(ZoneInfo(tz)).date()
    last_month = _add_months(_first_of_month(base), -1)
    return f"{prefix} {format_slash_year_month(last_month)}"


def get_same_month_last_year_display_label(
    tz: str = _DEFAULT_TZ, lang: str | None = None, reference_date: date | None = None
) -> str:
    """
    UI 去年同月標籤,依語言顯示,例如:去年同月 2025/07、Last Year 2025/07.

    reference_date 預設為今天;傳入畫面目前選取月份所在的任一日期,可算出去年同月的標籤.
    """
    language = _resolve_language(lang)
    prefix = _SAME_MONTH_LAST_YEAR_LABEL_PREFIX.get(
        language, _SAME_MONTH_LAST_YEAR_LABEL_PREFIX[_DEFAULT_LANGUAGE]
    )
    base = reference_date or datetime.now(ZoneInfo(tz)).date()
    same_month_last_year = _add_months(_first_of_month(base), -12)
    return f"{prefix} {format_slash_year_month(same_month_last_year)}"


def get_last_year_display_label(
    tz: str = _DEFAULT_TZ, lang: str | None = None, reference_date: date | None = None
) -> str:
    """
    UI 去年同時段標籤,依語言顯示,例如:去年同時段 2025、Last Year 2025.

    reference_date 預設為今天;傳入畫面目前選取年度所在的任一日期,可算出該年度的前一年標籤.
    """
    language = _resolve_language(lang)
    prefix = _LAST_YEAR_LABEL_PREFIX.get(
        language, _LAST_YEAR_LABEL_PREFIX[_DEFAULT_LANGUAGE]
    )
    base = reference_date or datetime.now(ZoneInfo(tz)).date()
    return f"{prefix} {base.year - 1}"


def get_calendar_day_timestamp(target_date: date, tz: str = _DEFAULT_TZ) -> int:
    """
    換算日期選擇器(MUI DateCalendar)單一日期格子的 data-timestamp:
    該日當地時區 00:00 的 epoch 毫秒,供 [[pages.energy_overview_page.date_picker_day_cell]] 定位使用.
    """
    local_tz = ZoneInfo(tz)
    start_local = datetime.combine(target_date, datetime.min.time(), tzinfo=local_tz)
    return int(start_local.timestamp() * 1000)


_CALENDAR_MONTH_OPTION_LABELS_ZH = [
    "一月", "二月", "三月", "四月", "五月", "六月",
    "七月", "八月", "九月", "十月", "十一月", "十二月",
]

_CALENDAR_MONTH_OPTION_LABELS_JA = [f"{month}月" for month in range(1, 13)]

# 英文月份全名,同時供月份選單 aria-label(英文站台與中/日文站台一致,皆為全名)
# 與月曆彈窗標題共用.
_CALENDAR_MONTH_HEADER_NAMES_EN = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def format_calendar_month_option_label(target_date: date, lang: str | None = None) -> str:
    """
    日期選擇器「月粒度」跳出的月份選單裡,指定月份選項的 aria-label.

    實測確認:zh-TW 為中文月份全名(例如「六月」);ja 為「N月」(無前導零,例如「6月」);
    en 為英文月份全名(例如「July」).
    """
    language = _resolve_language(lang)
    if language == "ja":
        return _CALENDAR_MONTH_OPTION_LABELS_JA[target_date.month - 1]
    if language == "en":
        return _CALENDAR_MONTH_HEADER_NAMES_EN[target_date.month - 1]
    return _CALENDAR_MONTH_OPTION_LABELS_ZH[target_date.month - 1]


def format_calendar_month_header(target_date: date, lang: str | None = None) -> str:
    """
    日期選擇器月曆標題文字,例如「2026年7月」.

    實測確認(直接以 Playwright expect().to_have_text() 對真實頁面驗證):en 站台
    實際顯示「2026August」(年份與英文月份全名之間無空格,並非原先假設的固定中文
    格式);ja 站台此彈出視窗尚未實測確認,暫沿用 zh-TW 格式(「年/月」漢字在 ja
    站台其他地方已確認共用,風險較低,待實測後再校正).
    """
    language = _resolve_language(lang)
    if language == "en":
        return f"{target_date.year}{_CALENDAR_MONTH_HEADER_NAMES_EN[target_date.month - 1]}"
    return f"{target_date.year}年{target_date.month}月"


def format_date_switcher_day_label(target_date: date, lang: str | None = None) -> str:
    """
    日期切換器(日粒度)顯示的完整日期文字,例如「2026年07月30日」.

    實測確認:en 站台顯示「2026/07/30」;ja 站台與 zh-TW 相同格式.
    """
    language = _resolve_language(lang)
    if language == "en":
        return target_date.strftime("%Y/%m/%d")
    return target_date.strftime("%Y年%m月%d日")


def format_date_switcher_month_label(target_date: date, lang: str | None = None) -> str:
    """
    日期切換器(月粒度)顯示的年月文字,例如「2026年07月」.

    ja 已實測確認與 zh-TW 相同格式.en 實測確認(en 語系測試失敗訊息的 aria
    snapshot):與月曆彈窗標題([[format_calendar_month_header]])同為「YYYY」+
    英文月份全名、無分隔符號的格式(例如「2026August」),並非原先推斷的「YYYY/MM」.
    """
    language = _resolve_language(lang)
    if language == "en":
        return f"{target_date.year}{_CALENDAR_MONTH_HEADER_NAMES_EN[target_date.month - 1]}"
    return target_date.strftime("%Y年%m月")


def format_date_switcher_year_label(target_date: date, lang: str | None = None) -> str:
    """
    日期切換器(年粒度)顯示的年度文字,例如「2026年」.

    ja 已實測確認與 zh-TW 相同格式.en 尚未實測確認,推斷僅顯示年份數字
    (不加後綴),待實測校正.
    """
    language = _resolve_language(lang)
    if language == "en":
        return f"{target_date.year}"
    return f"{target_date.year}年"


def format_quarterly_time_range_label(
    utc_timestamp: str, interval_minutes: int = 15, tz: str = _DEFAULT_TZ
) -> str:
    """API 最新時間戳轉 UI 15 分鐘區間,例如 2026-07-14T08:15:00Z -> 16:15 - 16:30."""
    dt_utc = datetime.fromisoformat(utc_timestamp.replace("Z", "+00:00"))
    dt_local = dt_utc.astimezone(ZoneInfo(tz))
    start = dt_local.strftime("%H:%M")
    end = (dt_local + timedelta(minutes=interval_minutes)).strftime("%H:%M")
    return f"{start} - {end}"
