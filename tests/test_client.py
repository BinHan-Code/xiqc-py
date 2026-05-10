from __future__ import annotations

import httpx
import pytest
import respx

from xiqc.client import XiqcClient
from xiqc.exceptions import XiqcAPIError, XiqcConnectionError

_HOST = "lab-ctrl.example.test"
_BASE_URL = f"https://{_HOST}:5825/management/v1"
_TOKEN_URL = f"{_BASE_URL}/oauth2/token"
_TOKEN_RESPONSE = {
    "access_token": "fake-access-token",
    "refresh_token": "fake-refresh-token",
    "expires_in": 7200,
}


@pytest.fixture
def client() -> XiqcClient:
    return XiqcClient(host=_HOST, user_id="admin", password="secret", verify=False)


@respx.mock
def test_client_request_raises_on_api_error(client: XiqcClient) -> None:
    respx.post(_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN_RESPONSE))
    respx.get(f"{_BASE_URL}/test").mock(
        return_value=httpx.Response(404, text="Not Found")
    )
    with pytest.raises(XiqcAPIError) as exc_info:
        client._request("GET", "/test")
    assert exc_info.value.status_code == 404


@respx.mock
def test_client_request_raises_on_connection_error(client: XiqcClient) -> None:
    respx.post(_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN_RESPONSE))
    respx.get(f"{_BASE_URL}/test").mock(side_effect=httpx.ConnectError("refused"))
    with pytest.raises(XiqcConnectionError):
        client._request("GET", "/test")
