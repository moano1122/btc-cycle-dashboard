"""Motor de puntuación.

Traduce cada indicador a una escala común 0-100 ("puntuación de suelo") y los
combina en un score agregado ponderado.

Dos decisiones de diseño que importan:

1. **Renormalización por cobertura.** Si faltan datos de 5 de 28 indicadores, el
   score se calcula solo con los 23 disponibles y se reporta el porcentaje de
   cobertura. Un score de 72 con 40% de cobertura no vale lo mismo que uno de 72
   con 95%, y la interfaz debe mostrar esa diferencia en vez de esconderla.

2. **Nada de extrapolación.** Fuera del rango de anclajes la puntuación se
   satura en 0 o 100. Si el MVRV Z-Score cae a -2 (nunca visto), el sistema dice
   100, no 130. Inventar precisión donde no hay historia sería peor que inútil.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from . import store
from .catalog import BY_ID, CATEGORY_LABELS, INDICATORS, Indicator, default_weights
from .config import STALE_AFTER_DAYS

WEIGHTS_KEY = "user_weights"

# Bandas del score agregado. Describen el estado histórico del mercado, no una
# recomendación: la decisión de comprar es del usuario.
BANDS: list[tuple[float, str, str, str]] = [
    (88, "capitulacion", "Capitulación extrema", "Lecturas comparables solo a los suelos de 2015, 2018 y 2022."),
    (75, "suelo_probable", "Zona de suelo probable", "La mayoría de indicadores en territorio de suelo de ciclo."),
    (60, "acumulacion", "Zona de acumulación", "Valoraciones históricamente bajas, pero sin capitulación completa."),
    (45, "valor", "Zona de valor", "Por debajo de la media del ciclo. Aún no es un extremo."),
    (28, "neutral", "Neutral", "Ni caro ni barato en términos históricos."),
    (15, "caro", "Caro", "Valoraciones por encima de la media del ciclo."),
    (0, "euforia", "Euforia", "Territorio de techo de ciclo."),
]


def interpolate(anchors: list[tuple[float, float]], value: float) -> float:
    """Interpola linealmente `value` sobre los anclajes (valor -> puntuación).

    Los anclajes pueden venir en orden ascendente o descendente de valor; se
    normalizan aquí para que el catálogo se pueda escribir de la forma que sea
    más legible para cada indicador.
    """
    pts = sorted(anchors, key=lambda t: t[0])
    if value <= pts[0][0]:
        return float(pts[0][1])
    if value >= pts[-1][0]:
        return float(pts[-1][1])
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        if x0 <= value <= x1:
            if x1 == x0:
                return float(y1)
            t = (value - x0) / (x1 - x0)
            return float(y0 + t * (y1 - y0))
    return float(pts[-1][1])


def band_for(score: float) -> tuple[str, str, str]:
    for threshold, key, label, blurb in BANDS:
        if score >= threshold:
            return key, label, blurb
    return BANDS[-1][1], BANDS[-1][2], BANDS[-1][3]


def _smoothed(points: list[dict], window: int) -> list[dict]:
    if window <= 1:
        return points
    vals = [p for p in points if p["value"] is not None]
    out = []
    acc: list[float] = []
    for p in vals:
        acc.append(float(p["value"]))
        if len(acc) > window:
            acc.pop(0)
        out.append({"d": p["d"], "value": sum(acc) / len(acc)})
    return out


def get_weights() -> dict[str, int]:
    saved = store.get_setting(WEIGHTS_KEY) or {}
    weights = default_weights()
    for k, v in saved.items():
        if k in weights:
            try:
                weights[k] = max(0, min(20, int(v)))
            except (TypeError, ValueError):
                continue
    return weights


def save_weights(weights: dict[str, Any]) -> dict[str, int]:
    clean: dict[str, int] = {}
    for k, v in weights.items():
        if k in BY_ID:
            try:
                clean[k] = max(0, min(20, int(v)))
            except (TypeError, ValueError):
                continue
    store.set_setting(WEIGHTS_KEY, clean)
    return get_weights()


def reset_weights() -> dict[str, int]:
    store.set_setting(WEIGHTS_KEY, {})
    return default_weights()


def _distance_to_trigger(ind: Indicator, value: float) -> dict[str, Any]:
    """Cuánto le falta al indicador para cruzar su umbral de disparo."""
    if ind.trigger_dir == "below":
        triggered = value <= ind.trigger
        gap = value - ind.trigger
    else:
        triggered = value >= ind.trigger
        gap = ind.trigger - value
    pct = None
    if ind.trigger not in (0, None):
        pct = (gap / abs(ind.trigger)) * 100.0
    return {"triggered": triggered, "gap": gap, "gap_pct": pct}


def evaluate_indicator(ind: Indicator, states: dict[str, dict]) -> dict[str, Any]:
    series = store.get_series(ind.id)
    series = _smoothed(series, ind.smooth_days)
    latest = series[-1] if series else None
    st = states.get(ind.id, {})

    base = {
        "id": ind.id,
        "label": ind.label,
        "category": ind.category,
        "category_label": CATEGORY_LABELS[ind.category],
        "summary": ind.summary,
        "unit": ind.unit,
        "decimals": ind.decimals,
        "trigger": ind.trigger,
        "trigger_dir": ind.trigger_dir,
        "smooth_days": ind.smooth_days,
        "historic": ind.historic,
        "source": ind.source,
        "calibration": ind.calibration,
        # Cuántos suelos de ciclo respaldan el umbral. Uno no es lo mismo que
        # tres, y el usuario tiene que poder verlo antes de fiarse.
        "ciclos": len([k for k in ind.historic if k.startswith("suelo ")]),
        "status": st.get("status", "never"),
        "detail": st.get("detail", ""),
        "invert_chart": ind.invert_chart,
    }

    if latest is None or latest["value"] is None:
        base.update(
            {
                "value": None,
                "score": None,
                "available": False,
                "stale": True,
                "as_of": None,
                "age_days": None,
                "triggered": False,
            }
        )
        return base

    value = float(latest["value"])
    score = interpolate(ind.anchors, value)
    age = store.days_since(latest["d"])
    dist = _distance_to_trigger(ind, value)

    # Variación reciente: da contexto sobre si el indicador se acerca o se aleja
    # del umbral, que suele importar más que el nivel puntual.
    prev_30 = None
    if len(series) > 30:
        prev_30 = series[-31]["value"]
    delta_30 = (value - float(prev_30)) if prev_30 is not None else None

    base.update(
        {
            "value": value,
            "score": round(score, 1),
            "available": True,
            "stale": age is not None and age > STALE_AFTER_DAYS,
            "as_of": latest["d"],
            "age_days": age,
            "delta_30d": delta_30,
            **dist,
        }
    )
    return base


def snapshot(weights: dict[str, int] | None = None) -> dict[str, Any]:
    weights = weights or get_weights()
    states = store.get_metric_states()

    rows = [evaluate_indicator(ind, states) for ind in INDICATORS]
    for r in rows:
        r["weight"] = weights.get(r["id"], 0)

    usable = [r for r in rows if r["available"] and not r["stale"] and r["weight"] > 0]
    total_weight = sum(r["weight"] for r in usable)
    all_weight = sum(weights.get(i.id, 0) for i in INDICATORS)

    if total_weight > 0:
        score = sum(r["score"] * r["weight"] for r in usable) / total_weight
    else:
        score = None

    coverage = (total_weight / all_weight * 100.0) if all_weight else 0.0

    # Cobertura POR CATEGORÍA, no solo global. Importa porque los indicadores que
    # faltan nunca están repartidos al azar: si Flujos y Sentimiento están al 0%,
    # el score agregado es en realidad un score de las categorías que sí tienen
    # datos, y eso hay que poder verlo.
    by_cat: dict[str, dict[str, Any]] = {}
    for r in rows:
        c = by_cat.setdefault(
            r["category"],
            {
                "key": r["category"], "label": r["category_label"],
                "w": 0, "acc": 0.0, "n": 0, "w_total": 0, "n_total": 0,
            },
        )
        c["w_total"] += r["weight"]
        c["n_total"] += 1
        if r["available"] and not r["stale"] and r["weight"] > 0:
            c["w"] += r["weight"]
            c["acc"] += r["score"] * r["weight"]
            c["n"] += 1
    categories = [
        {
            "key": c["key"],
            "label": c["label"],
            "score": round(c["acc"] / c["w"], 1) if c["w"] else None,
            "weight": c["w"],
            "weight_total": c["w_total"],
            "coverage_pct": round(100.0 * c["w"] / c["w_total"], 0) if c["w_total"] else 0.0,
            "count": c["n"],
            "count_total": c["n_total"],
        }
        for c in by_cat.values()
    ]
    categories.sort(key=lambda c: -(c["weight_total"] or 0))

    band_key, band_label, band_blurb = band_for(score) if score is not None else ("sin_datos", "Sin datos suficientes", "")

    triggered = [r["id"] for r in rows if r.get("triggered")]

    return {
        "score": round(score, 1) if score is not None else None,
        "band": band_key,
        "band_label": band_label,
        "band_blurb": band_blurb,
        "coverage_pct": round(coverage, 1),
        "indicators_total": len(rows),
        "indicators_usable": len(usable),
        "triggered_ids": triggered,
        "categories": categories,
        "indicators": rows,
        "weights": weights,
        "generated_at": store.now_utc(),
    }


def historical_score(weights: dict[str, int] | None = None, days: int = 3000) -> list[dict[str, Any]]:
    """Reconstruye el score día a día, para poder verlo contra suelos pasados.

    En cada fecha solo usa los indicadores que tenían dato ese día, renormalizando
    los pesos. Así el score de 2018 no se contamina con métricas que en ese
    momento no existían en la caché.
    """
    weights = weights or get_weights()
    since = (date.today() - timedelta(days=days)).isoformat()

    per_metric: dict[str, dict[str, float]] = {}
    for ind in INDICATORS:
        if weights.get(ind.id, 0) <= 0:
            continue
        series = _smoothed(store.get_series(ind.id, since=since), ind.smooth_days)
        if not series:
            continue
        per_metric[ind.id] = {
            p["d"]: interpolate(ind.anchors, float(p["value"]))
            for p in series
            if p["value"] is not None
        }

    all_dates: set[str] = set()
    for m in per_metric.values():
        all_dates.update(m)

    out: list[dict[str, Any]] = []
    for d in sorted(all_dates):
        acc = 0.0
        w = 0
        for mid, m in per_metric.items():
            if d in m:
                wt = weights.get(mid, 0)
                acc += m[d] * wt
                w += wt
        if w > 0:
            out.append({"d": d, "score": round(acc / w, 2), "coverage": w})
    return out
