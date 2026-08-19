"""Infraestructura común de los tests.

Cada test corre contra una base de datos SQLite temporal para no tocar nunca la
caché real del usuario, que contiene datos de mercado que costaron cupo de API.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend import store  # noqa: E402


@pytest.fixture()
def db(tmp_path, monkeypatch):
    """Base de datos limpia y aislada por test."""
    path = tmp_path / "test_cache.db"
    monkeypatch.setattr(store, "DB_PATH", path)
    store.init()
    return path


@pytest.fixture()
def serie(db):
    """Inyecta una serie sintética en la caché de test."""

    def _add(metric_id, points, status="ok"):
        store.upsert_series(metric_id, points)
        store.set_metric_state(
            metric_id,
            status=status,
            last_data_point=max(d for d, _ in points),
            ok=status == "ok",
        )

    return _add
