from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import respx

from xiqc.client import XiqcClient
from xiqc.exceptions import XiqcAPIError, XiqcConnectionError
from xiqc.models import Ap, ApSmartRf, ApStats, Site, SiteSmartRf, Station

_HOST = "lab-ctrl.example.test"
_ROOT = f"https://{_HOST}:5825"
_MGMT_V1 = "/management/v1"
_TOKEN_URL = f"{_ROOT}{_MGMT_V1}/oauth2/token"
_TOKEN_RESPONSE = {
    "access_token": "fake-access-token",
    "refresh_token": "fake-refresh-token",
    "expires_in": 7200,
}

_FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> dict:  # type: ignore[type-arg]
    return json.loads((_FIXTURES / name).read_text())


@pytest.fixture
def client() -> XiqcClient:
    return XiqcClient(host=_HOST, user_id="admin", password="secret", verify=False)


def _mock_token() -> None:
    respx.post(_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN_RESPONSE))


# ---------------------------------------------------------------------------
# _request plumbing
# ---------------------------------------------------------------------------


@respx.mock
def test_client_request_raises_on_api_error(client: XiqcClient) -> None:
    _mock_token()
    respx.get(f"{_ROOT}{_MGMT_V1}/test").mock(
        return_value=httpx.Response(404, text="Not Found")
    )
    with pytest.raises(XiqcAPIError) as exc_info:
        client._request("GET", f"{_MGMT_V1}/test")
    assert exc_info.value.status_code == 404


@respx.mock
def test_client_request_raises_on_connection_error(client: XiqcClient) -> None:
    _mock_token()
    respx.get(f"{_ROOT}{_MGMT_V1}/test").mock(side_effect=httpx.ConnectError("refused"))
    with pytest.raises(XiqcConnectionError):
        client._request("GET", f"{_MGMT_V1}/test")


# ---------------------------------------------------------------------------
# list_aps
# ---------------------------------------------------------------------------


@respx.mock
def test_list_aps_returns_ap_models(client: XiqcClient) -> None:
    _mock_token()
    respx.get(f"{_ROOT}/management/v1/aps").mock(
        return_value=httpx.Response(200, json=_fixture("ap_list.json"))
    )
    aps = client.list_aps()
    assert len(aps) == 2
    assert all(isinstance(ap, Ap) for ap in aps)
    assert aps[0].serial_number == "LAB-AP-0001"
    assert aps[1].serial_number == "LAB-AP-0002"


@respx.mock
def test_list_aps_raises_on_api_error(client: XiqcClient) -> None:
    _mock_token()
    respx.get(f"{_ROOT}/management/v1/aps").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )
    with pytest.raises(XiqcAPIError):
        client.list_aps()


# ---------------------------------------------------------------------------
# get_ap
# ---------------------------------------------------------------------------


@respx.mock
def test_get_ap_returns_single_ap(client: XiqcClient) -> None:
    _mock_token()
    ap_data = _fixture("ap_list.json")["data"][0]
    respx.get(f"{_ROOT}/management/v1/aps/LAB-AP-0001").mock(
        return_value=httpx.Response(200, json=ap_data)
    )
    ap = client.get_ap("LAB-AP-0001")
    assert isinstance(ap, Ap)
    assert ap.serial_number == "LAB-AP-0001"


# ---------------------------------------------------------------------------
# list_ap_stats
# ---------------------------------------------------------------------------


@respx.mock
def test_list_ap_stats_returns_apstats_models(client: XiqcClient) -> None:
    _mock_token()
    respx.get(f"{_ROOT}/management/v1/aps/query").mock(
        return_value=httpx.Response(200, json=_fixture("ap_stats_list.json"))
    )
    stats = client.list_ap_stats()
    assert len(stats) == 2
    assert all(isinstance(s, ApStats) for s in stats)
    assert stats[0].ap_serial == "LAB-AP-0001"
    assert stats[0].snr == 42.0
    assert stats[0].clients == 5


