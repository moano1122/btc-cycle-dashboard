"""Precio de BTC desde Binance.

Binance es gratis y sin cupo práctico, así que todo lo que se pueda derivar del
precio se calcula aquí en vez de gastar peticiones del plan on-chain: medias
móviles, Mayer Multiple, RSI semanal y mensual, y caída desde máximos. Eso
libera unas 6 peticiones diarias del cupo para las métricas que sí son
irremplazables.

Limitación conocida: el par BTCUSDT en Binance arranca en agosto de 2017. Para
la historia anterior se usa el endpoint `btc-price` del proveedor on-chain, que
llega hasta 2009 y solo cuesta una petición. Las dos series se fusionan.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone

import httpx

from .. import store

log = logging.getLogger(__name__)

BINANCE_KLINES = "https://api.binance.com/api/v3/klines"
PRICE_SERIES = "btc_price"


def fetch_binance_daily(start: date | None = None) -> int:
    """Descarga cierres diarios de BTCUSDT y los fusiona en la serie de precio."""
    if start is None:
        start = date(2017, 8, 17)
    start_ms = int(datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc).timestamp() * 1000)

    points: list[tuple[str, float | None]] = []
    cursor = start_ms
    try:
        with httpx.Client(timeout=45.0) as client:
            while True:
                resp = client.get(
                    BINANCE_KLINES,
                    params={
                        "symbol": "BTCUSDT",
                        "interval": "1d",
                        "startTime": cursor,
                        "limit": 1000,
                    },
                )
                resp.raise_for_status()
                rows = resp.json()
                if not rows:
                    break
                for r in rows:
                    open_ms = int(r[0])
                    close = float(r[4])
                    d = datetime.fromtimestamp(open_ms / 1000, tz=timezone.utc).date().isoformat()
                    points.append((d, close))
                if len(rows) < 1000:
                    break
                cursor = int(rows[-1][0]) + 86_400_000
    except Exception as exc:  # noqa: BLE001
        log.warning("Binance falló: %s", exc)
        store.set_metric_state(PRICE_SERIES, status="error", detail=f"binance: {exc}")
        if not points:
            return 0

    if not points:
        return 0

    n = store.upsert_series(PRICE_SERIES, points)
    store.set_metric_state(
        PRICE_SERIES,
        status="ok",
        detail=f"binance {n} puntos",
        last_data_point=max(p[0] for p in points),
        ok=True,
    )
    return n


def fetch_spot_price() -> float | None:
    """Precio actual, para que el encabezado del dashboard no muestre el cierre de ayer."""
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(
                "https://api.binance.com/api/v3/ticker/price", params={"symbol": "BTCUSDT"}
            )
            resp.raise_for_status()
            return float(resp.json()["price"])
    except Exception as exc:  # noqa: BLE001
        log.warning("precio spot no disponible: %s", exc)
        return None


def incremental_update() -> int:
    """Solo trae lo que falta desde el último dato guardado."""
    latest = store.get_latest(PRICE_SERIES)
    if not latest:
        return fetch_binance_daily()
    try:
        last = date.fromisoformat(latest["d"])
    except ValueError:
        return fetch_binance_daily()
    return fetch_binance_daily(start=last - timedelta(days=2))
