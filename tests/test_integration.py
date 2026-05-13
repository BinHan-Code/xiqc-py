from __future__ import annotations

import pytest

from xiqc.client import XiqcClient
from xiqc.exceptions import XiqcAPIError
from xiqc.models import Ap, ApSmartRf, ApStats, Site, SiteSmartRf, Station

pytestmark = pytest.mark.integration  # applies to every test in this file


def test_live_list_aps(live_client: XiqcClient) -> None:
    aps = live_client.list_aps()
    assert isinstance(aps, list)
    assert len(aps) > 0, "Lab controller reports no APs — check connectivity"
    assert all(isinstance(ap, Ap) for ap in aps)
    assert all(ap.serial_number for ap in aps)


def test_live_get_ap(live_client: XiqcClient) -> None:
    first_serial = live_client.list_aps()[0].serial_number
    ap = live_client.get_ap(first_serial)
    assert isinstance(ap, Ap)
    assert ap.serial_number == first_serial


def test_live_list_ap_stats(live_client: XiqcClient) -> None:
    stats = live_client.list_ap_stats()
    assert isinstance(stats, list)
    assert all(isinstance(s, ApStats) for s in stats)
    assert all(s.ap_serial for s in stats)


def test_live_list_stations(live_client: XiqcClient) -> None:
    stations = live_client.list_stations()
    assert isinstance(stations, list)
    assert all(isinstance(s, Station) for s in stations)
    # empty list is valid — lab may have no associated clients


def test_live_list_sites(live_client: XiqcClient) -> None:
    sites = live_client.list_sites()
    assert isinstance(sites, list)
    assert len(sites) > 0, "Lab controller reports no sites"
    assert all(isinstance(s, Site) for s in sites)
    assert all(s.id for s in sites)


def test_live_get_ap_smartrf(live_client: XiqcClient) -> None:
    first_serial = live_client.list_aps()[0].serial_number
    try:
        result = live_client.get_ap_smartrf(first_serial)
        assert isinstance(result, ApSmartRf)
        assert result.serial_number == first_serial
    except XiqcAPIError as exc:
        pytest.skip(f"SmartRF not available on this AP ({exc})")


def test_live_get_site_smartrf(live_client: XiqcClient) -> None:
    first_site_id = live_client.list_sites()[0].id
    try:
        result = live_client.get_site_smartrf(first_site_id)
        assert isinstance(result, SiteSmartRf)
        assert result.site_id == first_site_id
    except XiqcAPIError as exc:
        pytest.skip(f"SmartRF not available on this site ({exc})")
