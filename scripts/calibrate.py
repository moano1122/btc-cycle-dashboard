"""Calibra los anclajes de puntuación contra los suelos de ciclo REALES.

Por qué existe
--------------
Los umbrales publicados en artículos no coinciden con las series de los
proveedores: al confrontarlos, cinco indicadores resultaron estar en otra escala,
uno de ellos por un factor de casi 3. Y la creencia popular de que el precio
"nunca perfora su media de 200 semanas" es falsa: en 2022 cotizó un 34% por
debajo durante 210 días seguidos.

Este script no cree en la literatura. Deriva cada anclaje de lo que el indicador
hizo de verdad en los suelos de ciclo anteriores.

Método
------
Para cada indicador se busca su lectura **más extrema dentro de cada ventana de
suelo**, no en una fecha fija. Es una distinción importante: los indicadores no
tocan su extremo el mismo día. La capitulación minera de Hash Ribbons fue en
julio de 2022, cuatro meses antes del mínimo del precio, y el 21 de noviembre ese
indicador estaba exactamente en su mediana.

Dos cosas separadas, y conviene entender por qué:

**La FORMA de la escala sale de los percentiles de toda la serie.** Anclarla solo
a los suelos falla cuando hay pocos: si un indicador tiene un único suelo
conocido, la curva entre ese punto y la mediana se vuelve una recta larguísima
que regala puntuación. Pasó con la convergencia STH↔LTH, que puntuaba 85 estando
en 0.35 cuando su suelo fue 0.001.

**El UMBRAL de alerta sale de la mediana de los suelos de ciclo.** Un percentil
no significa nada por sí solo; "el indicador alcanzó el nivel de un suelo típico"
sí. Se usa la mediana y no el suelo más flojo porque en 2018 el precio apenas
rozó su media de 200 semanas (1.014) mientras que en 2022 se hundió a 0.658:
anclar al más flojo haría saltar la alerta con un simple roce.

Marzo de 2020 se registra como referencia pero **no entra en los anclajes**: fue
un shock de liquidez de dos semanas, no un suelo de ciclo por agotamiento, y
muchos indicadores no llegaron a extremos. Incluirlo aflojaría la escala.

Uso
---
    python scripts/calibrate.py            informe comparativo
    python scripts/calibrate.py --emit     bloques listos para catalog.py
"""

from __future__ import annotations

import statistics as st
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend import store  # noqa: E402
from backend.catalog import INDICATORS  # noqa: E402

# Suelos de ciclo por agotamiento. Son los que calibran la escala.
CICLOS: dict[str, tuple[str, str]] = {
    "2015": ("2014-10-01", "2015-03-31"),
    "2018": ("2018-10-01", "2019-02-28"),
    "2022": ("2022-06-01", "2023-01-31"),
}
# Shock de liquidez, no suelo de ciclo. Se informa, no se usa para anclar.
COVID = ("2020-03-01", "2020-04-15")

MINIMO_PUNTOS = 60
MINIMO_CICLOS = 0


def percentil(ordenados: list[float], p: float) -> float:
    if p <= 0:
        return ordenados[0]
    if p >= 100:
        return ordenados[-1]
    k = (len(ordenados) - 1) * p / 100.0
    lo, hi = int(k), min(int(k) + 1, len(ordenados) - 1)
    return ordenados[lo] + (ordenados[hi] - ordenados[lo]) * (k - lo)


def extremo_en(pts: list[dict], ventana: tuple[str, str], direccion: str):
    dentro = [p for p in pts if ventana[0] <= p["d"] <= ventana[1]]
    if not dentro:
        return None
    elegido = (
        min(dentro, key=lambda p: p["value"])
        if direccion == "below"
        else max(dentro, key=lambda p: p["value"])
    )
    return elegido["value"], elegido["d"]


