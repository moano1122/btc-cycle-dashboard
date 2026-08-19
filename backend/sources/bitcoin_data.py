"""Cliente de bitcoin-data.com (BGeometrics).

Dos cosas importantes de este módulo:

1. Respeta el cupo del plan de forma estricta. El plan gratuito son 10
   peticiones por hora y 15 por día; excederlo devuelve 429 y bloquea. El
   presupuesto se lleva en SQLite (no en memoria) para que sobreviva a
   reinicios del proceso.

2. Nunca revienta hacia arriba. Si una métrica falla, se registra el error en
   `metric_state` y el dashboard sigue mostrando el último dato bueno marcado
   como rancio. Es preferible un dato de ayer señalizado como tal que una
   pantalla en blanco.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Callable

import httpx

from .. import store
from ..config import BITCOIN_DATA_API_KEY, BITCOIN_DATA_BASE, REQ_PER_DAY, REQ_PER_HOUR

log = logging.getLogger(__name__)

PROVIDER = "bitcoin-data"

# Claves que son metadatos de fecha, nunca el valor de la métrica.
_DATE_KEYS = {"d", "day", "theday", "date", "unixts", "unixtimestamp", "timestamp", "ts"}


class BudgetExhausted(RuntimeError):
    """El cupo del plan se agotó. No es un error de red: es esperado y se maneja."""


def budget_status() -> dict[str, Any]:
    used_h, used_d = store.calls_used(PROVIDER)
    return {
        "used_hour": used_h,
        "limit_hour": REQ_PER_HOUR,
        "used_day": used_d,
        "limit_day": REQ_PER_DAY,
        "remaining_hour": max(0, REQ_PER_HOUR - used_h),
        "remaining_day": max(0, REQ_PER_DAY - used_d),
        "has_key": bool(BITCOIN_DATA_API_KEY),
    }


def _can_spend() -> bool:
    used_h, used_d = store.calls_used(PROVIDER)
    return used_h < REQ_PER_HOUR and used_d < REQ_PER_DAY


def _headers() -> dict[str, str]:
    h = {"Accept": "application/json", "User-Agent": "btc-indicators/1.0"}
    if BITCOIN_DATA_API_KEY:
        # El portal documenta la key como cabecera. Mandamos ambas variantes
        # habituales porque no tenemos forma de verificar cuál espera sin key.
        h["x-api-key"] = BITCOIN_DATA_API_KEY
        h["Authorization"] = f"Bearer {BITCOIN_DATA_API_KEY}"
    return h


def _pick_value(row: dict[str, Any]) -> float | None:
    """Extrae el valor numérico de una fila ignorando los campos de fecha.

    Las respuestas tienen forma {"d": "...", "unixTs": ..., "<nombreMetrica>": 0.35}
    y el nombre de la métrica cambia con cada endpoint, así que se detecta.
    """
    for k, v in row.items():
        if k.lower() in _DATE_KEYS:
            continue
        if isinstance(v, bool):
            continue
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                continue
    return None


def _pick_date(row: dict[str, Any]) -> str | None:
    for k in ("d", "day", "theDay", "date"):
        if k in row and row[k]:
            return str(row[k])[:10]
    for k, v in row.items():
        if k.lower() in ("unixts", "timestamp", "ts") and isinstance(v, (int, float)):
            try:
                return date.fromtimestamp(float(v)).isoformat()
            except (OverflowError, OSError, ValueError):
                return None
    return None


def _ratio_of_two(row: dict[str, Any], short_hint: str, long_hint: str) -> float | None:
    """Para endpoints que devuelven dos medias (p.ej. Hash Ribbons)."""
    s = l = None
    for k, v in row.items():
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            continue
        kl = k.lower()
        if kl in _DATE_KEYS:
            continue
        if short_hint in kl:
            s = float(v)
        elif long_hint in kl:
            l = float(v)
    if s is not None and l not in (None, 0):
        return s / l
    return None


# Endpoints cuya respuesta no es un único valor y necesitan extracción a medida.
EXTRACTORS: dict[str, Callable[[dict[str, Any]], float | None]] = {
    "hash_ribbons": lambda r: _ratio_of_two(r, "30", "60"),
}


def fetch_metric(metric_id: str, endpoint: str, *, full_history: bool = True) -> int:
    """Descarga una métrica y la guarda en caché. Devuelve nº de puntos guardados.

    Lanza BudgetExhausted si no queda cupo; el llamador decide si abortar el
    ciclo de refresco completo o saltarse esta métrica.
    """
    if not _can_spend():
        raise BudgetExhausted(
            f"Cupo agotado ({REQ_PER_HOUR}/hora, {REQ_PER_DAY}/día). "
            "Configure BITCOIN_DATA_API_KEY o suba de plan."
        )

    url = f"{BITCOIN_DATA_BASE}/v1/{endpoint}"
    if not full_history:
        url += "/400"

    ok = False
    try:
        with httpx.Client(timeout=60.0, follow_redirects=True) as client:
            resp = client.get(url, headers=_headers())
        ok = resp.status_code == 200
        store.record_call(PROVIDER, endpoint, ok)

        if resp.status_code == 429:
            store.set_metric_state(
                metric_id, status="error", detail="429 cupo excedido por el proveedor"
            )
            raise BudgetExhausted("El proveedor devolvió 429: cupo excedido.")
        resp.raise_for_status()
        payload = resp.json()
    except BudgetExhausted:
        raise
    except Exception as exc:  # noqa: BLE001 - queremos degradar, no propagar
        if not ok:
            store.record_call(PROVIDER, endpoint, False)
        store.set_metric_state(metric_id, status="error", detail=f"{type(exc).__name__}: {exc}")
        log.warning("fallo al descargar %s (%s): %s", metric_id, endpoint, exc)
        return 0

    rows = payload if isinstance(payload, list) else payload.get("data", [])
    if not isinstance(rows, list):
        store.set_metric_state(metric_id, status="error", detail="respuesta con forma inesperada")
        return 0

    extractor = EXTRACTORS.get(metric_id, _pick_value)
    points: list[tuple[str, float | None]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        d = _pick_date(row)
        v = extractor(row)
        if d is not None and v is not None:
            points.append((d, v))

    if not points:
        store.set_metric_state(metric_id, status="error", detail="0 puntos utilizables")
        return 0

    n = store.upsert_series(metric_id, points)
    last_d = max(p[0] for p in points)
    store.set_metric_state(
        metric_id, status="ok", detail=f"{n} puntos", last_data_point=last_d, ok=True
    )
    return n


def probe(endpoint: str) -> dict[str, Any]:
    """Inspección de un endpoint, para diagnóstico. Consume cupo."""
    if not _can_spend():
        return {"error": "sin cupo"}
    url = f"{BITCOIN_DATA_BASE}/v1/{endpoint}/2"
    try:
        with httpx.Client(timeout=45.0, follow_redirects=True) as client:
            resp = client.get(url, headers=_headers())
        store.record_call(PROVIDER, endpoint, resp.status_code == 200)
        return {"status": resp.status_code, "body": resp.text[:600]}
    except Exception as exc:  # noqa: BLE001
        store.record_call(PROVIDER, endpoint, False)
        return {"error": str(exc)}
