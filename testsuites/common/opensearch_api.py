"""業務層 OpenSearch 查詢封裝 (Wrapper).

底層走 libs/http_utils.py 的 opensearch_api_post_request() (basic auth)。
這裡只回傳 raw response, 不做斷言 (斷言交給 flow 層)。
"""

from libs.http_utils import opensearch_api_post_request

# server 端 config 下發訊息固定帶的 app_id marker (實測確認為固定值,
# 不是隨環境變動的資料), 用來從 websocket log 篩出「config 下發」這類事件。
CONFIG_DISPATCH_APP_ID = "434f4e46-4947-4d61-6e61-47654d656e54"

# gateway 上線後, config 下發記錄所在的 index (實測確認為 ns_infra-external-*,
# 不是 case 文件寫的 Infra-external / ns_Infra-external)
INFRA_EXTERNAL_INDEX = "ns_infra-external-*"


def search_gateway_config_dispatch(gateway_uuid: str, start_time: str, end_time: str):
    """查某個 gateway 在指定時間區間內, 「config 下發 (device receive)」的 log.

    gateway_uuid: gateway 的 profile_id (即 server log 裡的「gateway HW uuid」)
    start_time / end_time: UTC ISO8601 字串 (例如 2026-08-20T01:00:00.000Z)

    回傳 OpenSearch 原始 response (Dict), 呼叫端可用 response.response.hits.total.value
    取得筆數 (斷言「同一個 config 不應該送兩次」時需要), 或用
    response.response.hits.hits 取得每一筆完整內容。
    """
    body = {
        "size": 50,
        "query": {
            "bool": {
                "must": [
                    {"match_phrase": {"log": gateway_uuid}},
                    {"match_phrase": {"log": "device receive"}},
                    {"match_phrase": {"log": CONFIG_DISPATCH_APP_ID}},
                ],
                "filter": [
                    {"range": {"@timestamp": {"gte": start_time, "lte": end_time}}}
                ],
            }
        },
        "sort": [{"@timestamp": "desc"}],
    }
    return opensearch_api_post_request(f"/{INFRA_EXTERNAL_INDEX}/_search", json=body)
