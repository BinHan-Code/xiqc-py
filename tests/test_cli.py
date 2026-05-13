from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import respx
from typer.testing import CliRunner

from xiqc.cli import app

_HOST = "lab-ctrl.example.test"
_ROOT = f"https://{_HOST}:5825"
_MGMT_V1 = "/management/v1"
_TOKEN_URL = f"{_ROOT}{_MGMT_V1}/oauth2/token"
_TOKEN_RESPONSE = {
    "access_token": "fake-access-token",
    "refresh_token": "fake-refresh-token",
    "expires_in": 7200,
}
_XIQC_ENV = {
    "XIQC_HOST": _HOST,
    "XIQC_USER": "admin",
    "XIQC_PASS": "secret",
}

_FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> dict:  # type: ignore[type-arg]
    return json.loads((_FIXTURES / name).read_text())


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def _mock_token() -> None:
    respx.post(_TOKEN_URL).mock(return_value=httpx.Response(200, json=_TOKEN_RESPONSE))


# ---------------------------------------------------------------------------
# aps list
# ---------------------------------------------------------------------------


@respx.mock
def test_aps_list_table_shows_serials(runner: CliRunner) -> None:
    _mock_token()
    respx.get(f"{_ROOT}/management/v1/aps").mock(
        return_value=httpx.Response(200, json=_fixture("ap_list.json"))
    )
    result = runner.invoke(app, ["aps", "list"], env=_XIQC_ENV)
    assert result.exit_code == 0
    assert "LAB-AP-0001" in result.output
    assert "LAB-AP-0002" in result.output
    assert "SERIAL" in result.output


@respx.mock
def test_aps_list_json_output(runner: CliRunner) -> None:
    _mock_token()
    respx.get(f"{_ROOT}/management/v1/aps").mock(
        return_value=httpx.Response(200, json=_fixture("ap_list.json"))
    )
    result = runner.invoke(app, ["aps", "list", "--format", "json"], env=_XIQC_ENV)
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 2
    serials = [item["serial_number"] for item in data]
    assert "LAB-AP-0001" in serials


def test_aps_list_missing_env_exits_1(runner: CliRunner) -> None:
    result = runner.invoke(app, ["aps", "list"], env={"XIQC_HOST": _HOST})
    assert result.exit_code == 1


@respx.mock
def test_aps_list_api_error_exits_2(runner: CliRunner) -> None:
    _mock_token()
    respx.get(f"{_ROOT}/management/v1/aps").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )
    result = runner.invoke(app, ["aps", "list"], env=_XIQC_ENV)
    assert result.exit_code == 2


@respx.mock
def test_aps_list_connection_error_exits_3(runner: CliRunner) -> None:
    _mock_token()
    respx.get(f"{_ROOT}/management/v1/aps").mock(
        side_effect=httpx.ConnectError("refused")
    )
    result = runner.invoke(app, ["aps", "list"], env=_XIQC_ENV)
    assert result.exit_code == 3


# ---------------------------------------------------------------------------
# aps report
# ---------------------------------------------------------------------------


@respx.mock
def test_aps_report_table_shows_serial(runner: CliRunner) -> None:
    _mock_token()
    ap_data = _fixture("ap_list.json")["data"][0]
    respx.get(f"{_ROOT}/management/v1/aps/LAB-AP-0001").mock(
        return_value=httpx.Response(200, json=ap_data)
    )
    result = runner.invoke(app, ["aps", "report", "--serial", "LAB-AP-0001"], env=_XIQC_ENV)
    assert result.exit_code == 0
    assert "LAB-AP-0001" in result.output
    assert "Serial" in result.output


