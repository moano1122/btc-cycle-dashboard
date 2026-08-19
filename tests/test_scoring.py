"""Tests del motor de puntuación: interpolación, bandas, agregación y pesos."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from backend import scoring
from backend.catalog import BY_ID

ANCHORS = [(0.0, 100.0), (1.0, 50.0), (2.0, 0.0)]


def hoy(delta=0):
    return (datetime.now(timezone.utc).date() - timedelta(days=delta)).isoformat()


class TestInterpolate:
    def test_acierta_los_anclajes_exactos(self):
        for v, s in ANCHORS:
            assert scoring.interpolate(ANCHORS, v) == pytest.approx(s)

    def test_interpola_linealmente_entre_anclajes(self):
        assert scoring.interpolate(ANCHORS, 0.5) == pytest.approx(75.0)
        assert scoring.interpolate(ANCHORS, 1.5) == pytest.approx(25.0)

    def test_satura_y_no_extrapola(self):
        # Un valor nunca visto no debe producir puntuaciones fuera de 0-100:
        # inventar precisión donde no hay historia sería peor que inútil.
        assert scoring.interpolate(ANCHORS, -99.0) == 100.0
        assert scoring.interpolate(ANCHORS, 99.0) == 0.0

    def test_es_indiferente_al_orden_de_los_anclajes(self):
        assert scoring.interpolate(list(reversed(ANCHORS)), 0.5) == pytest.approx(75.0)

    def test_soporta_valores_negativos(self):
        a = [(-0.36, 100.0), (0.0, 80.0), (3.35, 0.0)]
        assert scoring.interpolate(a, -0.36) == pytest.approx(100.0)
        assert scoring.interpolate(a, -0.18) == pytest.approx(90.0)
        assert scoring.interpolate(a, 3.35) == pytest.approx(0.0)


class TestBandas:
    @pytest.mark.parametrize(
        "score,esperada",
        [
            (100, "capitulacion"),
            (88, "capitulacion"),
            (87.9, "suelo_probable"),
            (75, "suelo_probable"),
            (60, "acumulacion"),
            (45, "valor"),
            (28, "neutral"),
            (15, "caro"),
            (0, "euforia"),
        ],
    )
    def test_limites_de_banda(self, score, esperada):
        assert scoring.band_for(score)[0] == esperada

    def test_toda_banda_tiene_etiqueta_y_explicacion(self):
        for s in range(0, 101, 5):
            key, label, blurb = scoring.band_for(s)
            assert key and label and blurb


class TestSuavizado:
    def test_media_movil_expansiva_al_principio(self):
        pts = [{"d": "2026-01-0%d" % i, "value": float(i)} for i in range(1, 6)]
        out = scoring._smoothed(pts, 3)
        assert out[0]["value"] == pytest.approx(1.0)
        assert out[1]["value"] == pytest.approx(1.5)
        assert out[2]["value"] == pytest.approx(2.0)
        assert out[4]["value"] == pytest.approx(4.0)

    def test_ventana_uno_no_altera_la_serie(self):
        pts = [{"d": "2026-01-01", "value": 7.0}]
        assert scoring._smoothed(pts, 1) == pts

    def test_descarta_nulos(self):
        pts = [{"d": "2026-01-01", "value": None}, {"d": "2026-01-02", "value": 4.0}]
        out = scoring._smoothed(pts, 2)
        assert len(out) == 1 and out[0]["value"] == 4.0


class TestSnapshot:
    def test_sin_datos_no_inventa_un_score(self, db):
        snap = scoring.snapshot()
        assert snap["score"] is None
        assert snap["coverage_pct"] == 0.0
        assert snap["band"] == "sin_datos"

    def test_renormaliza_por_cobertura(self, serie):
        serie("mvrv_zscore", [(hoy(), -0.35)])
        snap = scoring.snapshot()
        fila = next(r for r in snap["indicators"] if r["id"] == "mvrv_zscore")
        assert fila["score"] == pytest.approx(snap["score"], abs=0.05)
        assert snap["indicators_usable"] == 1
        assert 0 < snap["coverage_pct"] < 20

    def test_los_datos_rancios_no_entran_al_score(self, serie):
        serie("mvrv_zscore", [(hoy(40), -0.35)])
        snap = scoring.snapshot()
        fila = next(r for r in snap["indicators"] if r["id"] == "mvrv_zscore")
        assert fila["stale"] is True
        assert snap["score"] is None, "un dato de hace 40 dias no debe puntuar"

    def test_peso_cero_excluye_el_indicador(self, serie):
        serie("mvrv_zscore", [(hoy(), -0.35)])
        serie("nupl", [(hoy(), -0.30)])
        scoring.save_weights({"mvrv_zscore": 0})
        snap = scoring.snapshot()
        assert snap["indicators_usable"] == 1

    def test_ponderacion_correcta_con_dos_indicadores(self, serie):
        # mvrv_zscore puntua 100 con peso 12; drawdown puntua 0 con peso 5.
        scoring.reset_weights()
        serie("mvrv_zscore", [(hoy(), BY_ID["mvrv_zscore"].anchors[0][0])])
        serie("drawdown_from_ath", [(hoy(), 0.0)])
        snap = scoring.snapshot()
        w1 = BY_ID["mvrv_zscore"].weight
        w2 = BY_ID["drawdown_from_ath"].weight
        assert snap["score"] == pytest.approx(100 * w1 / (w1 + w2), abs=0.3)

    def test_detecta_el_cruce_de_umbral(self, serie):
        ind = BY_ID["mvrv_zscore"]
        serie("mvrv_zscore", [(hoy(), ind.trigger - 0.05)])
        assert "mvrv_zscore" in scoring.snapshot()["triggered_ids"]

    def test_calcula_la_distancia_al_umbral(self, serie):
        ind = BY_ID["mvrv_zscore"]
        serie("mvrv_zscore", [(hoy(), ind.trigger + 0.10)])
        fila = next(r for r in scoring.snapshot()["indicators"] if r["id"] == "mvrv_zscore")
        assert fila["triggered"] is False
        assert fila["gap"] == pytest.approx(0.10)

    def test_umbral_hacia_arriba_dispara_al_superarlo(self, serie):
        ind = BY_ID["supply_in_loss_pct"]
        assert ind.trigger_dir == "above"
        serie("supply_in_loss_pct", [(hoy(), ind.trigger + 1)])
        assert "supply_in_loss_pct" in scoring.snapshot()["triggered_ids"]

    def test_reporta_variacion_a_30_dias(self, serie):
        pts = [(hoy(40 - i), 1.0 + i * 0.01) for i in range(41)]
        serie("mvrv_zscore", pts)
        fila = next(r for r in scoring.snapshot()["indicators"] if r["id"] == "mvrv_zscore")
        assert fila["delta_30d"] == pytest.approx(0.30, abs=0.01)


class TestPesos:
    def test_recorta_al_rango_valido(self, db):
        w = scoring.save_weights({"mvrv_zscore": 999, "nupl": -5})
        assert w["mvrv_zscore"] == 20
        assert w["nupl"] == 0

    def test_ignora_ids_desconocidos(self, db):
        assert "no_existe" not in scoring.save_weights({"no_existe": 5})

    def test_ignora_valores_no_numericos(self, db):
        w = scoring.save_weights({"mvrv_zscore": "abc"})
        assert w["mvrv_zscore"] == BY_ID["mvrv_zscore"].weight

    def test_persiste_y_restaura(self, db):
        scoring.save_weights({"mvrv_zscore": 3})
        assert scoring.get_weights()["mvrv_zscore"] == 3
        assert scoring.reset_weights()["mvrv_zscore"] == BY_ID["mvrv_zscore"].weight


class TestScoreHistorico:
    def test_renormaliza_en_cada_fecha(self, serie):
        # El 1 de enero solo hay un indicador; el 2 hay dos. El score de cada
        # fecha debe usar solo lo disponible ese dia, sin contaminarse.
        scoring.reset_weights()
        top = BY_ID["mvrv_zscore"].anchors[0][0]
        serie("mvrv_zscore", [("2026-01-01", top), ("2026-01-02", top)])
        serie("drawdown_from_ath", [("2026-01-02", 0.0)])
        hist = {p["d"]: p for p in scoring.historical_score(days=5000)}
        w1 = BY_ID["mvrv_zscore"].weight
        w2 = BY_ID["drawdown_from_ath"].weight
        assert hist["2026-01-01"]["score"] == pytest.approx(100.0)
        assert hist["2026-01-01"]["coverage"] == w1
        assert hist["2026-01-02"]["score"] == pytest.approx(100 * w1 / (w1 + w2), abs=0.3)
        assert hist["2026-01-02"]["coverage"] == w1 + w2
