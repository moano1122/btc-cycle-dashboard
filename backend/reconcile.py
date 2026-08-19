"""Fusión de historia entre proveedores, con verificación previa.

El problema
-----------
bitcoin-data.com da 4 años de historia; Coin Metrics da 16. Extender las series
hacia atrás con el segundo multiplica por cuatro la base de calibración. Pero
dos proveedores que dicen medir lo mismo pueden estar en escalas distintas —ya
pasó con CVDD, Balanced Price y Reserve Risk frente a la literatura— y fusionar
a ciegas metería un escalón invisible justo en la frontera entre ambos.

La regla
--------
Antes de fusionar, se comparan las dos series **en el tramo que solapan**. Solo
se acepta la fusión si:

  1. La correlación supera 0.95, y
  2. La diferencia relativa mediana es menor al 8%.

Si no se cumple, no se fusiona y se registra por qué. Es preferible una serie
corta y honesta a una larga con una costura falsa en medio.

Además, la fusión **nunca pisa** un dato existente: solo rellena fechas que el
proveedor principal no tiene, así que las lecturas recientes siguen siendo las
de bitcoin-data.com.
"""

from __future__ import annotations

import logging
import statistics as st
from typing import Any

from . import store

log = logging.getLogger(__name__)

CORRELACION_MINIMA = 0.95
DIFERENCIA_MAXIMA_PCT = 8.0
SOLAPE_MINIMO = 90

# serie destino  ->  serie de Coin Metrics que la extiende hacia atrás
PARES: dict[str, str] = {
    "btc_price": "cm_price",
    "mvrv": "cm_mvrv",
    "mvrv_zscore": "cm_mvrv_zscore",
    "puell_multiple": "cm_puell_multiple",
    "hash_ribbons": "cm_hash_ribbons",
    "exchange_netflow": "cm_exchange_netflow",
}


def comparar(destino: str, fuente: str) -> dict[str, Any]:
    """Contrasta ambas series en su tramo común."""
    A = {p["d"]: p["value"] for p in store.get_series(destino) if p["value"] is not None}
    B = {p["d"]: p["value"] for p in store.get_series(fuente) if p["value"] is not None}
    comunes = sorted(set(A) & set(B))

    info: dict[str, Any] = {
        "destino": destino,
        "fuente": fuente,
        "solape": len(comunes),
        "correlacion": None,
        "dif_mediana_pct": None,
        "compatible": False,
        "motivo": "",
    }

    if not B:
        info["motivo"] = "la fuente no tiene datos"
        return info
    if not A:
        # Sin serie principal no hay nada que contrastar, pero tampoco nada que
        # corromper: se acepta la fuente como origen único y se deja constancia.
        info.update(compatible=True, motivo="sin serie previa; se adopta la fuente sin contrastar")
        return info
    if len(comunes) < SOLAPE_MINIMO:
        info["motivo"] = f"solape insuficiente ({len(comunes)} días)"
        return info

    x = [A[d] for d in comunes]
    y = [B[d] for d in comunes]
    try:
        info["correlacion"] = st.correlation(x, y)
    except st.StatisticsError:
        info["motivo"] = "serie constante, correlación indefinida"
        return info

    difs = [abs(A[d] - B[d]) / abs(B[d]) * 100 for d in comunes if abs(B[d]) > 1e-9]
    info["dif_mediana_pct"] = st.median(difs) if difs else None

    if info["dif_mediana_pct"] is None:
        info["motivo"] = "no se pudo medir la diferencia"
        return info

    if info["correlacion"] >= CORRELACION_MINIMA and info["dif_mediana_pct"] <= DIFERENCIA_MAXIMA_PCT:
        info["compatible"] = True
        info["motivo"] = "escalas compatibles"
        return info

    # Segunda oportunidad para series con ruido diario. El Puell Multiple, por
    # ejemplo, depende de la emisión de cada día, que varía con el azar del
    # tiempo entre bloques; los dos proveedores discrepan tick a tick aunque
    # midan exactamente lo mismo. Lo que importa para calibrar es el NIVEL, así
    # que se repite la comparación sobre medias de 30 días y se exige además que
    # el ratio entre ambas no derive con los años, que es la firma de una escala
    # realmente distinta.
    sx, sy = _suavizar(x, 30), _suavizar(y, 30)
    if len(sx) >= SOLAPE_MINIMO:
        try:
            corr_suave = st.correlation(sx, sy)
        except st.StatisticsError:
            corr_suave = 0.0
        difs_suaves = [abs(a - b) / abs(b) * 100 for a, b in zip(sx, sy) if abs(b) > 1e-9]
        med_suave = st.median(difs_suaves) if difs_suaves else 999.0

        ratios_por_anio: dict[str, list[float]] = {}
        for d in comunes:
            if abs(B[d]) > 1e-9:
                ratios_por_anio.setdefault(d[:4], []).append(A[d] / B[d])
        medianas = [st.median(v) for v in ratios_por_anio.values() if len(v) >= 30]
        sin_deriva = bool(medianas) and all(0.93 <= m <= 1.07 for m in medianas)

        info["correlacion_suavizada"] = corr_suave
        info["dif_mediana_suavizada_pct"] = med_suave
        info["ratio_anual_estable"] = sin_deriva

        if corr_suave >= CORRELACION_MINIMA and med_suave <= DIFERENCIA_MAXIMA_PCT and sin_deriva:
            info["compatible"] = True
            info["motivo"] = (
                f"compatible al suavizar (corr {corr_suave:.3f}, dif {med_suave:.1f}%); "
                "la discrepancia diaria es ruido, no escala"
            )
            return info

    if info["correlacion"] < CORRELACION_MINIMA:
        info["motivo"] = f"correlación {info['correlacion']:.3f} < {CORRELACION_MINIMA}"
    else:
        info["motivo"] = f"diferencia mediana {info['dif_mediana_pct']:.1f}% > {DIFERENCIA_MAXIMA_PCT}%"
    return info


def _suavizar(valores: list[float], ventana: int) -> list[float]:
    salida, acc = [], []
    for v in valores:
        acc.append(v)
        if len(acc) > ventana:
            acc.pop(0)
        if len(acc) == ventana:
            salida.append(sum(acc) / ventana)
    return salida


def fusionar(destino: str, fuente: str) -> dict[str, Any]:
    """Rellena hacia atrás sin tocar ningún dato existente."""
    info = comparar(destino, fuente)
    info["añadidos"] = 0
    if not info["compatible"]:
        log.info("no se fusiona %s <- %s: %s", destino, fuente, info["motivo"])
        return info

    existentes = {p["d"] for p in store.get_series(destino)}
    nuevos = [
        (p["d"], p["value"])
        for p in store.get_series(fuente)
        if p["value"] is not None and p["d"] not in existentes
    ]
    if nuevos:
        store.upsert_series(destino, nuevos)
        info["añadidos"] = len(nuevos)
        info["desde"] = min(d for d, _ in nuevos)
    return info


def reconcile_all() -> list[dict[str, Any]]:
    return [fusionar(dest, fuente) for dest, fuente in PARES.items()]
