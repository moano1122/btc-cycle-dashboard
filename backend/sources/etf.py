"""Flujos de los ETF spot de bitcoin (Farside Investors).

Por qué este módulo importa más de lo que parece
------------------------------------------------
Todas las métricas on-chain del catálogo miden lo mismo desde ángulos distintos:
qué hacen las monedas dentro de la cadena. Los ETF spot introdujeron un comprador
que **no aparece ahí**: el flujo de dinero institucional se ejecuta contra
custodios y mesas OTC, y mueve el precio sin dejar la huella on-chain que esos
indicadores esperan.

Eso no es teórico. Las tenencias de los ETF hicieron pico en octubre de 2025 con
BTC sobre 126.000 dólares, y desde entonces han salido más de 160.000 BTC. Ese
mismo techo pasó sin que ningún indicador on-chain mayor diera señal de venta.
Si un panel de suelo de mercado ignora los ETFs, ignora al actor que marcó el
último giro del ciclo.

Fuente
------
Farside Investors publica la tabla diaria completa desde el lanzamiento de los
ETF (11 de enero de 2024), por fondo y agregada, en millones de dólares. Es
pública y gratuita; solo exige una cabecera de navegador.

Limitación que hay que tener presente
-------------------------------------
La serie empieza en 2024, así que **no contiene ningún suelo de ciclo**. Los
ETFs no existían en 2015, 2018 ni 2022. Cualquier umbral aquí se calibra contra
cero suelos históricos, y el panel lo marca como tal. Es el indicador más
relevante por mecanismo y el menos validado por historia, a la vez.
"""

from __future__ import annotations

import logging
import re
import urllib.request
from datetime import datetime

from .. import store

log = logging.getLogger(__name__)

URL = "https://farside.co.uk/bitcoin-etf-flow-all-data/"
PROVIDER = "farside"
CABECERAS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml",
}

FLOW_USD = "etf_flow_usd"          # flujo neto diario, en millones de USD
# Posición NETA acumulada desde el lanzamiento de los ETF, en BTC. No son las
# tenencias totales: GBTC llegó al mercado con un stack previo de cientos de
# miles de BTC que nunca aparece como "flujo". Lo que mide esta serie es cuánto
# ha entrado o salido desde enero de 2024, que es justo lo que interesa para
# medir el apetito institucional.
NET_POSITION_BTC = "etf_net_position_btc"

# Posición mínima a partir de la cual una caída porcentual es interpretable.
BASE_MINIMA_BTC = 100_000


def _numero(txt: str) -> float | None:
    """Convierte una celda de Farside a número.

    Los negativos vienen entre paréntesis —convención contable— y los miles con
    coma. Un guion significa que ese fondo no cotizaba aún ese día.
    """
    t = txt.replace(" ", " ").strip()
    if not t or t == "-":
        return None
    negativo = t.startswith("(") and t.endswith(")")
    t = t.strip("()").replace(",", "").replace("$", "").strip()
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if negativo else v


def _celdas(fila_html: str) -> list[str]:
    return [
        re.sub(r"<[^>]+>", "", c).replace(" ", " ").strip()
        for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", fila_html, re.S)
    ]


def fetch() -> int:
    """Descarga y guarda el flujo neto diario agregado."""
    try:
        req = urllib.request.Request(URL, headers=CABECERAS)
        with urllib.request.urlopen(req, timeout=90) as r:
            html = r.read().decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        store.set_metric_state(FLOW_USD, status="error", detail=f"farside: {exc}")
        log.warning("no se pudo descargar Farside: %s", exc)
        return 0

    filas = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S)
    cabecera = None
    puntos: list[tuple[str, float | None]] = []

    for fila in filas:
        c = _celdas(fila)
        if not c:
            continue
        if c[0].strip().lower() == "date":
            cabecera = [x.strip() for x in c]
            continue
        if cabecera is None or len(c) != len(cabecera):
            continue
        # La última fila de la tabla es el acumulado "Total", no un día.
        if c[0].strip().lower().startswith("total"):
            continue
        try:
            d = datetime.strptime(c[0].strip(), "%d %b %Y").date().isoformat()
        except ValueError:
            continue
        total = _numero(c[cabecera.index("Total")]) if "Total" in cabecera else _numero(c[-1])
        if total is not None:
            puntos.append((d, total))

    if not puntos:
        store.set_metric_state(FLOW_USD, status="error", detail="no se pudo parsear la tabla")
        return 0

    store.upsert_series(FLOW_USD, puntos)
    store.set_metric_state(
        FLOW_USD,
        status="ok",
        detail=f"farside {len(puntos)} días desde {min(p[0] for p in puntos)}",
        last_data_point=max(p[0] for p in puntos),
        ok=True,
    )
    store.record_call(PROVIDER, "bitcoin-etf-flow", True)
    return len(puntos)