# ---------------------------------------------------------------------------
# list_stations
# ---------------------------------------------------------------------------


@respx.mock
def test_list_stations_returns_station_models(client: XiqcClient) -> None:
    _mock_token()
    respx.get(f"{_ROOT}/management/v1/stations/query").mock(
        return_value=httpx.Response(200, json=_fixture("station_list.json"))
    )
    stations = client.list_stations()
    assert len(stations) == 2
    assert all(isinstance(s, Station) for s in stations)
    assert stations[0].mac_address == "02:00:00:aa:bb:01"
    assert stations[0].ip_address == "10.99.1.101"


@respx.mock
def test_list_stations_passes_query_params(client: XiqcClient) -> None:
    _mock_token()
    route = respx.get(f"{_ROOT}/management/v1/stations/query").mock(
        return_value=httpx.Response(200, json=_fixture("station_list.json"))
    )
    client.list_stations(active=False, duration="3D")
    assert route.called
    qs = dict(route.calls.last.request.url.params)
    assert qs["showActive"] == "false"
    assert qs["duration"] == "3D"


# ---------------------------------------------------------------------------
# list_sites
# ---------------------------------------------------------------------------


@respx.mock
def test_list_sites_returns_site_models(client: XiqcClient) -> None:
    _mock_token()
    respx.get(f"{_ROOT}/management/v3/sites").mock(
        return_value=httpx.Response(200, json=_fixture("site_list.json"))
    )
    sites = client.list_sites()
    assert len(sites) == 2
    assert all(isinstance(s, Site) for s in sites)
    assert sites[0].id == "00000000-0000-0000-0000-000000000001"
    assert sites[0].site_name == "Lab Site A"
    assert sites[0].country == "Japan"


# ---------------------------------------------------------------------------
# get_ap_smartrf
# ---------------------------------------------------------------------------


@respx.mock
def test_get_ap_smartrf_returns_model(client: XiqcClient) -> None:
    _mock_token()
    respx.get(f"{_ROOT}/management/v2/aps/LAB-AP-0001/smartrf").mock(
        return_value=httpx.Response(200, json=_fixture("ap_smartrf.json"))
    )
    result = client.get_ap_smartrf("LAB-AP-0001")
    assert isinstance(result, ApSmartRf)
    assert result.serial_number == "LAB-AP-0001"
    assert len(result.radios) == 2
    assert result.radios[0].radio_index == 0
    assert result.radios[0].channel == 6
    assert result.radios[1].channel == 36


@respx.mock
def test_get_ap_smartrf_raises_on_api_error(client: XiqcClient) -> None:
    _mock_token()
    respx.get(f"{_ROOT}/management/v2/aps/LAB-AP-0001/smartrf").mock(
        return_value=httpx.Response(404, text="Not Found")
    )
    with pytest.raises(XiqcAPIError) as exc_info:
        client.get_ap_smartrf("LAB-AP-0001")
    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# get_site_smartrf
# ---------------------------------------------------------------------------


@respx.mock
def test_get_site_smartrf_returns_model(client: XiqcClient) -> None:
    _mock_token()
    site_id = "00000000-0000-0000-0000-000000000001"
    respx.get(f"{_ROOT}/management/v4/sites/{site_id}/smartrf").mock(
        return_value=httpx.Response(200, json=_fixture("site_smartrf.json"))
    )
    result = client.get_site_smartrf(site_id)
    assert isinstance(result, SiteSmartRf)
    assert result.site_id == site_id
    assert result.smartrf_enabled is True


@respx.mock
def test_get_site_smartrf_raises_on_api_error(client: XiqcClient) -> None:
    _mock_token()
    site_id = "00000000-0000-0000-0000-000000000001"
    respx.get(f"{_ROOT}/management/v4/sites/{site_id}/smartrf").mock(
        return_value=httpx.Response(404, text="Not Found")
    )
    with pytest.raises(XiqcAPIError):
        client.get_site_smartrf(site_id)
