from __future__ import annotations

import pytest

from symref import clear_refs


@pytest.fixture(autouse=True)
def _clear_registry() -> None:
    clear_refs()
