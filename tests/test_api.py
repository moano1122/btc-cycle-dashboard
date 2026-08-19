"""Tests de los endpoints HTTP.

Se instancia el TestClient sin usarlo como gestor de contexto a propósito: eso
evita que arranque el `lifespan`, que lanzaría el ciclo de refresco en segundo
plano y saldría a la red. Aquí no se toca la red en ningún test.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from backend import store
from backend.api import app
from backend.catalog import INDICATORS
from backend.sources import market


def hoy(delta=0):
    return (datetime.now(timezone.utc).date() - timedelta(days=delta)).isoformat()


@pytest.fixture()
def client(db, monkeypatch):
    monkeypatch.setattr(market, "fetch_spot_price", lambda: 64000.0)
    return TestClient(app)


@pytest.fixture()
def con_datos(client, serie):
    serie("mvrv_zscore", [(hoy(1), 0.35), (hoy(), 0.354)])
    serie("btc_price", [(hoy(1), 63000.0), (hoy(), 64500.0)])
    return client


class TestSnapshot:
    def test_responde_con_la_forma_esperada(self, client):
        r = client.get("/api/snapshot")
        assert r.status_code == 200
        d = r.json()
        for clave in (
            "score", "band", "band_label", "coverage_pct", "indicators",
            "categories", "weights", "price", "budget", "telegram_enabled",
        ):
            assert clave in d, f"falta {clave}"

    def test_incluye_todo_el_catalogo_aunque_falten_datos(self, client):
        d = client.get("/api/snapshot").json()
        assert len(d["indicators"]) == len(INDICATORS)

    def test_sin_datos_devuelve_score_nulo_y_no_un_cero(self, client):
        # Un cero se leería como "euforia"; el nulo dice la verdad.
        d = client.get("/api/snapshot").json()
        assert d["score"] is None

    def test_expone_el_precio_spot_y_el_ultimo_cierre(self, con_datos):
        d = con_datos.get("/api/snapshot").json()
        assert d["price"]["spot"] == 64000.0
        assert d["price"]["last_close"] == 64500.0
        assert d["price"]["last_close_date"] == hoy()

    def test_cada_indicador_declara_cuantos_ciclos_lo_respaldan(self, con_datos):
        # Es la información que permite juzgar cuánto pesa cada umbral: uno
        # derivado de tres suelos vale mucho más que uno derivado de cero.
        d = con_datos.get("/api/snapshot").json()
        for r in d["indicators"]:
            assert isinstance(r["ciclos"], int) and 0 <= r["ciclos"] <= 3
        con_respaldo = [r for r in d["indicators"] if r["ciclos"] >= 3]
        assert len(con_respaldo) >= 8, "deberían quedar al menos 8 con tres ciclos"

    def test_cada_indicador_declara_su_procedencia_de_datos(self, con_datos):
        d = con_datos.get("/api/snapshot").json()
        fila = next(r for r in d["indicators"] if r["id"] == "mvrv_zscore")
        assert fila["available"] is True
        assert fila["stale"] is False
        assert fila["as_of"] == hoy()


class TestSeries:
    def test_devuelve_la_serie_y_el_precio_de_fondo(self, con_datos):
        d = con_datos.get("/api/series/mvrv_zscore").json()
        assert len(d["points"]) == 2
        assert len(d["price"]) == 2
        assert d["trigger"] is not None

    def test_puede_omitirse_el_precio(self, con_datos):
        d = con_datos.get("/api/series/mvrv_zscore?with_price=false").json()
        assert "price" not in d

    def test_indicador_desconocido_da_404(self, client):
        assert client.get("/api/series/no_existe").status_code == 404

    def test_acepta_la_serie_de_precio(self, con_datos):
        assert con_datos.get("/api/series/btc_price").status_code == 200

    def test_recorta_el_rango_de_dias_pedido(self, client, serie):
        serie("mvrv_zscore", [(hoy(500), 1.0), (hoy(), 0.3)])
        d = client.get("/api/series/mvrv_zscore?days=30").json()
        assert len(d["points"]) == 1, "no debe devolver puntos fuera de la ventana"

    def test_aplica_el_suavizado_declarado(self, client, serie):
        # aSOPR se suaviza a 30 días: el valor devuelto debe ser la media, no
        # el dato crudo del último día.
        pts = [(hoy(5 - i), 1.0 if i < 5 else 2.0) for i in range(6)]
        serie("asopr", pts)
        d = client.get("/api/series/asopr").json()
        assert d["points"][-1]["value"] < 2.0


class TestPesos:
    def test_lee_los_pesos_por_defecto(self, client):
        w = client.get("/api/weights").json()
        assert w["mvrv_zscore"] == 12

    def test_guarda_y_recalcula_en_la_misma_respuesta(self, con_datos):
        r = con_datos.post("/api/weights", json={"weights": {"mvrv_zscore": 20}})
        assert r.status_code == 200
        d = r.json()
        assert d["weights"]["mvrv_zscore"] == 20
        assert "snapshot" in d

    def test_restaura_los_valores_por_defecto(self, con_datos):
        con_datos.post("/api/weights", json={"weights": {"mvrv_zscore": 1}})
        d = con_datos.post("/api/weights/reset").json()
        assert d["weights"]["mvrv_zscore"] == 12

    def test_ignora_basura_sin_romperse(self, client):
        r = client.post("/api/weights", json={"weights": {"xx": "yy", "mvrv_zscore": None}})
        assert r.status_code == 200


class TestEstado:
    def test_reporta_cupo_y_metricas_faltantes(self, client):
        d = client.get("/api/status").json()
        assert d["catalog_size"] == len(INDICATORS)
        assert d["budget"]["limit_day"] > 0
        assert len(d["missing"]) == len(INDICATORS), "sin datos, todo debe faltar"

    def test_las_metricas_con_datos_dejan_de_faltar(self, con_datos):
        d = con_datos.get("/api/status").json()
        assert "mvrv_zscore" not in d["missing"]


class TestScoreHistorico:
    def test_devuelve_score_precio_y_bandas(self, con_datos):
        d = con_datos.get("/api/score-history?days=90").json()
        assert "score" in d and "price" in d and "bands" in d
        assert len(d["score"]) >= 1

    def test_cada_punto_lleva_su_cobertura(self, con_datos):
        d = con_datos.get("/api/score-history?days=90").json()
        for p in d["score"]:
            assert p["coverage"] > 0


class TestTutoriales:
    def test_devuelve_el_markdown(self, client):
        d = client.get("/api/tutorial/mvrv_zscore").json()
        assert d["missing"] is False
        assert len(d["markdown"]) > 500

    def test_indicador_desconocido_da_404(self, client):
        assert client.get("/api/tutorial/no_existe").status_code == 404

    def test_todos_los_indicadores_tienen_tutorial_servible(self, client):
        for ind in INDICATORS:
            r = client.get(f"/api/tutorial/{ind.id}")
            assert r.status_code == 200, ind.id
            assert r.json()["missing"] is False, f"{ind.id} no tiene tutorial servido"


class TestAlertas:
    def test_lista_vacia_al_principio(self, client):
        assert client.get("/api/alerts").json()["events"] == []

    def test_devuelve_los_eventos_registrados(self, client):
        store.add_alert_event(
            metric_id="mvrv_zscore", kind="cross_in", severity="signal",
            title="prueba", message="cuerpo", value=1.0,
        )
        eventos = client.get("/api/alerts").json()["events"]
        assert len(eventos) == 1 and eventos[0]["title"] == "prueba"

    def test_la_prueba_de_telegram_no_revienta_sin_credenciales(self, client):
        r = client.post("/api/alerts/test")
        assert r.status_code == 200
        assert r.json()["ok"] in (True, False)


class TestFrontend:
    def test_sirve_el_dashboard(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "BTC Indicators" in r.text

    def test_versiona_los_estaticos_para_esquivar_la_cache(self, client):
        # Sin versionado, un cambio en el frontend queda invisible detrás de la
        # caché del navegador y uno depura un problema ya arreglado.
        html = client.get("/").text
        assert "/static/app.js?v=" in html
        assert "/static/app.css?v=" in html

    def test_la_version_cambia_al_editar_el_archivo(self, client, tmp_path, monkeypatch):
        import os
        from backend import api

        ruta = api.FRONTEND_DIR / "app.js"
        antes = client.get("/").text
        v1 = antes.split("/static/app.js?v=")[1].split('"')[0]
        os.utime(ruta, (int(v1) + 500, int(v1) + 500))
        try:
            v2 = client.get("/").text.split("/static/app.js?v=")[1].split('"')[0]
            assert v2 != v1
        finally:
            os.utime(ruta, (int(v1), int(v1)))

    def test_los_estaticos_piden_revalidacion(self, client):
        r = client.get("/static/app.js")
        assert "no-cache" in (r.headers.get("cache-control") or "")

    @pytest.mark.parametrize("recurso", ["app.css", "app.js", "index.html"])
    def test_sirve_los_estaticos(self, client, recurso):
        assert client.get(f"/static/{recurso}").status_code == 200
