from __future__ import annotations

import logging

import httpx

from xiqc._http import _throttle, build_client
from xiqc.auth import AuthClient
from xiqc.exceptions import XiqcAPIError, XiqcConnectionError

logger = logging.getLogger(__name__)

_DEFAULT_PORT = 5825
_BASE_PATH = "/management/v1"


class XiqcClient:
    """High-level client for the XIQ-C REST API."""

    def __init__(
        self,
        host: str,
        user_id: str,
        password: str,
        port: int = _DEFAULT_PORT,
        verify: bool = True,
        scope: str = "",
        timeout: float = 30.0,
    ) -> None:
        self._base_url = f"https://{host}:{port}{_BASE_PATH}"
        self._auth = AuthClient(
            base_url=self._base_url,
            user_id=user_id,
            password=password,
            scope=scope,
            verify=verify,
        )
        self._http = build_client(verify=verify, timeout=timeout)

    def _request(self, method: str, path: str, **kwargs: object) -> httpx.Response:
        """Send a throttled, authenticated request to the controller."""
        _throttle()
        url = f"{self._base_url}{path}"
        headers = {"Authorization": f"Bearer {self._auth.access_token}"}
        try:
            response = self._http.request(method, url, headers=headers, **kwargs)
        except httpx.RequestError as exc:
            raise XiqcConnectionError(f"Connection error: {exc}") from exc
        if not response.is_success:
            raise XiqcAPIError(response.status_code, response.text)
        return response
