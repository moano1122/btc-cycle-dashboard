"""Índice de Miedo y Codicia (alternative.me).

Por qué tiene su propio módulo
------------------------------
Este indicador estaba consumiendo un hueco del cupo de bitcoin-data.com —15
peticiones al día en el plan gratuito— para un dato que su autor original
publica abierto y sin autenticación. Peor aún: nunca llegaba a descargarse,
porque siempre quedaba al final de la cola de prioridad.

Traerlo de la fuente canónica resuelve tres cosas a la vez:

  1. **Libera un hueco del cupo** para una métrica on-chain irremplazable.
  2. **Da 8 años de historia** en vez de los 4 del plan gratuito, lo que permite
     calibrarlo contra los suelos de 2018 y 2022 en lugar de contra ninguno.
  3. Es la fuente original del índice, no una redistribución.

Sin API key, sin límite práctico de peticiones. La serie arranca el 1 de febrero
de 2018, que es cuando el índice empezó a publicarse.
"""

from __future__ import annotations

import json
import logging
import urllib.request
from datetime import datetime, timezone

from .. import store

log = logging.getLogger(__name__)

URL = "https://api.alternative.me/fng/?limit=0&format=json"
PROVIDER = "alternative.me"
SERIES_ID = "fear_greed"


def fetch() -> int:
    """Descarga el histórico completo del índice."""
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "btc-indicators/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            payload = json.loads(r.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        store.set_metric_state(SERIES_ID, status="error", detail=f"alternative.me: {exc}")
        log.warning("no se pudo descargar el índice de miedo y codicia: %s", exc)
        return 0

    filas = payload.get("data") or []
    puntos: list[tuple[str, float | None]] = []
    for fila in filas:
        try:
            d = datetime.fromtimestamp(int(fila["timestamp"]), tz=timezone.utc).date().isoformat()
            puntos.append((d, float(fila["value"])))
        except (KeyError, TypeError, ValueError):
            continue

    if not puntos:
        store.set_metric_state(SERIES_ID, status="error", detail="respuesta sin datos utilizables")
        return 0

    store.upsert_series(SERIES_ID, puntos)
    store.set_metric_state(
        SERIES_ID,
        status="ok",
        detail=f"alternative.me {len(puntos)} días desde {min(p[0] for p in puntos)}",
        last_data_point=max(p[0] for p in puntos),
        ok=True,
    )
    store.record_call(PROVIDER, "fng", True)
    return len(puntos)
