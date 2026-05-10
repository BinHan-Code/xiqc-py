from __future__ import annotations

from pydantic import BaseModel


class XiqcModel(BaseModel):
    """Base model for all XIQ-C API responses."""

    model_config = {"extra": "ignore"}
