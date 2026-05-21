from __future__ import annotations

import os

import pytest

from xiqc.client import XiqcClient


@pytest.fixture(scope="session")
def live_client() -> XiqcClient:
    """Real XiqcClient built from env vars. Skips the test if XIQC_HOST is not set."""
    host = os.environ.get("XIQC_HOST")
    if not host:
        pytest.skip("XIQC_HOST not set — skipping integration tests")
    return XiqcClient(
        host=host,
        user_id=os.environ["XIQC_USER"],
        password=os.environ["XIQC_PASS"],
        port=int(os.environ.get("XIQC_PORT", "5825")),
        verify=os.environ.get("XIQC_VERIFY", "true").lower()
        not in ("false", "0", "no"),
        timeout=float(os.environ.get("XIQC_TIMEOUT", "30")),
    )
