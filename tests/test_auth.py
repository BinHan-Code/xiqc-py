from __future__ import annotations

import time

import httpx
import pytest
import respx

from xiqc.auth import AuthClient
from xiqc.exceptions import XiqcAuthError

_BASE_URL = "https://lab-ctrl.example.test:5825/management/v1"
_TOKEN_URL = f"{_BASE_URL}/oauth2/token"
_TOKEN_RESPONSE = {
    "access_token": "fake-access-token",
    "refresh_token": "fake-refresh-token",
    "expires_in": 7200,
}


@pytest.fixture
def auth_client() -> AuthClient:
    return AuthClient(
        base_url=_BASE_URL,
        user_id="admin",
        password="secret",
        verify=False,
    )


@respx.mock
def test_auth_password_grant_returns_token(auth_client: AuthClient) -> None:
    respx.post(_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN_RESPONSE))
    assert auth_client.access_token == "fake-access-token"


@respx.mock
def test_auth_bad_credentials_raises_xiqcautherror(auth_client: AuthClient) -> None:
    respx.post(_TOKEN_URL).mock(return_value=httpx.Response(401, text="Unauthorized"))
    with pytest.raises(XiqcAuthError):
        _ = auth_client.access_token


@respx.mock
def test_auth_expired_token_triggers_refresh(auth_client: AuthClient) -> None:
    respx.post(_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN_RESPONSE))
    _ = auth_client.access_token
    auth_client._expires_at = time.monotonic()  # force expiry
    _ = auth_client.access_token
    assert respx.calls.call_count == 2
