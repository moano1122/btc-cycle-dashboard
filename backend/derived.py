"""Indicadores calculados localmente.

Todo lo que se pueda derivar de series ya en caché se calcula aquí, sin gastar
cupo de la API. Implementado en Python puro a propósito: sin pandas ni numpy,
para que la instalación sea trivial y no dependa de ruedas compiladas.
"""

from __future__ import annotations

import logging
from datetime import date

from . import store

log = logging.getLogger(__name__)

PRICE = "btc_price"


# --------------------------------------------------------------------------
# Utilidades numéricas
# --------------------------------------------------------------------------
def sma(values: list[float], window: int) -> list[float | None]:
    out: list[float | None] = []
    total = 0.0
    for i, v in enumerate(values):
        total += v
        if i >= window:
            total -= values[i - window]
        out.append(total / window if i >= window - 1 else None)
    return out


def wilder_rsi(closes: list[float], period: int = 14) -> list[float | None]:
    """RSI de Wilder, el que usan TradingView y la convención estándar."""
    n = len(closes)
    out: list[float | None] = [None] * n
    if n <= period:
        return out

    gains = losses = 0.0
    for i in range(1, period + 1):
        ch = closes[i] - closes[i - 1]
        gains += max(ch, 0.0)
        losses += max(-ch, 0.0)
    avg_gain = gains / period
    avg_loss = losses / period

    def rsi_from(g: float, l: float) -> float:
        if l == 0:
            return 100.0
        rs = g / l
        return 100.0 - (100.0 / (1.0 + rs))

    out[period] = rsi_from(avg_gain, avg_loss)
    for i in range(period + 1, n):
        ch = closes[i] - closes[i - 1]
        gain = max(ch, 0.0)
        loss = max(-ch, 0.0)
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        out[i] = rsi_from(avg_gain, avg_loss)
    return out


def _period_closes(points: list[dict], mode: str) -> list[tuple[str, float]]:
    """Reduce una serie diaria al último cierre de cada semana o mes."""
    buckets: dict[str, tuple[str, float]] = {}
    for p in points:
        if p["value"] is None:
            continue
        d = date.fromisoformat(p["d"])
        if mode == "weekly":
            iso = d.isocalendar()
            key = f"{iso.year}-W{iso.week:02d}"
        else:
            key = f"{d.year}-{d.month:02d}"
        prev = buckets.get(key)
        if prev is None or p["d"] > prev[0]:
            buckets[key] = (p["d"], float(p["value"]))
    return [buckets[k] for k in sorted(buckets)]


def _align(a: list[dict], b: list[dict]) -> list[tuple[str, float, float]]:
    """Une dos series por fecha, quedándose solo con las fechas presentes en ambas."""
    bm = {p["d"]: p["value"] for p in b if p["value"] is not None}
    out = []
    for p in a:
        if p["value"] is None:
            continue
        other = bm.get(p["d"])
        if other not in (None, 0):
            out.append((p["d"], float(p["value"]), float(other)))
    return out


# --------------------------------------------------------------------------
# Cálculo de cada indicador derivado
# --------------------------------------------------------------------------
def _ratio_series(target_id: str, numerator_id: str, denominator_id: str) -> int:
    num = store.get_series(numerator_id)
    den = store.get_series(denominator_id)
    pairs = _align(num, den)
    if not pairs:
        store.set_metric_state(
            target_id, status="error", detail=f"faltan datos de {numerator_id} o {denominator_id}"
        )
        return 0
    points = [(d, n / dd) for d, n, dd in pairs]
    store.upsert_series(target_id, points)
    store.set_metric_state(
        target_id, status="ok", detail="derivado", last_data_point=points[-1][0], ok=True
    )
    return len(points)


