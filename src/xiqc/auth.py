from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from xiqc.exceptions import XiqcAuthError

logger = logging.getLogger(__name__)

GRANT_PASSWORD = "password"
GRANT_REFRESH = "refresh_token"
REFRESH_THRESHOLD = 300  # seconds before expiry to proactively refresh


class AuthClient:
    """Manages OAuth2 tokens for the XIQ-C API."""

    def __init__(
        self,
        base_url: str,
        user_id: str,
        password: str,
        scope: str = "",
        verify: bool = True,
    ) -> None:
        self._base_url = base_url
        self._user_id = user_id
        self._password = password
        self._scope = scope
        self._verify = verify
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._expires_at: float = 0.0

    @property
    def access_token(self) -> str:
        """Return a valid access token, refreshing proactively when near expiry."""
        if self._needs_refresh():
            self._authenticate()
        assert self._access_token is not None
        return self._access_token

    def _needs_refresh(self) -> bool:
        if self._access_token is None:
            return True
        return time.monotonic() >= self._expires_at - REFRESH_THRESHOLD

    def _authenticate(self) -> None:
        if self._refresh_token:
            try:
                self._token_request(
                    {"grantType": GRANT_REFRESH, "refreshToken": self._refresh_token}
                )
                return
            except XiqcAuthError:
                logger.warning("Refresh grant failed; retrying with password grant.")
        self._token_request(
            {
                "grantType": GRANT_PASSWORD,
                "userId": self._user_id,
                "password": self._password,
                "scope": self._scope,
            }
        )

    def _token_request(self, body: dict[str, Any]) -> None:
        url = f"{self._base_url}/oauth2/token"
        try:
            response = httpx.post(url, json=body, verify=self._verify)
        except httpx.RequestError as exc:
            raise XiqcAuthError(f"Network error during auth: {exc}") from exc
        if response.status_code != 200:
            raise XiqcAuthError(f"Auth failed with status {response.status_code}")
        data = response.json()
        self._access_token = data["access_token"]
        self._refresh_token = data.get("refresh_token")
        expires_in: int = data.get("expires_in", 7200)
        self._expires_at = time.monotonic() + expires_in
        logger.debug(
            "Token acquired, expires_in=%s, access_token=<redacted>.", expires_in
        )