# --------------------------------------------------------------------------
# Derivaciones
# --------------------------------------------------------------------------
def _serie(sid: str) -> list[tuple[str, float]]:
    return [(p["d"], float(p["value"])) for p in store.get_series(sid) if p["value"] is not None]


def _guardar(sid: str, puntos: list[tuple[str, float]], detalle: str) -> int:
    if not puntos:
        store.set_metric_state(sid, status="error", detail="sin insumos")
        return 0
    # Reemplazo y no fusión: si cambia la definición del derivado, los puntos
    # calculados con la regla anterior no deben sobrevivir.
    store.replace_series(sid, puntos)
    store.set_metric_state(sid, status="ok", detail=detalle, last_data_point=puntos[-1][0], ok=True)
    return len(puntos)


def derive_net_position() -> int:
    """Posición neta acumulada en BTC, convirtiendo cada flujo diario al precio del día.

    Es una estimación: convierte cada flujo al precio de su día, así que no
    coincide exactamente con el conteo de monedas de los custodios —vender el
    mismo dinero a un precio más bajo libera más BTC—. Sirve para medir la forma
    de la curva y cuánto se ha deshecho la posición desde su pico, que es lo que
    interesa aquí.
    """
    precio = dict(_serie("btc_price"))
    acumulado = 0.0
    puntos: list[tuple[str, float]] = []
    for d, usd_millones in _serie(FLOW_USD):
        p = precio.get(d)
        if not p:
            continue
        acumulado += usd_millones * 1_000_000.0 / p
        puntos.append((d, acumulado))
    return _guardar(NET_POSITION_BTC, puntos, "flujos acumulados al precio de cada día")


def derive_flow_30d() -> int:
    """Flujo neto de los últimos 30 días, en millones de USD."""
    serie = _serie(FLOW_USD)
    puntos, acc = [], []
    for d, v in serie:
        acc.append(v)
        if len(acc) > 30:
            acc.pop(0)
        puntos.append((d, sum(acc)))
    return _guardar("etf_flow_30d", puntos, "suma móvil de 30 días")


def derive_position_drawdown() -> int:
    """Caída porcentual de la posición neta desde su máximo.

    Mide cuánto de la posición institucional se ha deshecho. Es el análogo, del
    lado de la demanda, a la caída del precio desde máximos.
    """
    pico = 0.0
    puntos = []
    for d, v in _serie(NET_POSITION_BTC):
        pico = max(pico, v)
        # Se descartan las primeras semanas de 2024. Con la posición acumulada
        # aún en unos pocos miles de BTC, una salida normal de GBTC producía
        # caídas del 45% que no significan nada: el denominador era diminuto.
        # Ese artefacto llegó a fijar el anclaje de puntuación máxima, así que
        # no es una sutileza cosmética.
        if pico >= BASE_MINIMA_BTC:
            puntos.append((d, (v / pico - 1.0) * 100.0))
    return _guardar(
        "etf_position_drawdown", puntos,
        f"caída desde el pico, desde que la base superó {BASE_MINIMA_BTC:,.0f} BTC",
    )


def refresh_all() -> dict[str, int]:
    res = {FLOW_USD: fetch()}
    res["etf_flow_30d"] = derive_flow_30d()
    res[NET_POSITION_BTC] = derive_net_position()
    res["etf_position_drawdown"] = derive_position_drawdown()
    return res
