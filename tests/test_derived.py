"""Tests de la matemática de los indicadores derivados.

El RSI y las medias móviles se implementaron a mano en Python puro para evitar
dependencias compiladas. Eso significa que hay que demostrar que son correctos,
no suponerlo: un error de un índice en el RSI produce un número plausible pero
equivocado, y de ahí saldrían decisiones de dinero.
"""

from __future__ import annotations

import pytest

from backend import derived, store


class TestSMA:
    def test_ventana_llena_da_el_promedio(self):
        assert derived.sma([1, 2, 3, 4, 5], 5)[-1] == pytest.approx(3.0)

    def test_devuelve_none_antes_de_completar_la_ventana(self):
        out = derived.sma([1, 2, 3, 4, 5], 3)
        assert out[0] is None and out[1] is None
        assert out[2] == pytest.approx(2.0)
        assert out[3] == pytest.approx(3.0)
        assert out[4] == pytest.approx(4.0)

    def test_coincide_con_el_calculo_directo(self):
        vals = [float((i * 37) % 91) for i in range(300)]
        w = 20
        rapida = derived.sma(vals, w)
        for i in range(w - 1, len(vals)):
            lento = sum(vals[i - w + 1 : i + 1]) / w
            assert rapida[i] == pytest.approx(lento, abs=1e-9), f"desvio en i={i}"

    def test_ventana_de_uno_es_la_serie_misma(self):
        assert derived.sma([3.0, 7.0], 1) == [3.0, 7.0]


class TestWilderRSI:
    def test_serie_solo_alcista_da_cien(self):
        assert derived.wilder_rsi([float(i) for i in range(1, 40)], 14)[-1] == pytest.approx(100.0)

    def test_serie_solo_bajista_da_cero(self):
        assert derived.wilder_rsi([float(i) for i in range(40, 1, -1)], 14)[-1] == pytest.approx(0.0)

    def test_serie_demasiado_corta_devuelve_nulos(self):
        out = derived.wilder_rsi([1.0, 2.0, 3.0], 14)
        assert all(v is None for v in out)

    def test_el_primer_valor_aparece_en_el_periodo(self):
        out = derived.wilder_rsi([float(i % 7) for i in range(40)], 14)
        assert out[13] is None
        assert out[14] is not None

    def test_subidas_y_bajadas_alternas_rondan_cincuenta(self):
        # Alternar +1 / -1 no da exactamente 50: el suavizado de Wilder arrastra
        # la semilla inicial y el resultado depende de la paridad del último
        # movimiento. El valor correcto para esta serie es 48.21, y comprobamos
        # que se mantenga en el entorno de la neutralidad.
        closes = [100.0]
        for i in range(60):
            closes.append(closes[-1] + (1.0 if i % 2 == 0 else -1.0))
        assert derived.wilder_rsi(closes, 14)[-1] == pytest.approx(48.21, abs=0.05)

    def test_coincide_con_una_implementacion_independiente(self):
        # Segunda implementación escrita de otra forma, para detectar errores de
        # índice que una sola versión no revelaría.
        closes = [100.0]
        for i in range(120):
            closes.append(closes[-1] * (1 + ((i * 13) % 17 - 8) / 100.0))

        def referencia(vals, period=14):
            deltas = [vals[i] - vals[i - 1] for i in range(1, len(vals))]
            g = sum(d for d in deltas[:period] if d > 0) / period
            l = sum(-d for d in deltas[:period] if d < 0) / period
            out = [None] * len(vals)
            out[period] = 100.0 if l == 0 else 100 - 100 / (1 + g / l)
            for i in range(period, len(deltas)):
                d = deltas[i]
                g = (g * (period - 1) + max(d, 0.0)) / period
                l = (l * (period - 1) + max(-d, 0.0)) / period
                out[i + 1] = 100.0 if l == 0 else 100 - 100 / (1 + g / l)
            return out

        mio = derived.wilder_rsi(closes, 14)
        ref = referencia(closes, 14)
        for i, (a, b) in enumerate(zip(mio, ref)):
            if a is None or b is None:
                assert a is None and b is None, f"desalineado en i={i}"
            else:
                assert a == pytest.approx(b, abs=1e-9), f"desvio en i={i}"

    def test_rango_siempre_entre_cero_y_cien(self):
        closes = [100.0]
        for i in range(400):
            closes.append(max(1.0, closes[-1] + ((i * 29) % 23 - 11)))
        for v in derived.wilder_rsi(closes, 14):
            if v is not None:
                assert 0.0 <= v <= 100.0


