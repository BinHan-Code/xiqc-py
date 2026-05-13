from __future__ import annotations

import json
import os
from enum import Enum
from typing import Any, Union

import typer

from xiqc.client import XiqcClient
from xiqc.exceptions import XiqcAPIError, XiqcAuthError, XiqcConnectionError

app = typer.Typer(help="XIQ-C command-line interface.")
aps_app = typer.Typer(help="AP commands.")
stations_app = typer.Typer(help="Station commands.")
sites_app = typer.Typer(help="Site commands.")

app.add_typer(aps_app, name="aps")
app.add_typer(stations_app, name="stations")
app.add_typer(sites_app, name="sites")


class _Fmt(str, Enum):
    json = "json"
    table = "table"


def _make_client() -> XiqcClient:
    host = os.environ.get("XIQC_HOST")
    user = os.environ.get("XIQC_USER")
    password = os.environ.get("XIQC_PASS")
    missing = [n for n, v in (("XIQC_HOST", host), ("XIQC_USER", user), ("XIQC_PASS", password)) if not v]
    if missing:
        typer.echo(f"Error: {', '.join(missing)} must be set.", err=True)
        raise typer.Exit(1)
    assert host and user and password  # narrowing for mypy
    port = int(os.environ.get("XIQC_PORT", "5825"))
    verify_str = os.environ.get("XIQC_VERIFY", "true").lower()
    verify = verify_str not in ("false", "0", "no")
    if not verify:
        typer.echo("Warning: TLS verification is disabled (XIQC_VERIFY=false).", err=True)
    timeout = float(os.environ.get("XIQC_TIMEOUT", "30"))
    return XiqcClient(host=host, user_id=user, password=password, port=port, verify=verify, timeout=timeout)


_XiqcErrors = Union[XiqcAuthError, XiqcAPIError, XiqcConnectionError]


def _exit_on_error(exc: _XiqcErrors) -> None:
    typer.echo(f"Error: {exc}", err=True)
    if isinstance(exc, XiqcAuthError):
        raise typer.Exit(1)
    if isinstance(exc, XiqcAPIError):
        raise typer.Exit(2)
    raise typer.Exit(3)


def _print_json(data: Any) -> None:
    typer.echo(json.dumps(data, indent=2))


def _table(rows: list[list[str]], headers: list[str]) -> str:
    all_rows = [headers] + rows
    widths = [max(len(r[i]) for r in all_rows) for i in range(len(headers))]
    lines = ["  ".join(h.ljust(widths[i]) for i, h in enumerate(row)) for row in all_rows]
    lines.insert(1, "  ".join("-" * w for w in widths))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# aps
# ---------------------------------------------------------------------------


@aps_app.command("list")
def aps_list(
    fmt: _Fmt = typer.Option(_Fmt.table, "--format", "-f", help="Output format."),
) -> None:
    """List all adopted APs."""
    try:
        aps = _make_client().list_aps()
    except (XiqcAuthError, XiqcAPIError, XiqcConnectionError) as exc:
        _exit_on_error(exc)
        return
    if fmt == _Fmt.json:
        _print_json([ap.model_dump(by_alias=False) for ap in aps])
    else:
        rows = [[ap.serial_number, ap.ap_name or "", ap.host_site or ""] for ap in aps]
        typer.echo(_table(rows, ["SERIAL", "NAME", "SITE"]))


@aps_app.command("report")
def aps_report(
    serial: str = typer.Option(..., "--serial", "-s", help="AP serial number."),
    fmt: _Fmt = typer.Option(_Fmt.table, "--format", "-f", help="Output format."),
) -> None:
    """Show configuration details for a single AP."""
    try:
        ap = _make_client().get_ap(serial)
    except (XiqcAuthError, XiqcAPIError, XiqcConnectionError) as exc:
        _exit_on_error(exc)
        return
    if fmt == _Fmt.json:
        _print_json(ap.model_dump(by_alias=False))
    else:
        rows = [
            ["Serial", ap.serial_number],
            ["Name", ap.ap_name or ""],
            ["Site", ap.host_site or ""],
            ["Radios", str(len(ap.radios))],
        ]
        typer.echo(_table(rows, ["Field", "Value"]))


# ---------------------------------------------------------------------------
# stations
# ---------------------------------------------------------------------------


@stations_app.command("list")
def stations_list(
    active: bool = typer.Option(True, help="Show only currently associated stations."),
    duration: str = typer.Option("3H", help="Time window: 3H, 3D, or 14D."),
    fmt: _Fmt = typer.Option(_Fmt.table, "--format", "-f", help="Output format."),
) -> None:
    """List stations (Wi-Fi clients)."""
    try:
        stations = _make_client().list_stations(active=active, duration=duration)
    except (XiqcAuthError, XiqcAPIError, XiqcConnectionError) as exc:
        _exit_on_error(exc)
        return
    if fmt == _Fmt.json:
        _print_json([s.model_dump(by_alias=False) for s in stations])
    else:
        rows = [[s.mac_address, s.ip_address or ""] for s in stations]
        typer.echo(_table(rows, ["MAC", "IP"]))


# ---------------------------------------------------------------------------
# sites
# ---------------------------------------------------------------------------


@sites_app.command("list")
def sites_list(
    fmt: _Fmt = typer.Option(_Fmt.table, "--format", "-f", help="Output format."),
) -> None:
    """List all sites."""
    try:
        sites = _make_client().list_sites()
    except (XiqcAuthError, XiqcAPIError, XiqcConnectionError) as exc:
        _exit_on_error(exc)
        return
    if fmt == _Fmt.json:
        _print_json([s.model_dump(by_alias=False) for s in sites])
    else:
        rows = [[s.id, s.site_name or "", s.country or "", s.timezone or ""] for s in sites]
        typer.echo(_table(rows, ["ID", "NAME", "COUNTRY", "TIMEZONE"]))


@aps_app.command("smartrf")
def aps_smartrf(
    serial: str = typer.Option(..., "--serial", "-s", help="AP serial number."),
    fmt: _Fmt = typer.Option(_Fmt.table, "--format", "-f", help="Output format."),
) -> None:
    """Show SmartRF channel/power assignments for an AP."""
    try:
        result = _make_client().get_ap_smartrf(serial)
    except (XiqcAuthError, XiqcAPIError, XiqcConnectionError) as exc:
        _exit_on_error(exc)
        return
    if fmt == _Fmt.json:
        _print_json(result.model_dump(by_alias=False))
    else:
        rows = [
            [str(r.radio_index), str(r.channel or ""), str(r.power or ""), str(r.noise_floor or "")]
            for r in result.radios
        ]
        typer.echo(_table(rows, ["RADIO", "CHANNEL", "POWER", "NOISE FLOOR"]))


@sites_app.command("smartrf")
def sites_smartrf(
    site_id: str = typer.Option(..., "--id", help="Site UUID."),
    fmt: _Fmt = typer.Option(_Fmt.table, "--format", "-f", help="Output format."),
) -> None:
    """Show SmartRF configuration for a site."""
    try:
        result = _make_client().get_site_smartrf(site_id)
    except (XiqcAuthError, XiqcAPIError, XiqcConnectionError) as exc:
        _exit_on_error(exc)
        return
    if fmt == _Fmt.json:
        _print_json(result.model_dump(by_alias=False))
    else:
        rows = [
            ["Site ID", result.site_id],
            ["SmartRF Enabled", str(result.smartrf_enabled)],
        ]
        typer.echo(_table(rows, ["Field", "Value"]))


def main() -> None:
    """Entry point for the xiqc CLI."""
    app()