def build(ind):
    pts = [p for p in store.get_series(ind.id) if p["value"] is not None]
    if len(pts) < MINIMO_PUNTOS:
        return None

    suelos = {}
    for nombre, ventana in CICLOS.items():
        e = extremo_en(pts, ventana, ind.trigger_dir)
        if e:
            suelos[nombre] = e
    abajo = ind.trigger_dir == "below"
    todos = sorted(p["value"] for p in pts)

    if suelos:
        umbral = st.median([v for v, _ in suelos.values()])
    else:
        # Series que no existían en ningún suelo de ciclo —los ETF spot nacieron
        # en 2024— no tienen contra qué anclarse. El umbral cae en el percentil 8
        # de su propia distribución: dice "esta lectura está entre las más
        # extremas que este indicador ha registrado", que es lo máximo que se
        # puede afirmar honestamente sin un precedente de suelo.
        umbral = percentil(todos, 8 if abajo else 92)
    # Percentiles medidos desde el lado de suelo del indicador.
    def q(p):
        return percentil(todos, p if abajo else 100 - p)

    # Rejilla de percentiles: da forma a la curva usando toda la historia
    # disponible, sin depender de cuántos suelos se conozcan.
    crudos = [(q(0), 100.0), (q(2), 94.0), (q(6), 86.0), (q(13), 76.0),
              (q(25), 64.0), (q(50), 48.0), (q(75), 28.0), (q(90), 12.0), (q(100), 0.0)]

    # Se ordenan por valor y se descartan los que romperían la monotonía: con
    # pocos suelos es posible que un percentil caiga entre dos anclajes de suelo.
    crudos.sort(key=lambda t: t[0], reverse=not abajo)
    limpios: list[tuple[float, float]] = []
    for v, s in crudos:
        if limpios and (v == limpios[-1][0] or s >= limpios[-1][1]):
            continue
        limpios.append((v, s))
    # Los extremos de la serie deben marcar los extremos de la escala. Si el
    # percentil más alto y el más bajo coinciden en valor —pasa cuando una
    # métrica pasa mucho tiempo pegada a cero, como el % de manos largas en
    # pérdida durante un bull— la deduplicación deja el extremo sin su
    # puntuación límite y la escala se queda coja.
    if limpios:
        limpios[0] = (limpios[0][0], 100.0)
        limpios[-1] = (limpios[-1][0], 0.0)
    anchors = sorted(limpios, key=lambda t: t[0])

    cur = pts[-1]["value"]
    rank = 100.0 * sum(1 for v in todos if v < cur) / len(todos)
    covid = extremo_en(pts, COVID, ind.trigger_dir)

    return anchors, {
        "n": len(pts),
        "desde": pts[0]["d"],
        "años": round((date.fromisoformat(pts[-1]["d"]) - date.fromisoformat(pts[0]["d"])).days / 365.25, 1),
        "suelos": suelos,
        "covid": covid,
        "trigger": umbral,
        "hoy": cur,
        "hoy_pctil": round(rank, 1),
    }


def main() -> None:
    emit = "--emit" in sys.argv
    if not emit:
        print(f"{'indicador':<24}{'años':>6}{'ciclos':>8}   suelos por ciclo")
    for ind in INDICATORS:
        res = build(ind)
        if res is None:
            if not emit:
                print(f"{ind.id:<24}{'—':>6}{'0':>8}   sin datos suficientes")
            continue
        anchors, i = res
        if emit:
            cuerpo = ", ".join(f"({v:g}, {s:g})" for v, s in anchors)
            print(f"    # {ind.id}: {len(i['suelos'])} ciclos, {i['años']} años")
            print(f"    anchors=[{cuerpo}],")
            print(f"    trigger={i['trigger']:g},")
        else:
            detalle = "  ".join(f"{k}:{v:.4g}({d[:7]})" for k, (v, d) in sorted(i["suelos"].items()))
            print(f"{ind.id:<24}{i['años']:>6}{len(i['suelos']):>8}   {detalle}")


if __name__ == "__main__":
    main()