class TestAgregacionPorPeriodo:
    def test_semanal_toma_el_ultimo_cierre_de_cada_semana(self):
        # 2026-01-05 es lunes; 2026-01-11 domingo. Misma semana ISO.
        pts = [
            {"d": "2026-01-05", "value": 1.0},
            {"d": "2026-01-08", "value": 2.0},
            {"d": "2026-01-11", "value": 3.0},
            {"d": "2026-01-12", "value": 4.0},
        ]
        out = derived._period_closes(pts, "weekly")
        assert out == [("2026-01-11", 3.0), ("2026-01-12", 4.0)]

    def test_mensual_toma_el_ultimo_cierre_de_cada_mes(self):
        pts = [
            {"d": "2026-01-05", "value": 1.0},
            {"d": "2026-01-31", "value": 2.0},
            {"d": "2026-02-02", "value": 3.0},
        ]
        out = derived._period_closes(pts, "monthly")
        assert out == [("2026-01-31", 2.0), ("2026-02-02", 3.0)]

    def test_ignora_nulos(self):
        pts = [{"d": "2026-01-05", "value": None}, {"d": "2026-01-06", "value": 9.0}]
        assert derived._period_closes(pts, "monthly") == [("2026-01-06", 9.0)]

    def test_orden_cronologico_garantizado(self):
        pts = [{"d": "2025-12-31", "value": 1.0}, {"d": "2026-01-01", "value": 2.0}]
        out = derived._period_closes(pts, "monthly")
        assert [d for d, _ in out] == ["2025-12-31", "2026-01-01"]


class TestAlineacion:
    def test_solo_conserva_fechas_presentes_en_ambas_series(self):
        a = [{"d": "2026-01-01", "value": 10.0}, {"d": "2026-01-02", "value": 20.0}]
        b = [{"d": "2026-01-02", "value": 2.0}]
        assert derived._align(a, b) == [("2026-01-02", 20.0, 2.0)]

    def test_descarta_denominadores_cero(self):
        a = [{"d": "2026-01-01", "value": 10.0}]
        b = [{"d": "2026-01-01", "value": 0.0}]
        assert derived._align(a, b) == []


class TestRecalculoCompleto:
    def test_marca_error_cuando_falta_el_insumo(self, db):
        res = derived.recompute_all()
        assert res["price_vs_cvdd"] == 0
        estado = store.get_metric_states()["price_vs_cvdd"]
        assert estado["status"] == "error"
        assert "cvdd" in estado["detail"]

    def test_calcula_ratio_cuando_hay_insumos(self, db):
        store.upsert_series("btc_price", [("2026-01-01", 60000.0), ("2026-01-02", 62000.0)])
        store.upsert_series("cvdd", [("2026-01-01", 12000.0), ("2026-01-02", 12400.0)])
        derived.recompute_all()
        assert store.get_latest("price_vs_cvdd")["value"] == pytest.approx(5.0)

    def test_convergencia_es_la_distancia_absoluta(self, db):
        store.upsert_series("sth_mvrv", [("2026-01-01", 0.84)])
        store.upsert_series("lth_mvrv", [("2026-01-01", 1.31)])
        derived.recompute_all()
        assert store.get_latest("sth_lth_convergence")["value"] == pytest.approx(0.47)

    def test_caida_desde_maximo_usa_maximo_acumulado(self, db):
        store.upsert_series(
            "btc_price",
            [("2026-01-01", 100.0), ("2026-01-02", 200.0), ("2026-01-03", 150.0)],
        )
        derived.recompute_all()
        serie = {p["d"]: p["value"] for p in store.get_series("drawdown_from_ath")}
        assert serie["2026-01-01"] == pytest.approx(0.0)
        assert serie["2026-01-02"] == pytest.approx(0.0)
        assert serie["2026-01-03"] == pytest.approx(-25.0)

    def test_el_maximo_no_retrocede(self, db):
        # Tras una caída, el máximo histórico sigue siendo el anterior.
        store.upsert_series(
            "btc_price",
            [("2026-01-01", 100.0), ("2026-01-02", 50.0), ("2026-01-03", 60.0)],
        )
        derived.recompute_all()
        serie = {p["d"]: p["value"] for p in store.get_series("drawdown_from_ath")}
        assert serie["2026-01-03"] == pytest.approx(-40.0)