def _moving_average_ratio(target_id: str, window_days: int) -> int:
    pts = [p for p in store.get_series(PRICE) if p["value"] is not None]
    if len(pts) < window_days:
        store.set_metric_state(
            target_id,
            status="error",
            detail=f"hacen falta {window_days} días de precio, hay {len(pts)}",
        )
        return 0
    closes = [float(p["value"]) for p in pts]
    ma = sma(closes, window_days)
    points = [
        (pts[i]["d"], closes[i] / ma[i])
        for i in range(len(pts))
        if ma[i] not in (None, 0)
    ]
    store.upsert_series(target_id, points)
    store.set_metric_state(
        target_id, status="ok", detail="derivado", last_data_point=points[-1][0], ok=True
    )
    return len(points)


def _rsi(target_id: str, mode: str) -> int:
    pts = store.get_series(PRICE)
    closes = _period_closes(pts, mode)
    if len(closes) < 20:
        store.set_metric_state(target_id, status="error", detail="historia insuficiente")
        return 0
    values = [c for _, c in closes]
    rsi = wilder_rsi(values, 14)
    points = [(closes[i][0], rsi[i]) for i in range(len(closes)) if rsi[i] is not None]
    if not points:
        store.set_metric_state(target_id, status="error", detail="RSI vacío")
        return 0
    store.upsert_series(target_id, points)
    store.set_metric_state(
        target_id, status="ok", detail="derivado", last_data_point=points[-1][0], ok=True
    )
    return len(points)


def _drawdown() -> int:
    pts = [p for p in store.get_series(PRICE) if p["value"] is not None]
    if not pts:
        store.set_metric_state("drawdown_from_ath", status="error", detail="sin precio")
        return 0
    peak = 0.0
    points: list[tuple[str, float | None]] = []
    for p in pts:
        v = float(p["value"])
        peak = max(peak, v)
        points.append((p["d"], (v / peak - 1.0) * 100.0 if peak else 0.0))
    store.upsert_series("drawdown_from_ath", points)
    store.set_metric_state(
        "drawdown_from_ath", status="ok", detail="derivado", last_data_point=points[-1][0], ok=True
    )
    return len(points)


def _convergence() -> int:
    sth = store.get_series("sth_mvrv")
    lth = store.get_series("lth_mvrv")
    lm = {p["d"]: p["value"] for p in lth if p["value"] is not None}
    points = [
        (p["d"], abs(float(p["value"]) - float(lm[p["d"]])))
        for p in sth
        if p["value"] is not None and p["d"] in lm
    ]
    if not points:
        store.set_metric_state(
            "sth_lth_convergence", status="error", detail="faltan sth_mvrv o lth_mvrv"
        )
        return 0
    store.upsert_series("sth_lth_convergence", points)
    store.set_metric_state(
        "sth_lth_convergence", status="ok", detail="derivado", last_data_point=points[-1][0], ok=True
    )
    return len(points)


def recompute_all() -> dict[str, int]:
    """Recalcula todos los derivados. Barato: solo lee de SQLite."""
    results: dict[str, int] = {}
    steps = [
        ("price_vs_200wma", lambda: _moving_average_ratio("price_vs_200wma", 1400)),
        ("mayer_multiple", lambda: _moving_average_ratio("mayer_multiple", 200)),
        ("rsi_weekly", lambda: _rsi("rsi_weekly", "weekly")),
        ("rsi_monthly", lambda: _rsi("rsi_monthly", "monthly")),
        ("drawdown_from_ath", _drawdown),
        ("sth_lth_convergence", _convergence),
        ("price_vs_cvdd", lambda: _ratio_series("price_vs_cvdd", PRICE, "cvdd")),
        ("price_vs_balanced", lambda: _ratio_series("price_vs_balanced", PRICE, "balanced_price")),
    ]
    for name, fn in steps:
        try:
            results[name] = fn()
        except Exception as exc:  # noqa: BLE001
            log.exception("fallo calculando %s", name)
            store.set_metric_state(name, status="error", detail=str(exc))
            results[name] = 0
    return results
