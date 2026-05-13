from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class XiqcModel(BaseModel):
    """Base model for all XIQ-C API responses."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class Radio(XiqcModel):
    """A single radio interface on an AP."""

    radio_index: int = Field(alias="radioIndex")
    mode: str | None = None
    channel_width: str | None = Field(default=None, alias="channelwidth")
    tx_bf: bool | None = Field(default=None, alias="txBf")


class Ap(XiqcModel):
    """AP configuration record from GET /management/v1/aps."""

    serial_number: str = Field(alias="serialNumber")
    ap_name: str | None = Field(default=None, alias="apName")
    host_site: str | None = Field(default=None, alias="hostSite")
    radios: list[Radio] = Field(default_factory=list)


class ApStats(XiqcModel):
    """AP statistics record from the ApTable dataset (/management/v1/aps/query)."""

    ap_serial: str = Field(alias="ApSerial")
    ap_name: str | None = Field(default=None, alias="ApName")
    hw_type: str | None = Field(default=None, alias="HwType")
    ip: str | None = Field(default=None, alias="IP")
    mac: str | None = Field(default=None, alias="MAC")
    sw_version: str | None = Field(default=None, alias="SwVersion")
    site_name: str | None = Field(default=None, alias="SiteName")
    site_uuid: str | None = Field(default=None, alias="SiteUUID")
    location: str | None = Field(default=None, alias="Location")
    is_connected: bool | None = Field(default=None, alias="IsConnected")
    last_update: str | None = Field(default=None, alias="LastUpdate")
    channel_freq: int | None = Field(default=None, alias="ChannelFreq")
    channel_width: int | None = Field(default=None, alias="ChannelWidth")
    channel_utilization: float | None = Field(default=None, alias="ChannelUtilization")
    channel_utilization_adjusted: float | None = Field(
        default=None, alias="ChannelUtilizationAdjusted"
    )
    clear_channel: float | None = Field(default=None, alias="ClearChannel")
    clients: int | None = Field(default=None, alias="Clients")
    noise: float | None = Field(default=None, alias="Noise")
    power: float | None = Field(default=None, alias="Power")
    protocol: str | None = Field(default=None, alias="Protocol")
    radio_index: int | None = Field(default=None, alias="RadioIndex")
    radio_rx_occupancy: float | None = Field(default=None, alias="RadioRxOccupancy")
    rx_occupancy: float | None = Field(default=None, alias="RxOccupancy")
    tx_occupancy: float | None = Field(default=None, alias="TxOccupancy")
    snr: float | None = Field(default=None, alias="SNR")


class Station(XiqcModel):
    """Station (client) record from GET /management/v1/stations/query."""

    mac_address: str = Field(alias="macAddress")
    ip_address: str | None = Field(default=None, alias="ipAddress")


class Site(XiqcModel):
    """Site record from GET /management/v3/sites."""

    id: str
    site_name: str | None = Field(default=None, alias="siteName")
    country: str | None = None
    timezone: str | None = None
    features: dict[str, Any] | None = None


class ApSmartRfRadio(XiqcModel):
    """Per-radio SmartRF assignment from GET /management/v2/aps/{serial}/smartrf."""

    radio_index: int = Field(alias="radioIndex")
    channel: int | None = None
    power: float | None = None
    noise_floor: float | None = Field(default=None, alias="noiseFloor")


class ApSmartRf(XiqcModel):
    """SmartRF state for a single AP from GET /management/v2/aps/{serial}/smartrf."""

    serial_number: str = Field(alias="serialNumber")
    radios: list[ApSmartRfRadio] = Field(default_factory=list)


class SiteSmartRf(XiqcModel):
    """SmartRF configuration for a site from GET /management/v4/sites/{siteId}/smartrf."""

    site_id: str = Field(alias="siteId")
    smartrf_enabled: bool | None = Field(default=None, alias="smartrfEnabled")
