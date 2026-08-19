"""Arranca el dashboard y abre el navegador.

    python run.py              -> servidor + navegador
    python run.py --no-browser -> solo servidor
    python run.py --refresh    -> un ciclo de refresco y salir (para tareas programadas)
    python run.py --status     -> diagnóstico en consola
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import threading
import webbrowser

import uvicorn

from backend import alerts, refresh, scoring, store
from backend.config import HOST, PORT
from backend.sources import bitcoin_data

# La consola de Windows usa cp1252 y revienta al imprimir los emoji de las
# alertas. Forzamos UTF-8 en la salida para que `--refresh` funcione dentro de
# una tarea programada sin fallar por un carácter.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


def cmd_refresh() -> None:
    store.init()
    report = refresh.refresh()
    events = alerts.evaluate(send=True)
    report["alerts_fired"] = [e["title"] for e in events]
    print(json.dumps(report, indent=2, ensure_ascii=False))


def cmd_status() -> None:
    store.init()
    budget = bitcoin_data.budget_status()
    snap = scoring.snapshot()
    print("\n=== PRESUPUESTO DE API ===")
    print(f"  API key configurada : {'sí' if budget['has_key'] else 'NO'}")
    print(f"  Última hora         : {budget['used_hour']}/{budget['limit_hour']}")
    print(f"  Últimas 24h         : {budget['used_day']}/{budget['limit_day']}")

    print("\n=== SCORE DE SUELO ===")
    if snap["score"] is None:
        print("  Sin datos suficientes. Ejecute: python run.py --refresh")
    else:
        print(f"  Score      : {snap['score']}/100  ->  {snap['band_label']}")
        print(f"  Cobertura  : {snap['coverage_pct']}%  "
              f"({snap['indicators_usable']}/{snap['indicators_total']} indicadores)")

    print("\n=== INDICADORES ===")
    for r in sorted(snap["indicators"], key=lambda x: -(x["weight"] or 0)):
        if r["available"]:
            flag = "!" if r.get("triggered") else (" " if not r["stale"] else "~")
            val = f"{r['value']:,.{r['decimals']}f}{r['unit']}"
            print(f"  {flag} {r['label']:<32} {val:>16}   score {r['score']:>5}  peso {r['weight']:>2}  {r['as_of']}")
        else:
            print(f"  ? {r['label']:<32} {'sin datos':>16}   {r['detail'][:40]}")
    print("\n  ! = umbral cruzado    ~ = dato rancio    ? = sin datos\n")


def cmd_serve(open_browser: bool) -> None:
    store.init()
    url = f"http://{HOST}:{PORT}/"
    if open_browser:
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    print(f"\n  BTC Indicators  ->  {url}\n")
    uvicorn.run("backend.api:app", host=HOST, port=PORT, log_level="warning")


def main() -> None:
    parser = argparse.ArgumentParser(description="BTC Indicators")
    parser.add_argument("--no-browser", action="store_true", help="no abrir el navegador")
    parser.add_argument("--refresh", action="store_true", help="refrescar datos y salir")
    parser.add_argument("--status", action="store_true", help="diagnóstico en consola")
    args = parser.parse_args()

    if args.refresh:
        cmd_refresh()
    elif args.status:
        cmd_status()
    else:
        cmd_serve(not args.no_browser)


if __name__ == "__main__":
    main()
