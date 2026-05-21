from __future__ import annotations

import logging
from typing import Any

import httpx

from xiqc._http import _throttle, build_client
from xiqc.auth import AuthClient
from xiqc.exceptions import XiqcAPIError, XiqcConnectionError
from xiqc.models import Ap, ApSmartRf, ApStats, Site, SiteSmartRf, Station

logger = logging.getLogger(__name__)

_DEFAULT_PORT = 5825
_MGMT_V1 = "/management/v1"

# Endpoint path constants — API versions intentionally mixed, never normalise.
_PATH_APS = "/management/v1/aps"
_PATH_STATIONS_QUERY = "/management/v1/stations/query"
_PATH_SITES = "/management/v3/sites"
_PATH_AP_SMARTRF = "/management/v2/aps/{}/smartrf"
_PATH_SITE_SMARTRF = "/management/v4/sites/{}/smartrf"


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
        self._root = f"https://{host}:{port}"
        self._auth = AuthClient(
            base_url=f"{self._root}{_MGMT_V1}",
            user_id=user_id,
            password=password,
            scope=scope,
            verify=verify,
        )
        self._http = build_client(verify=verify, timeout=timeout)

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        """Send a throttled, authenticated request.

        ``path`` must be a full ``/management/...`` path.
        """
        _throttle()
        url = f"{self._root}{path}"
        headers = {"Authorization": f"Bearer {self._auth.access_token}"}
        try:
            response = self._http.request(method, url, headers=headers, **kwargs)
        except httpx.RequestError as exc:
            raise XiqcConnectionError(f"Connection error: {exc}") from exc
        if not response.is_success:
            raise XiqcAPIError(response.status_code, response.text)
        return response

    def _unwrap_list(self, response: httpx.Response) -> list[Any]:
        """Extract the item list from a response, unwrapping a ``data`` envelope."""
        payload = response.json()
        if isinstance(payload, dict) and "data" in payload:
            return payload["data"]  # type: ignore[no-any-return]
        return payload  # type: ignore[no-any-return]

    def list_aps(self) -> list[Ap]:
        """Return all AP configuration records from GET /management/v1/aps."""
        items = self._unwrap_list(self._request("GET", _PATH_APS))
        return [Ap.model_validate(item) for item in items]

    def get_ap(self, serial: str) -> Ap:
        """Return a single AP configuration record by serial number."""
        data = self._request("GET", f"{_PATH_APS}/{serial}").json()
        return Ap.model_validate(data)

    def list_ap_stats(self) -> list[ApStats]:
        """Return extended per-AP statistics from GET /management/v1/aps/query."""
        items = self._unwrap_list(self._request("GET", f"{_PATH_APS}/query"))
        return [ApStats.model_validate(item) for item in items]

    def list_stations(
        self, *, active: bool = True, duration: str = "3H"
    ) -> list[Station]:
        """Return station (client) records from GET /management/v1/stations/query.

        Args:
            active: When True, return only currently associated stations.
            duration: Time window — one of ``3H``, ``3D``, ``14D``.
        """
        params = {"showActive": str(active).lower(), "duration": duration}
        items = self._unwrap_list(
            self._request("GET", _PATH_STATIONS_QUERY, params=params)
        )
        return [Station.model_validate(item) for item in items]

    def list_sites(self) -> list[Site]:
        """Return all site records from GET /management/v3/sites."""
        items = self._unwrap_list(self._request("GET", _PATH_SITES))
        return [Site.model_validate(item) for item in items]

    def get_ap_smartrf(self, serial: str) -> ApSmartRf:
        """Return SmartRF channel/power assignments for an AP.

        Calls GET /management/v2/aps/{serial}/smartrf.
        """
        data = self._request("GET", _PATH_AP_SMARTRF.format(serial)).json()
        return ApSmartRf.model_validate(data)

    def get_site_smartrf(self, site_id: str) -> SiteSmartRf:
        """Return SmartRF configuration for a site.

        Calls GET /management/v4/sites/{siteId}/smartrf.
        """
        data = self._request("GET", _PATH_SITE_SMARTRF.format(site_id)).json()
        return SiteSmartRf.model_validate(data)
