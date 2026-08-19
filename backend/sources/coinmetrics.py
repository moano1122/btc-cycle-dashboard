"""Coin Metrics Community API — historia larga y gratuita.

Por qué existe este módulo
--------------------------
bitcoin-data.com solo entrega **4 años** de historia en el plan gratuito, así
que toda la calibración descansaba sobre un único suelo de ciclo (nov-2022).
Coin Metrics publica un subconjunto de sus métricas bajo licencia community:
**gratis, sin API key, y desde 2010**. Eso permite calibrar contra cuatro suelos
—2015, 2018, marzo-2020 y 2022— en vez de uno.

Qué se trae y qué se deriva
---------------------------
De la API vienen métricas crudas; los indicadores del catálogo se construyen
aquí a partir de ellas:

    CapMVRVCur     -> MVRV, y con la capitalización, el MVRV Z-Score
    CapMrktCurUSD  -> capitalización de mercado
    PriceUSD       -> precio desde 2010 (Binance solo llega a 2017)
    IssTotUSD      -> Puell Multiple
    HashRate       -> Hash Ribbons
    FlowInExNtv    -> flujo neto a exchanges
    FlowOutExNtv

Regla de convivencia con el otro proveedor
------------------------------------------
Las series se guardan con prefijo `cm_` y **nunca sobrescriben** las de
bitcoin-data.com. La fusión hacia atrás la decide `reconcile.py`, y solo después
de comprobar que ambos proveedores coinciden en el tramo solapado. Dos fuentes
que miden lo mismo pueden estar en escalas distintas, y mezclarlas a ciegas
produciría una serie con un escalón invisible justo en la frontera.

Límite de uso: 10 peticiones cada 6 segundos por IP. Cada métrica es una
petición paginada, así que un refresco completo son unas pocas decenas.
"""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from typing import Any

from .. import store

log = logging.getLogger(__name__)

BASE = "https://community-api.coinmetrics.io/v4"
PROVIDER = "coinmetrics"
START = "2010-01-01"

# métrica de Coin Metrics -> id de serie local
RAW_METRICS: dict[str, str] = {
    "PriceUSD": "cm_price",
    "CapMVRVCur": "cm_mvrv",
    "CapMrktCurUSD": "cm_marketcap",
    "IssTotUSD": "cm_issuance_usd",
    "HashRate": "cm_hashrate",
    "FlowInExNtv": "cm_exch_in",
    "FlowOutExNtv": "cm_exch_out",
}


def _get(url: str, intentos: int = 3) -> dict[str, Any]:
    ultimo: Exception | None = None
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "btc-indicators/1.0"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429:  # límite de 10 req / 6 s
                time.sleep(3 * (i + 1))
                ultimo = exc
                continue
            raise
        except Exception as exc:  # noqa: BLE001
            ultimo = exc
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"Coin Metrics no respondió: {ultimo}")


def fetch_metric(cm_metric: str, series_id: str, start: str = START) -> int:
    """Descarga una métrica completa paginando hasta agotar los resultados."""
    puntos: list[tuple[str, float | None]] = []
    url = (
        f"{BASE}/timeseries/asset-metrics?assets=btc&metrics={cm_metric}"
        f"&frequency=1d&start_time={start}&page_size=10000"
    )
    try:
        while url:
            payload = _get(url)
            for fila in payload.get("data", []):
                valor = fila.get(cm_metric)
                if valor in (None, ""):
                    continue
                try:
                    puntos.append((fila["time"][:10], float(valor)))
                except (ValueError, KeyError):
                    continue
            url = payload.get("next_page_url")
            if url:
                time.sleep(0.7)  # respeta el límite de 10 req / 6 s
    except Exception as exc:  # noqa: BLE001
        store.set_metric_state(series_id, status="error", detail=f"coinmetrics: {exc}")
        log.warning("Coin Metrics falló en %s: %s", cm_metric, exc)
        return 0

    if not puntos:
        store.set_metric_state(series_id, status="error", detail="0 puntos")
        return 0

    n = store.upsert_series(series_id, puntos)
    store.set_metric_state(
        series_id,
        status="ok",
        detail=f"coinmetrics {n} puntos desde {puntos[0][0]}",
        last_data_point=max(p[0] for p in puntos),
        ok=True,
    )
    store.record_call(PROVIDER, cm_metric, True)
    return n


