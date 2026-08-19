"""API HTTP y servidor del dashboard."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import date, timedelta
from typing import Any

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import alerts, refresh, scoring, store
from .catalog import BY_ID, INDICATORS
from .config import CONTENT_DIR, FRONTEND_DIR, TELEGRAM_ENABLED
from .sources import bitcoin_data, market

log = logging.getLogger(__name__)

# Una hora, no seis. El cupo del plan gratuito se renueva por ventana horaria
# (10 peticiones), así que intentarlo cada hora es lo que permite ir rellenando
# el catálogo sin excederse: el refresco ya respeta el presupuesto y se salta lo
# que está fresco, de modo que un intento sin cupo disponible no cuesta nada.
REFRESH_INTERVAL_SECONDS = 3600


async def _background_loop() -> None:
    """Refresca periódicamente y evalúa alertas. Tolera fallos sin morir."""
    while True:
        try:
            await asyncio.to_thread(refresh.refresh)
            await asyncio.to_thread(alerts.evaluate, True)
        except Exception:  # noqa: BLE001
            log.exception("ciclo de refresco en segundo plano falló")
        await asyncio.sleep(REFRESH_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    store.init()
    task = asyncio.create_task(_background_loop())
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(title="BTC Indicators", lifespan=lifespan)


# --------------------------------------------------------------------------
# Datos
# --------------------------------------------------------------------------
@app.get("/api/snapshot")
async def api_snapshot() -> dict[str, Any]:
    snap = await asyncio.to_thread(scoring.snapshot)
    spot = await asyncio.to_thread(market.fetch_spot_price)
    latest_close = await asyncio.to_thread(store.get_latest, "btc_price")
    snap["price"] = {
        "spot": spot,
        "last_close": latest_close["value"] if latest_close else None,
        "last_close_date": latest_close["d"] if latest_close else None,
    }
    snap["budget"] = await asyncio.to_thread(bitcoin_data.budget_status)
    snap["telegram_enabled"] = TELEGRAM_ENABLED
    return snap


@app.get("/api/series/{metric_id}")
async def api_series(metric_id: str, days: int = 1800, with_price: bool = True) -> dict[str, Any]:
    if metric_id not in BY_ID and metric_id != "btc_price":
        raise HTTPException(404, f"indicador desconocido: {metric_id}")
    since = (date.today() - timedelta(days=max(30, min(days, 8000)))).isoformat()

    ind = BY_ID.get(metric_id)
    raw = await asyncio.to_thread(store.get_series, metric_id, since)
    if ind and ind.smooth_days > 1:
        raw = scoring._smoothed(raw, ind.smooth_days)

    payload: dict[str, Any] = {
        "id": metric_id,
        "points": raw,
        "trigger": ind.trigger if ind else None,
        "trigger_dir": ind.trigger_dir if ind else None,
        "historic": ind.historic if ind else {},
        "anchors": ind.anchors if ind else [],
        "label": ind.label if ind else "Precio BTC",
        "decimals": ind.decimals if ind else 0,
        "unit": ind.unit if ind else " USD",
    }
    if with_price:
        payload["price"] = await asyncio.to_thread(store.get_series, "btc_price", since)
    return payload


@app.get("/api/score-history")
async def api_score_history(days: int = 3000) -> dict[str, Any]:
    hist = await asyncio.to_thread(scoring.historical_score, None, days)
    since = (date.today() - timedelta(days=days)).isoformat()
    price = await asyncio.to_thread(store.get_series, "btc_price", since)
    return {"score": hist, "price": price, "bands": scoring.BANDS}


# --------------------------------------------------------------------------
# Pesos
# --------------------------------------------------------------------------
@app.get("/api/weights")
async def api_get_weights() -> dict[str, int]:
    return await asyncio.to_thread(scoring.get_weights)


@app.post("/api/weights")
async def api_set_weights(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    weights = await asyncio.to_thread(scoring.save_weights, payload.get("weights", {}))
    snap = await asyncio.to_thread(scoring.snapshot, weights)
    return {"weights": weights, "snapshot": snap}


@app.post("/api/weights/reset")
async def api_reset_weights() -> dict[str, Any]:
    weights = await asyncio.to_thread(scoring.reset_weights)
    snap = await asyncio.to_thread(scoring.snapshot, weights)
    return {"weights": weights, "snapshot": snap}


# --------------------------------------------------------------------------
# Operación
# --------------------------------------------------------------------------
@app.post("/api/refresh")
async def api_refresh(force: bool = False) -> dict[str, Any]:
    report = await asyncio.to_thread(refresh.refresh, force=force)
    events = await asyncio.to_thread(alerts.evaluate, True)
    report["alerts_fired"] = events
    return report


@app.get("/api/status")
async def api_status() -> dict[str, Any]:
    states = await asyncio.to_thread(store.get_metric_states)
    budget = await asyncio.to_thread(bitcoin_data.budget_status)
    missing = await asyncio.to_thread(refresh.missing_metrics)
    return {
        "budget": budget,
        "metric_states": states,
        "missing": missing,
        "telegram_enabled": TELEGRAM_ENABLED,
        "catalog_size": len(INDICATORS),
    }


@app.get("/api/alerts")
async def api_alerts(limit: int = 50) -> dict[str, Any]:
    return {"events": await asyncio.to_thread(store.recent_alerts, limit)}


@app.post("/api/alerts/test")
async def api_alerts_test() -> dict[str, Any]:
    return await asyncio.to_thread(alerts.test_telegram)


@app.get("/api/tutorial/{metric_id}")
async def api_tutorial(metric_id: str) -> JSONResponse:
    if metric_id not in BY_ID:
        raise HTTPException(404, "indicador desconocido")
    path = CONTENT_DIR / "tutorials" / f"{metric_id}.md"
    if not path.exists():
        return JSONResponse({"markdown": "", "missing": True})
    return JSONResponse({"markdown": path.read_text(encoding="utf-8"), "missing": False})


# --------------------------------------------------------------------------
# Frontend estático
# --------------------------------------------------------------------------
@app.middleware("http")
async def sin_cache_estaticos(request, call_next):
    """Obliga al navegador a revalidar el CSS y el JS en cada carga.

    Sin esto, cualquier cambio en el frontend queda invisible detrás de la caché
    del navegador y hay que recargar a mano con Ctrl+Shift+R. En una aplicación
    local el costo de revalidar es cero y evita depurar un problema que no
    existe.
    """
    response = await call_next(request)
    if request.url.path.startswith("/static") or request.url.path == "/":
        response.headers["Cache-Control"] = "no-cache, must-revalidate"
    return response


@app.get("/")
async def index() -> HTMLResponse:
    """Sirve el dashboard con las URLs de CSS y JS versionadas.

    Se añade `?v=<fecha de modificación>` a cada estático. Sin esto, un cambio en
    el frontend puede quedar invisible detrás de la caché del navegador: la URL
    es la misma, así que el navegador reutiliza la copia vieja y uno acaba
    depurando un problema que ya estaba arreglado. Al cambiar la URL con cada
    edición, la caché deja de ser un factor.
    """
    html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
    for asset in ("app.css", "app.js"):
        ruta = FRONTEND_DIR / asset
        version = int(ruta.stat().st_mtime) if ruta.exists() else 0
        html = html.replace(f"/static/{asset}", f"/static/{asset}?v={version}")
    return HTMLResponse(html)


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
