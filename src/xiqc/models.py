from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class XiqcModel(BaseModel):
    """Base model for all XIQ-C API responses."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class Radio(XiqcModel):
    """A single radio interface on an AP."""

    radio_index: int = Field(alias="radioIndex")
    mode: str | None = None
    channel_width: str | None = Field(default=None, alias="channelwidth")
    tx_bf: bool | None = Field(default=None, alias="txBf")

    @field_validator("tx_bf", mode="before")
    @classmethod
    def _coerce_tx_bf(cls, v: object) -> object:
        # API returns "enabled"/"disabled" strings instead of booleans.
        if isinstance(v, str):
            return v.lower() not in ("disabled", "false", "0", "no")
        return v


class Ap(XiqcModel):
    """AP configuration record from GET /management/v1/aps."""

    serial_number: str = Field(alias="serialNumber")
    ap_name: str | None = Field(default=None, alias="apName")
    host_site: str | None = Field(default=None, alias="hostSite")
    radios: list[Radio] = Field(default_factory=list)


class ApStats(XiqcModel):
    """AP statistics record from GET /management/v1/aps/query."""

    ap_serial: str = Field(alias="serialNumber")
    ap_name: str | None = Field(default=None, alias="apName")
    hw_type: str | None = Field(default=None, alias="hardwareType")
    ip: str | None = Field(default=None, alias="ipAddress")
    mac: str | None = Field(default=None, alias="macAddress")
    sw_version: str | None = Field(default=None, alias="swVersion")
    site_name: str | None = Field(default=None, alias="siteName")
    site_uuid: str | None = Field(default=None, alias="siteUuid")
    location: str | None = Field(default=None, alias="location")
    is_connected: bool | None = Field(default=None, alias="isConnected")
    last_update: str | None = Field(default=None, alias="lastUpdate")
    channel_freq: int | None = Field(default=None, alias="channelFreq")
    channel_width: int | None = Field(default=None, alias="channelWidth")
    channel_utilization: float | None = Field(default=None, alias="channelUtilization")
    channel_utilization_adjusted: float | None = Field(
        default=None, alias="channelUtilizationAdjusted"
    )
    clear_channel: float | None = Field(default=None, alias="clearChannel")
    clients: int | None = Field(default=None, alias="clients")
    noise: float | None = Field(default=None, alias="noise")
    power: float | None = Field(default=None, alias="power")
    protocol: str | None = Field(default=None, alias="protocol")
    radio_index: int | None = Field(default=None, alias="radioIndex")
    radio_rx_occupancy: float | None = Field(default=None, alias="radioRxOccupancy")
    rx_occupancy: float | None = Field(default=None, alias="rxOccupancy")
    tx_occupancy: float | None = Field(default=None, alias="txOccupancy")
    snr: float | None = Field(default=None, alias="snr")


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
    features: list[str] | None = None


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
    """SmartRF configuration for a site from GET /management/v4/sites/{id}/smartrf."""

    site_id: str = Field(alias="siteId")
    smartrf_enabled: bool | None = Field(default=None, alias="smartrfEnabled")