def fetch_all(start: str = START) -> dict[str, int]:
    resultado: dict[str, int] = {}
    for cm_metric, series_id in RAW_METRICS.items():
        resultado[series_id] = fetch_metric(cm_metric, series_id, start)
        time.sleep(0.7)
    return resultado


# --------------------------------------------------------------------------
# Derivaciones sobre las series crudas
# --------------------------------------------------------------------------
def _serie(sid: str) -> list[tuple[str, float]]:
    return [(p["d"], float(p["value"])) for p in store.get_series(sid) if p["value"] is not None]


def _guardar(sid: str, puntos: list[tuple[str, float]], detalle: str) -> int:
    if not puntos:
        store.set_metric_state(sid, status="error", detail="sin insumos")
        return 0
    store.upsert_series(sid, puntos)
    store.set_metric_state(
        sid, status="ok", detail=detalle, last_data_point=puntos[-1][0], ok=True
    )
    return len(puntos)


def derive_mvrv_zscore() -> int:
    """MVRV Z-Score = (capitalización − capitalización realizada) / desviación estándar.

    La capitalización realizada se obtiene como `capitalización / MVRV`, y la
    desviación estándar es la de la capitalización sobre toda la historia
    transcurrida hasta cada día (ventana expansiva), que es la definición
    estándar del indicador.
    """
    mvrv = dict(_serie("cm_mvrv"))
    cap = _serie("cm_marketcap")
    puntos: list[tuple[str, float]] = []
    n = 0
    suma = suma_cuadrados = 0.0
    for d, c in cap:
        n += 1
        suma += c
        suma_cuadrados += c * c
        m = mvrv.get(d)
        if m in (None, 0) or n < 30:
            continue
        varianza = max(suma_cuadrados / n - (suma / n) ** 2, 0.0)
        desv = varianza ** 0.5
        if desv <= 0:
            continue
        realizada = c / m
        puntos.append((d, (c - realizada) / desv))
    return _guardar("cm_mvrv_zscore", puntos, "derivado de cap y MVRV")


def derive_realized_price() -> int:
    """Precio realizado = capitalización realizada / oferta.

    La oferta se deduce de capitalización / precio, así se evita una petición.
    """
    mvrv = dict(_serie("cm_mvrv"))
    precio = dict(_serie("cm_price"))
    puntos = []
    for d, c in _serie("cm_marketcap"):
        m, p = mvrv.get(d), precio.get(d)
        if not m or not p:
            continue
        oferta = c / p
        if oferta <= 0:
            continue
        puntos.append((d, (c / m) / oferta))
    return _guardar("cm_realized_price", puntos, "derivado")


def _media_movil(serie: list[tuple[str, float]], ventana: int) -> list[tuple[str, float]]:
    salida, acc = [], []
    for d, v in serie:
        acc.append(v)
        if len(acc) > ventana:
            acc.pop(0)
        if len(acc) == ventana:
            salida.append((d, sum(acc) / ventana))
    return salida


def derive_puell() -> int:
    """Puell Multiple = emisión diaria en USD / su media de 365 días."""
    emision = _serie("cm_issuance_usd")
    media = dict(_media_movil(emision, 365))
    puntos = [(d, v / media[d]) for d, v in emision if media.get(d)]
    return _guardar("cm_puell_multiple", puntos, "derivado de la emisión")


def derive_hash_ribbons() -> int:
    """Hash Ribbons = media de 30 días del hashrate / media de 60 días."""
    hr = _serie("cm_hashrate")
    m30 = dict(_media_movil(hr, 30))
    m60 = dict(_media_movil(hr, 60))
    puntos = [(d, m30[d] / m60[d]) for d in m30 if m60.get(d)]
    puntos.sort()
    return _guardar("cm_hash_ribbons", puntos, "derivado del hashrate")


def derive_exchange_netflow() -> int:
    salidas = dict(_serie("cm_exch_out"))
    puntos = [(d, v - salidas[d]) for d, v in _serie("cm_exch_in") if d in salidas]
    return _guardar("cm_exchange_netflow", puntos, "entradas menos salidas")


def derive_all() -> dict[str, int]:
    return {
        "cm_mvrv_zscore": derive_mvrv_zscore(),
        "cm_realized_price": derive_realized_price(),
        "cm_puell_multiple": derive_puell(),
        "cm_hash_ribbons": derive_hash_ribbons(),
        "cm_exchange_netflow": derive_exchange_netflow(),
    }
