from __future__ import annotations

import pytest


@pytest.fixture
def controller_url() -> str:
    return "https://lab-ctrl.example.test:5825/management/v1"
