from __future__ import annotations

__version__ = "0.1.0"

from xiqc.auth import AuthClient
from xiqc.client import XiqcClient
from xiqc.exceptions import XiqcAPIError, XiqcAuthError, XiqcConnectionError, XiqcError
from xiqc.models import Ap, ApSmartRf, ApSmartRfRadio, ApStats, Radio, Site, SiteSmartRf, Station

__all__ = [
    "__version__",
    "AuthClient",
    "XiqcClient",
    "XiqcError",
    "XiqcAuthError",
    "XiqcAPIError",
    "XiqcConnectionError",
    "Ap",
    "ApSmartRf",
    "ApSmartRfRadio",
    "ApStats",
    "Radio",
    "Site",
    "SiteSmartRf",
    "Station",
]
