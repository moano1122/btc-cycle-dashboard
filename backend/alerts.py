"""Evaluación de disparos y envío por Telegram.

Tres reglas que evitan que esto se vuelva ruido inútil:

1. **Solo se avisa en el cruce, no mientras dure la condición.** El estado
   anterior de cada indicador se guarda en SQLite, así que si el MVRV Z-Score
   lleva tres semanas bajo cero usted recibió un mensaje, no veintiuno.

2. **Histéresis del 3%.** Un indicador que oscila justo encima y justo debajo de
   su umbral generaría un mensaje por chequeo. Para armarse necesita cruzar el
   umbral; para desarmarse necesita alejarse un 3% adicional.

3. **Los datos rancios no disparan.** Si una métrica lleva días sin actualizarse
   no se evalúa: una alerta basada en un dato viejo es peor que ninguna alerta.
"""

from __future__ import annotations

import html
import logging
from typing import Any

import httpx

from . import scoring, store
from .catalog import BY_ID
from .config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_ENABLED

log = logging.getLogger(__name__)

HYSTERESIS = 0.03  # 3%


def _armed_key(metric_id: str) -> str:
    return f"{metric_id}:armed"


def _is_armed(metric_id: str) -> bool:
    return store.get_alert_state(_armed_key(metric_id)) == "1"


def _set_armed(metric_id: str, armed: bool) -> None:
    store.set_alert_state(_armed_key(metric_id), "1" if armed else "0")


def _crosses(ind_id: str, value: float, trigger: float, direction: str, armed: bool) -> bool | None:
    """Devuelve True si debe armarse, False si debe desarmarse, None si no cambia."""
    margin = abs(trigger) * HYSTERESIS if trigger else HYSTERESIS
    if direction == "below":
        if not armed and value <= trigger:
            return True
        if armed and value > trigger + margin:
            return False
    else:
        if not armed and value >= trigger:
            return True
        if armed and value < trigger - margin:
            return False
    return None


def _fmt(value: float, decimals: int, unit: str) -> str:
    return f"{value:,.{decimals}f}{unit}"


def evaluate(send: bool = True) -> list[dict[str, Any]]:
    """Revisa todos los indicadores y el score. Devuelve los eventos nuevos."""
    snap = scoring.snapshot()
    events: list[dict[str, Any]] = []

    for row in snap["indicators"]:
        if not row["available"] or row["stale"]:
            continue
        ind = BY_ID[row["id"]]
        armed = _is_armed(ind.id)
        change = _crosses(ind.id, row["value"], ind.trigger, ind.trigger_dir, armed)
        if change is None:
            continue

        _set_armed(ind.id, change)
        arrow = "por debajo de" if ind.trigger_dir == "below" else "por encima de"
        val = _fmt(row["value"], ind.decimals, ind.unit)
        thr = _fmt(ind.trigger, ind.decimals, ind.unit)

        if change:
            title = f"🟢 {ind.label} cruzó su umbral de suelo"
            msg = (
                f"{ind.label} está en {val}, {arrow} su umbral de {thr}.\n\n"
                f"{ind.summary}\n\n"
                f"Score agregado actual: {snap['score']} ({snap['band_label']})."
            )
            severity = "signal"
        else:
            title = f"⚪ {ind.label} salió de su zona de suelo"
            msg = f"{ind.label} volvió a {val}, fuera de su umbral de {thr}."
            severity = "info"

        eid = store.add_alert_event(
            metric_id=ind.id,
            kind="cross_in" if change else "cross_out",
            severity=severity,
            title=title,
            message=msg,
            value=row["value"],
        )
        events.append({"id": eid, "title": title, "message": msg, "severity": severity})

    # --- Cambio de banda del score agregado ---------------------------------
    if snap["score"] is not None:
        prev_band = store.get_alert_state("score:band")
        if prev_band != snap["band"]:
            store.set_alert_state("score:band", snap["band"])
            if prev_band is not None:  # el primer arranque no genera alerta
                title = f"📊 El score de suelo entró en «{snap['band_label']}»"
                msg = (
                    f"Score agregado: {snap['score']}/100 ({snap['band_label']}).\n"
                    f"{snap['band_blurb']}\n\n"
                    f"Cobertura de datos: {snap['coverage_pct']}% "
                    f"({snap['indicators_usable']}/{snap['indicators_total']} indicadores)."
                )
                eid = store.add_alert_event(
                    metric_id=None,
                    kind="score_band",
                    severity="signal" if snap["score"] >= 60 else "info",
                    title=title,
                    message=msg,
                    value=snap["score"],
                )
                events.append({"id": eid, "title": title, "message": msg, "severity": "signal"})

    if send and events:
        for ev in events:
            if send_telegram(f"<b>{html.escape(ev['title'])}</b>\n\n{html.escape(ev['message'])}"):
                store.mark_delivered(ev["id"])

    return events


def send_telegram(text: str) -> bool:
    if not TELEGRAM_ENABLED:
        log.info("Telegram no configurado; alerta solo queda en el dashboard.")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.post(
                url,
                json={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
            )
        if resp.status_code != 200:
            log.warning("Telegram respondió %s: %s", resp.status_code, resp.text[:200])
            return False
        return True
    except Exception as exc:  # noqa: BLE001
        log.warning("no se pudo enviar a Telegram: %s", exc)
        return False


def test_telegram() -> dict[str, Any]:
    if not TELEGRAM_ENABLED:
        return {
            "ok": False,
            "detail": "Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID en el archivo .env",
        }
    ok = send_telegram(
        "<b>✅ BTC Indicators conectado</b>\n\n"
        "Si lee esto, las alertas de suelo de mercado llegarán a este chat."
    )
    return {"ok": ok, "detail": "Mensaje enviado" if ok else "Telegram rechazó el envío"}