@respx.mock
def test_aps_report_json_output(runner: CliRunner) -> None:
    _mock_token()
    ap_data = _fixture("ap_list.json")["data"][0]
    respx.get(f"{_ROOT}/management/v1/aps/LAB-AP-0001").mock(
        return_value=httpx.Response(200, json=ap_data)
    )
    result = runner.invoke(
        app, ["aps", "report", "--serial", "LAB-AP-0001", "--format", "json"], env=_XIQC_ENV
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["serial_number"] == "LAB-AP-0001"


def test_aps_report_missing_serial_exits(runner: CliRunner) -> None:
    result = runner.invoke(app, ["aps", "report"], env=_XIQC_ENV)
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# stations list
# ---------------------------------------------------------------------------


@respx.mock
def test_stations_list_table_shows_macs(runner: CliRunner) -> None:
    _mock_token()
    respx.get(f"{_ROOT}/management/v1/stations/query").mock(
        return_value=httpx.Response(200, json=_fixture("station_list.json"))
    )
    result = runner.invoke(app, ["stations", "list"], env=_XIQC_ENV)
    assert result.exit_code == 0
    assert "02:00:00:aa:bb:01" in result.output
    assert "MAC" in result.output


@respx.mock
def test_stations_list_forwards_active_and_duration(runner: CliRunner) -> None:
    _mock_token()
    route = respx.get(f"{_ROOT}/management/v1/stations/query").mock(
        return_value=httpx.Response(200, json=_fixture("station_list.json"))
    )
    result = runner.invoke(
        app, ["stations", "list", "--no-active", "--duration", "3D"], env=_XIQC_ENV
    )
    assert result.exit_code == 0
    params = dict(route.calls.last.request.url.params)
    assert params["showActive"] == "false"
    assert params["duration"] == "3D"


# ---------------------------------------------------------------------------
# sites list
# ---------------------------------------------------------------------------


@respx.mock
def test_sites_list_table_shows_names(runner: CliRunner) -> None:
    _mock_token()
    respx.get(f"{_ROOT}/management/v3/sites").mock(
        return_value=httpx.Response(200, json=_fixture("site_list.json"))
    )
    result = runner.invoke(app, ["sites", "list"], env=_XIQC_ENV)
    assert result.exit_code == 0
    assert "Lab Site A" in result.output
    assert "Lab Site B" in result.output
    assert "NAME" in result.output


@respx.mock
def test_sites_list_json_output(runner: CliRunner) -> None:
    _mock_token()
    respx.get(f"{_ROOT}/management/v3/sites").mock(
        return_value=httpx.Response(200, json=_fixture("site_list.json"))
    )
    result = runner.invoke(app, ["sites", "list", "--format", "json"], env=_XIQC_ENV)
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["site_name"] == "Lab Site A"


# ---------------------------------------------------------------------------
# aps smartrf
# ---------------------------------------------------------------------------


@respx.mock
def test_aps_smartrf_table_shows_channels(runner: CliRunner) -> None:
    _mock_token()
    respx.get(f"{_ROOT}/management/v2/aps/LAB-AP-0001/smartrf").mock(
        return_value=httpx.Response(200, json=_fixture("ap_smartrf.json"))
    )
    result = runner.invoke(app, ["aps", "smartrf", "--serial", "LAB-AP-0001"], env=_XIQC_ENV)
    assert result.exit_code == 0
    assert "6" in result.output   # channel for radio 0
    assert "36" in result.output  # channel for radio 1
    assert "CHANNEL" in result.output


@respx.mock
def test_aps_smartrf_json_output(runner: CliRunner) -> None:
    _mock_token()
    respx.get(f"{_ROOT}/management/v2/aps/LAB-AP-0001/smartrf").mock(
        return_value=httpx.Response(200, json=_fixture("ap_smartrf.json"))
    )
    result = runner.invoke(
        app, ["aps", "smartrf", "--serial", "LAB-AP-0001", "--format", "json"], env=_XIQC_ENV
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["serial_number"] == "LAB-AP-0001"
    assert len(data["radios"]) == 2


@respx.mock
def test_aps_smartrf_api_error_exits_2(runner: CliRunner) -> None:
    _mock_token()
    respx.get(f"{_ROOT}/management/v2/aps/LAB-AP-0001/smartrf").mock(
        return_value=httpx.Response(404, text="Not Found")
    )
    result = runner.invoke(app, ["aps", "smartrf", "--serial", "LAB-AP-0001"], env=_XIQC_ENV)
    assert result.exit_code == 2


# ---------------------------------------------------------------------------
# sites smartrf
# ---------------------------------------------------------------------------


@respx.mock
def test_sites_smartrf_table_shows_enabled(runner: CliRunner) -> None:
    _mock_token()
    site_id = "00000000-0000-0000-0000-000000000001"
    respx.get(f"{_ROOT}/management/v4/sites/{site_id}/smartrf").mock(
        return_value=httpx.Response(200, json=_fixture("site_smartrf.json"))
    )
    result = runner.invoke(app, ["sites", "smartrf", "--id", site_id], env=_XIQC_ENV)
    assert result.exit_code == 0
    assert site_id in result.output
    assert "True" in result.output


@respx.mock
def test_sites_smartrf_json_output(runner: CliRunner) -> None:
    _mock_token()
    site_id = "00000000-0000-0000-0000-000000000001"
    respx.get(f"{_ROOT}/management/v4/sites/{site_id}/smartrf").mock(
        return_value=httpx.Response(200, json=_fixture("site_smartrf.json"))
    )
    result = runner.invoke(
        app, ["sites", "smartrf", "--id", site_id, "--format", "json"], env=_XIQC_ENV
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["site_id"] == site_id
    assert data["smartrf_enabled"] is True
