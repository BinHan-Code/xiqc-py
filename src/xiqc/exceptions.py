from __future__ import annotations


class XiqcError(Exception):
    """Base exception for xiqc."""


class XiqcAuthError(XiqcError):
    """Authentication or authorization failure."""


class XiqcAPIError(XiqcError):
    """Non-2xx response from the XIQ-C API."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}: {message}")


class XiqcConnectionError(XiqcError):
    """Network-level failure reaching the controller."""
