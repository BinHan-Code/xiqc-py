from __future__ import annotations

import logging
import time

import httpx

logger = logging.getLogger(__name__)

_MIN_INTERVAL = 0.5  # enforces ≤ 2 req/s per controller
_last_call: float = 0.0


def _throttle() -> None:
    global _last_call
    elapsed = time.monotonic() - _last_call
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _last_call = time.monotonic()


def build_client(verify: bool, timeout: float = 30.0) -> httpx.Client:
    """Return a configured httpx.Client with optional TLS verification."""
    if not verify:
        logger.warning(
            "TLS verification is DISABLED — do not use this setting in production."
        )
    return httpx.Client(verify=verify, timeout=timeout)
