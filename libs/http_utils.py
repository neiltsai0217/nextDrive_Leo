import time
import requests
from addict import Dict
from libs.config_utils import get_config
from libs.log_utils import get_logger

_logger = get_logger(__name__)


def cems_api_post_request(uri, **kwargs):
    response = _api_request('cems_api', 'POST', uri, **kwargs)
    return response


def cems_api_get_request(uri, **kwargs):
    response = _api_request('cems_api', 'GET', uri, **kwargs)
    return response


def cems_api_put_request(uri, **kwargs):
    response = _api_request('cems_api', 'PUT', uri, **kwargs)
    return response


def ioe_api_post_request(uri, **kwargs):
    response = _api_request('ioe_api', 'POST', uri, **kwargs)
    return response


def ioe_api_get_request(uri, **kwargs):
    response = _api_request('ioe_api', 'GET', uri, **kwargs)
    return response


def ioe_api_delete_request(uri, **kwargs):
    response = _api_request('ioe_api', 'DELETE', uri, **kwargs)
    return response


def eg3_app_api_post_request(uri, **kwargs):
    response = _api_request('eg3_app_api', 'POST', uri, **kwargs)
    return response


def eg3_app_api_get_request(uri, **kwargs):
    response = _api_request('eg3_app_api', 'GET', uri, **kwargs)
    return response


def opensearch_api_post_request(uri, **kwargs):
    """OpenSearch 走 basic auth (帳密在 variables 的 opensearch), 不是 Bearer token,
    所以獨立一條路徑, 不走 _api_request/cems_api 那套 access_token 邏輯."""
    config = get_config()
    opensearch = config.opensearch

    url = f"{opensearch.url}{uri}"
    _logger.info(f'url: {url}')

    kwargs.setdefault('auth', (opensearch.username, opensearch.password))

    http_response = _request('POST', url, **kwargs)
    try:
        return Dict({
            "status_code": http_response.status_code,
            "response": _parse_response_body(http_response),
        })
    finally:
        http_response.close()


def _api_request(service_name, method, uri, **kwargs):
    config = get_config()

    api_base_url = config.services[f"{service_name}_url"]

    url = f"{api_base_url}{uri}"
    _logger.info(f'url: {url}')

    headers = kwargs.get('headers', {})
    kwargs['headers'] = headers
    role = kwargs.pop('role', None)
    if role:
        user = getattr(config.users, role)
        _logger.debug(f"Call api by user {user.user_id}.")
        access_token = user.access_token
    else:
        access_token = kwargs.pop('access_token', None)

    if access_token:
        headers['Authorization'] = f"Bearer {access_token}"

    http_response = _request(method, url, **kwargs)
    try:
        return Dict({
            "status_code": http_response.status_code,
            "response": _parse_response_body(http_response),
        })
    finally:
        http_response.close()


def _parse_response_body(http_response):
    try:
        return http_response.json()
    except ValueError:
        return http_response.text


def _request(method, url, **kwargs):
    config = get_config()
    kwargs.setdefault("timeout", 30)
    kwargs.setdefault("verify", False)

    for attempt in range(2):
        start_time = time.perf_counter()
        try:
            response = requests.request(method, url, **kwargs)
            spent_time = int((time.perf_counter() - start_time) * 1000)
            request_id = response.headers.get("X-Amz-Cf-Id")
            _logger.debug(
                "Receive %s %s (request_id=%s) in %s ms",
                method,
                url,
                request_id,
                spent_time,
            )
            return response
        except (requests.ConnectionError, requests.Timeout):
            if attempt == 1:
                raise
            _logger.warning("HTTP request failed; retrying once: %s %s", method, url)

    raise RuntimeError("HTTP retry loop exited unexpectedly")
