"""Pytest fixtures: every test gets a fresh state dir + fresh lineage DB."""

from __future__ import annotations

from pathlib import Path

import pytest

from ferryte import config as _config_module
from ferryte import instrument as _instrument_module
from ferryte import registry as _registry_module
from ferryte.lineage import graph as _graph_module


@pytest.fixture(autouse=True)
def fresh_ferryte(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("FERRYTE_STATE_DIR", str(tmp_path / "state"))
    _config_module._config = None
    _graph_module.reset_lineage_for_tests()
    _instrument_module._handle = None
    _instrument_module._installed = False
    _registry_module.clear_for_tests()
    yield tmp_path
    _instrument_module._handle = None
    _instrument_module._installed = False
    _graph_module.reset_lineage_for_tests()
    _config_module._config = None
