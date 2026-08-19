"""Almacén SQLite: series históricas, estado de refresco, presupuesto de API,
configuración de pesos e historial de alertas.

El dashboard SIEMPRE lee de aquí y nunca de la red. Si la API está caída o el
cupo agotado, la herramienta sigue funcionando con el último dato bueno y lo
marca como rancio. Esa separación es deliberada: una decisión de compra no
debe depender de que un proveedor externo responda en ese instante.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterable

from .config import DB_PATH

_LOCK = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS series (
    metric_id TEXT NOT NULL,
    d         TEXT NOT NULL,          -- fecha ISO YYYY-MM-DD
    value     REAL,
    PRIMARY KEY (metric_id, d)
);

CREATE TABLE IF NOT EXISTS metric_state (
    metric_id       TEXT PRIMARY KEY,
    last_fetch_utc  TEXT,             -- cuándo intentamos por última vez
    last_ok_utc     TEXT,             -- cuándo lo logramos por última vez
    last_data_point TEXT,             -- fecha del dato más reciente que tenemos
    status          TEXT,             -- ok | error | never
    detail          TEXT
);

CREATE TABLE IF NOT EXISTS api_calls (
    ts_utc    TEXT NOT NULL,
    provider  TEXT NOT NULL,
    endpoint  TEXT,
    ok        INTEGER
);
CREATE INDEX IF NOT EXISTS idx_api_calls_ts ON api_calls (provider, ts_utc);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS alert_events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_utc     TEXT NOT NULL,
    metric_id  TEXT,
    kind       TEXT,                  -- cross_in | cross_out | score_band
    severity   TEXT,                  -- info | warn | signal
    title      TEXT,
    message    TEXT,
    value      REAL,
    delivered  INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS alert_state (
    key        TEXT PRIMARY KEY,      -- p.ej. "mvrv_zscore:triggered"
    value      TEXT,
    updated_utc TEXT
);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


@contextmanager
def db():
    with _LOCK:
        conn = _connect()
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()


def init() -> None:
    with db() as conn:
        conn.executescript(SCHEMA)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --------------------------------------------------------------------------
# Series
# --------------------------------------------------------------------------
def upsert_series(metric_id: str, points: Iterable[tuple[str, float | None]]) -> int:
    rows = [(metric_id, d, v) for d, v in points if d]
    if not rows:
        return 0
    with db() as conn:
        conn.executemany(
            "INSERT INTO series (metric_id, d, value) VALUES (?, ?, ?) "
            "ON CONFLICT(metric_id, d) DO UPDATE SET value = excluded.value",
            rows,
        )
    return len(rows)


def replace_series(metric_id: str, points: Iterable[tuple[str, float | None]]) -> int:
    """Sustituye una serie entera en lugar de fusionarla.

    `upsert_series` nunca borra, que es lo correcto para datos que solo crecen.
    Pero cuando cambia la DEFINICIÓN de un indicador derivado —por ejemplo al
    excluir un periodo de arranque cuyos porcentajes eran un artefacto— los
    puntos viejos sobrevivirían y seguirían contaminando la calibración.
    """
    rows = [(metric_id, d, v) for d, v in points if d]
    with db() as conn:
        conn.execute("DELETE FROM series WHERE metric_id = ?", (metric_id,))
        if rows:
            conn.executemany(
                "INSERT INTO series (metric_id, d, value) VALUES (?, ?, ?)", rows
            )
    return len(rows)


def get_series(metric_id: str, since: str | None = None) -> list[dict[str, Any]]:
    sql = "SELECT d, value FROM series WHERE metric_id = ?"
    params: list[Any] = [metric_id]
    if since:
        sql += " AND d >= ?"
        params.append(since)
    sql += " ORDER BY d ASC"
    with db() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def get_latest(metric_id: str) -> dict[str, Any] | None:
    with db() as conn:
        row = conn.execute(
            "SELECT d, value FROM series WHERE metric_id = ? AND value IS NOT NULL "
            "ORDER BY d DESC LIMIT 1",
            (metric_id,),
        ).fetchone()
    return dict(row) if row else None


def get_latest_many(metric_ids: Iterable[str]) -> dict[str, dict[str, Any]]:
    """Un solo query para todos los últimos valores: evita N roundtrips."""
    ids = list(metric_ids)
    if not ids:
        return {}
    placeholders = ",".join("?" * len(ids))
    sql = f"""
        SELECT s.metric_id, s.d, s.value
        FROM series s
        JOIN (
            SELECT metric_id, MAX(d) AS md
            FROM series
            WHERE metric_id IN ({placeholders}) AND value IS NOT NULL
            GROUP BY metric_id
        ) m ON m.metric_id = s.metric_id AND m.md = s.d
    """
    with db() as conn:
        rows = conn.execute(sql, ids).fetchall()
    return {r["metric_id"]: {"d": r["d"], "value": r["value"]} for r in rows}


def series_span(metric_id: str) -> tuple[str | None, str | None, int]:
    with db() as conn:
        row = conn.execute(
            "SELECT MIN(d) a, MAX(d) b, COUNT(*) n FROM series WHERE metric_id = ?",
            (metric_id,),
        ).fetchone()
    return (row["a"], row["b"], row["n"]) if row else (None, None, 0)


# --------------------------------------------------------------------------
# Estado de cada métrica
# --------------------------------------------------------------------------
def set_metric_state(
    metric_id: str,
    *,
    status: str,
    detail: str = "",
    last_data_point: str | None = None,
    ok: bool = False,
) -> None:
    ts = now_utc()
    with db() as conn:
        prev = conn.execute(
            "SELECT last_ok_utc, last_data_point FROM metric_state WHERE metric_id = ?",
            (metric_id,),
        ).fetchone()
        last_ok = ts if ok else (prev["last_ok_utc"] if prev else None)
        ldp = last_data_point or (prev["last_data_point"] if prev else None)
        conn.execute(
            "INSERT INTO metric_state (metric_id, last_fetch_utc, last_ok_utc, "
            "last_data_point, status, detail) VALUES (?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(metric_id) DO UPDATE SET last_fetch_utc=excluded.last_fetch_utc, "
            "last_ok_utc=excluded.last_ok_utc, last_data_point=excluded.last_data_point, "
            "status=excluded.status, detail=excluded.detail",
            (metric_id, ts, last_ok, ldp, status, detail),
        )


def get_metric_states() -> dict[str, dict[str, Any]]:
    with db() as conn:
        rows = conn.execute("SELECT * FROM metric_state").fetchall()
    return {r["metric_id"]: dict(r) for r in rows}


# --------------------------------------------------------------------------
# Presupuesto de llamadas a la API
# --------------------------------------------------------------------------
def record_call(provider: str, endpoint: str, ok: bool) -> None:
    with db() as conn:
        conn.execute(
            "INSERT INTO api_calls (ts_utc, provider, endpoint, ok) VALUES (?, ?, ?, ?)",
            (now_utc(), provider, endpoint, 1 if ok else 0),
        )
        # Poda: el presupuesto solo mira 24h atrás, no hace falta guardar más.
        cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        conn.execute("DELETE FROM api_calls WHERE ts_utc < ?", (cutoff,))


def calls_used(provider: str) -> tuple[int, int]:
    """Devuelve (llamadas en la última hora, llamadas en las últimas 24h)."""
    now = datetime.now(timezone.utc)
    h_cut = (now - timedelta(hours=1)).isoformat()
    d_cut = (now - timedelta(hours=24)).isoformat()
    with db() as conn:
        h = conn.execute(
            "SELECT COUNT(*) c FROM api_calls WHERE provider = ? AND ts_utc >= ?",
            (provider, h_cut),
        ).fetchone()["c"]
        d = conn.execute(
            "SELECT COUNT(*) c FROM api_calls WHERE provider = ? AND ts_utc >= ?",
            (provider, d_cut),
        ).fetchone()["c"]
    return h, d


# --------------------------------------------------------------------------
# Settings (pesos, umbrales personalizados)
# --------------------------------------------------------------------------
def get_setting(key: str, default: Any = None) -> Any:
    with db() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    if not row:
        return default
    try:
        return json.loads(row["value"])
    except (TypeError, ValueError):
        return default


def set_setting(key: str, value: Any) -> None:
    with db() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, json.dumps(value)),
        )


# --------------------------------------------------------------------------
# Alertas
# --------------------------------------------------------------------------
def add_alert_event(
    *,
    metric_id: str | None,
    kind: str,
    severity: str,
    title: str,
    message: str,
    value: float | None,
) -> int:
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO alert_events (ts_utc, metric_id, kind, severity, title, "
            "message, value) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (now_utc(), metric_id, kind, severity, title, message, value),
        )
        return int(cur.lastrowid)


def mark_delivered(event_id: int) -> None:
    with db() as conn:
        conn.execute("UPDATE alert_events SET delivered = 1 WHERE id = ?", (event_id,))


def recent_alerts(limit: int = 50) -> list[dict[str, Any]]:
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM alert_events ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_alert_state(key: str) -> str | None:
    with db() as conn:
        row = conn.execute("SELECT value FROM alert_state WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def set_alert_state(key: str, value: str) -> None:
    with db() as conn:
        conn.execute(
            "INSERT INTO alert_state (key, value, updated_utc) VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value, "
            "updated_utc = excluded.updated_utc",
            (key, value, now_utc()),
        )


def days_since(iso_date: str | None) -> int | None:
    if not iso_date:
        return None
    try:
        d = date.fromisoformat(iso_date[:10])
    except ValueError:
        return None
    return (datetime.now(timezone.utc).date() - d).days
