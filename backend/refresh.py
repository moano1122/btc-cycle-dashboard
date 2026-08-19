"""Orquestador de refresco.

El cupo gratuito (10 peticiones/hora, 15/día) no alcanza para los 22 indicadores
on-chain del catálogo. En vez de fallar, este módulo prioriza:

  1. Binance y todo lo derivado del precio: gratis e ilimitado, siempre primero.
  2. Series de apoyo que otros indicadores necesitan (precio histórico, CVDD,
     Balanced Price).
  3. Indicadores on-chain ordenados por (tier de refresco, peso descendente).
     Los de mayor peso se refrescan a diario; los secundarios cada 2-3 días.

Si el cupo se agota a mitad del ciclo, lo que quedó sin refrescar conserva su
último valor bueno y el dashboard lo marca. En la siguiente pasada se retoma
por donde se quedó, porque el orden es estable y los ya frescos se saltan.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from . import derived, store
from .catalog import INDICATORS, SUPPORT_SERIES, onchain_indicators
from . import reconcile
from .sources import bitcoin_data, coinmetrics, etf, market, sentiment

log = logging.getLogger(__name__)

# Ventana bajo la cual se considera que una métrica ya está fresca y no vale la
# pena gastarle una petición. Los datos on-chain se publican una vez al día.
FRESH_HOURS = 20


def _is_fresh(metric_id: str, states: dict[str, dict]) -> bool:
    st = states.get(metric_id)
    if not st or st.get("status") != "ok" or not st.get("last_ok_utc"):
        return False
    try:
        last = datetime.fromisoformat(st["last_ok_utc"])
    except ValueError:
        return False
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - last < timedelta(hours=FRESH_HOURS)


def _tier_due(metric_id: str, tier: int, states: dict[str, dict]) -> bool:
    """Los indicadores de tier 2 y 3 no necesitan refresco diario."""
    if tier <= 1:
        return True
    st = states.get(metric_id)
    if not st or not st.get("last_ok_utc"):
        return True
    try:
        last = datetime.fromisoformat(st["last_ok_utc"])
    except ValueError:
        return True
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    interval = timedelta(days=2 if tier == 2 else 7)
    return datetime.now(timezone.utc) - last >= interval


def refresh(*, force: bool = False, include_history: bool = True) -> dict[str, Any]:
    """Ejecuta un ciclo completo de refresco. Nunca lanza excepción hacia arriba."""
    store.init()
    report: dict[str, Any] = {
        "started": store.now_utc(),
        "market": 0,
        "onchain_fetched": [],
        "onchain_skipped_fresh": [],
        "onchain_skipped_budget": [],
        "errors": [],
    }

    # --- 1. Precio (gratis) -------------------------------------------------
    try:
        report["market"] = market.incremental_update()
    except Exception as exc:  # noqa: BLE001
        report["errors"].append(f"binance: {exc}")

    # Miedo y codicia: fuente abierta, sin cupo. Va con el bloque gratuito para
    # no competir por las peticiones que necesitan las métricas on-chain.
    try:
        report["fear_greed"] = sentiment.fetch()
    except Exception as exc:  # noqa: BLE001
        report["errors"].append(f"fear_greed: {exc}")

    states = store.get_metric_states()

    # --- 2. Series de apoyo -------------------------------------------------
    # btc_price desde el proveedor on-chain solo se pide una vez, para rellenar
    # la historia anterior a 2017 que Binance no tiene. Después no se vuelve a
    # tocar: sería desperdiciar cupo.
    support_queue: list[tuple[str, str]] = []
    _, _, price_points = store.series_span("btc_price_full")
    if include_history and price_points == 0:
        support_queue.append(("btc_price_full", SUPPORT_SERIES["btc_price"]))
    for key in ("cvdd", "balanced_price"):
        if force or not _is_fresh(key, states):
            support_queue.append((key, SUPPORT_SERIES[key]))
    # SOPR sin ajustar: se pide una sola vez para comparar su profundidad
    # histórica con la del aSOPR, que apenas llega a noviembre de 2025.
    if store.series_span("sopr_raw")[2] == 0:
        support_queue.append(("sopr_raw", SUPPORT_SERIES["sopr_raw"]))

    for metric_id, endpoint in support_queue:
        try:
            n = bitcoin_data.fetch_metric(metric_id, endpoint)
            if n:
                report["onchain_fetched"].append(metric_id)
        except bitcoin_data.BudgetExhausted as exc:
            report["onchain_skipped_budget"].append(metric_id)
            report["errors"].append(str(exc))
            break
        except Exception as exc:  # noqa: BLE001
            report["errors"].append(f"{metric_id}: {exc}")

    # Fusiona la historia larga en la serie de precio principal sin pisar los
    # datos de Binance, que son más precisos para fechas recientes.
    if store.series_span("btc_price_full")[2]:
        existing = {p["d"] for p in store.get_series("btc_price")}
        old = [
            (p["d"], p["value"])
            for p in store.get_series("btc_price_full")
            if p["d"] not in existing and p["value"] is not None
        ]
        if old:
            store.upsert_series("btc_price", old)

    # --- 3. Indicadores on-chain, por prioridad -----------------------------
    states = store.get_metric_states()
    queue = sorted(onchain_indicators(), key=lambda i: (i.refresh_tier, -i.weight))
    for ind in queue:
        if not force:
            if _is_fresh(ind.id, states) or not _tier_due(ind.id, ind.refresh_tier, states):
                report["onchain_skipped_fresh"].append(ind.id)
                continue
        try:
            n = bitcoin_data.fetch_metric(ind.id, ind.endpoint or "")
            if n:
                report["onchain_fetched"].append(ind.id)
        except bitcoin_data.BudgetExhausted:
            remaining = [
                i.id
                for i in queue[queue.index(ind) :]
                if i.id not in report["onchain_fetched"]
            ]
            report["onchain_skipped_budget"].extend(remaining)
            break
        except Exception as exc:  # noqa: BLE001
            report["errors"].append(f"{ind.id}: {exc}")

    # --- 3b. Coin Metrics: historia larga, gratis y sin key -----------------
    # Se refresca una vez al día. Aporta 16 años de historia frente a los 4 del
    # plan gratuito del otro proveedor, que es lo que permite calibrar contra
    # tres suelos de ciclo en vez de uno.
    try:
        if force or not _is_fresh("cm_mvrv", store.get_metric_states()):
            report["coinmetrics"] = coinmetrics.fetch_all()
            report["coinmetrics_derivados"] = coinmetrics.derive_all()
        else:
            report["coinmetrics"] = "fresco, se omite"
        # La fusión solo extiende hacia atrás y solo si ambos proveedores
        # coinciden en el tramo solapado; nunca pisa un dato existente.
        report["fusion"] = [
            {k: r[k] for k in ("destino", "añadidos", "motivo")}
            for r in reconcile.reconcile_all()
        ]
    except Exception as exc:  # noqa: BLE001
        report["errors"].append(f"coinmetrics: {exc}")

    # --- 3c. Flujos de ETF (Farside, gratis) --------------------------------
    # Es el único bloque que mide al comprador institucional, invisible para las
    # métricas on-chain. Se refresca a diario porque el dato es diario.
    try:
        if force or not _is_fresh("etf_flow_usd", store.get_metric_states()):
            report["etf"] = etf.refresh_all()
        else:
            report["etf"] = "fresco, se omite"
    except Exception as exc:  # noqa: BLE001
        report["errors"].append(f"etf: {exc}")

    # --- 4. Derivados (gratis, solo lee de SQLite) --------------------------
    try:
        report["derived"] = derived.recompute_all()
    except Exception as exc:  # noqa: BLE001
        report["errors"].append(f"derivados: {exc}")

    report["budget"] = bitcoin_data.budget_status()
    report["finished"] = store.now_utc()
    return report


def missing_metrics() -> list[str]:
    """Indicadores del catálogo que aún no tienen ningún dato en caché."""
    out = []
    for ind in INDICATORS:
        if store.series_span(ind.id)[2] == 0:
            out.append(ind.id)
    return out
