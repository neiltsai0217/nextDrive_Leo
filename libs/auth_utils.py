"""Authentication helpers shared by pytest fixtures."""

import requests

from libs.config_utils import config


def mask_token(token):
    if not token:
        return None
    return f"{token[:8]}...{token[-8:]}"


def _is_jwt(token):
    return isinstance(token, str) and token.count(".") == 2


def _exchange_refresh_token(refresh_token):
    response = requests.post(
        f"{config.services.cems_api_url}/v1/token/exchange",
        json={"token": refresh_token},
        timeout=30,
        verify=False,
    )
    response.raise_for_status()
    return response.json()


def resolve_auth_tokens(account):
    """Resolve an access token, exchanging a refresh token when available."""
    access_token = account.get("access_token")
    refresh_token = account.get("refresh_token")

    if refresh_token:
        token_response = _exchange_refresh_token(refresh_token)
        token_data = token_response.get("data", token_response)
        return {
            "access_token": token_data.get("accessToken")
            or token_data.get("access_token"),
            "refresh_token": token_data.get("refreshToken")
            or token_data.get("refresh_token"),
        }

    if not _is_jwt(access_token):
        raise ValueError(
            "admin_user.access_token 不是有效 JWT。"
            "請透過 CEMS_ACCESS_TOKEN 提供完整 access token，或透過 "
            "CEMS_REFRESH_TOKEN 提供 refresh token。"
        )

    return {"access_token": access_token, "refresh_token": refresh_token}
