from libs.assert_utils import assert_equal
from libs.config_utils import config


def check_restful_response(response, error):
    """
    驗證 API 回應狀態碼並回傳解包後的內容.

    error=None 預期成功(200);傳入錯誤碼(例如 403)代表這次呼叫本來就預期被拒絕.
    """
    status_code = response.status_code
    response = response.response

    expected_status = config.http_status_code.ok if error is None else error
    assert_equal(status_code, expected_status, "驗證 API 回應狀態碼", context={"response": response})
    return response
