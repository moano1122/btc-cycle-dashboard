"""Tests de los flujos de ETF.

El parseo es de una tabla HTML, así que es frágil por naturaleza: si Farside
cambia el formato, lo que importa es que falle de forma visible y no que devuelva
números plausibles pero equivocados. Los negativos vienen entre paréntesis
—convención contable— y confundir el signo invertiría por completo la lectura del
indicador.
"""

from __future__ import annotations

import pytest

from backend import store
from backend.sources import etf


class TestParseoDeNumeros:
    def test_positivo_simple(self):
        assert etf._numero("227.0") == pytest.approx(227.0)

    def test_los_parentesis_significan_negativo(self):
        # El error más caro posible de este módulo: leer una salida de 484
        # millones como una entrada.
        assert etf._numero("(484.1)") == pytest.approx(-484.1)

    def test_separador_de_miles(self):
        assert etf._numero("61,256") == pytest.approx(61256.0)

    def test_negativo_con_miles(self):
        assert etf._numero("(27,549)") == pytest.approx(-27549.0)

    def test_guion_significa_sin_dato(self):
        assert etf._numero("-") is None

    def test_celda_vacia(self):
        assert etf._numero("   ") is None

    def test_texto_no_numerico(self):
        assert etf._numero("Total") is None

    def test_cero(self):
        assert etf._numero("0.0") == 0.0

    def test_simbolo_de_dolar(self):
        assert etf._numero("$123.4") == pytest.approx(123.4)


class TestExtraccionDeCeldas:
    def test_extrae_texto_de_una_fila(self):
        fila = "<td>11 Jan 2024</td><td>111.7</td><td>(95.1)</td>"
        assert etf._celdas(fila) == ["11 Jan 2024", "111.7", "(95.1)"]

    def test_limpia_etiquetas_anidadas(self):
        fila = "<td><span class='x'>227.0</span></td>"
        assert etf._celdas(fila) == ["227.0"]

    def test_acepta_encabezados(self):
        assert etf._celdas("<th>Date</th><th>Total</th>") == ["Date", "Total"]


class TestDerivadas:
    def test_posicion_acumulada_usa_el_precio_de_cada_dia(self, db):
        # 100 M a 50.000 = 2.000 BTC; 50 M a 25.000 = otros 2.000 BTC.
        store.upsert_series("btc_price", [("2024-01-11", 50000.0), ("2024-01-12", 25000.0)])
        store.upsert_series(etf.FLOW_USD, [("2024-01-11", 100.0), ("2024-01-12", 50.0)])
        etf.derive_net_position()
        serie = {p["d"]: p["value"] for p in store.get_series(etf.NET_POSITION_BTC)}
        assert serie["2024-01-11"] == pytest.approx(2000.0)
        assert serie["2024-01-12"] == pytest.approx(4000.0)

    def test_las_salidas_reducen_la_posicion(self, db):
        store.upsert_series("btc_price", [("2024-01-11", 50000.0), ("2024-01-12", 50000.0)])
        store.upsert_series(etf.FLOW_USD, [("2024-01-11", 100.0), ("2024-01-12", -50.0)])
        etf.derive_net_position()
        assert store.get_latest(etf.NET_POSITION_BTC)["value"] == pytest.approx(1000.0)

    def test_suma_movil_de_treinta_dias(self, db):
        pts = [(f"2024-02-{i:02d}", 10.0) for i in range(1, 29)]
        store.upsert_series(etf.FLOW_USD, pts)
        etf.derive_flow_30d()
        assert store.get_latest("etf_flow_30d")["value"] == pytest.approx(280.0)

    def test_la_caida_descarta_el_periodo_de_arranque(self, db):
        # Con la posición aún en unos miles de BTC, una salida normal producía
        # caídas del 45% que no significaban nada y llegaron a fijar el anclaje
        # de puntuación máxima. No deben aparecer en la serie.
        store.upsert_series("btc_price", [(f"2024-01-{i:02d}", 50000.0) for i in range(11, 32)])
        flujos = [("2024-01-11", 500.0), ("2024-01-12", -300.0)]      # base diminuta
        flujos += [(f"2024-01-{i:02d}", 900.0) for i in range(13, 25)]  # base ya grande
        flujos += [("2024-01-25", -2000.0)]
        store.upsert_series(etf.FLOW_USD, flujos)
        etf.derive_net_position()
        etf.derive_position_drawdown()
        serie = store.get_series("etf_position_drawdown")
        assert serie, "debería haber datos una vez superada la base mínima"
        assert all(p["d"] >= "2024-01-13" for p in serie), "el arranque no debe colarse"

    def test_la_caida_es_cero_en_maximos(self, db):
        store.upsert_series("btc_price", [(f"2024-01-{i:02d}", 50000.0) for i in range(11, 25)])
        store.upsert_series(etf.FLOW_USD, [(f"2024-01-{i:02d}", 900.0) for i in range(11, 25)])
        etf.derive_net_position()
        etf.derive_position_drawdown()
        assert store.get_latest("etf_position_drawdown")["value"] == pytest.approx(0.0)

    def test_reemplaza_la_serie_en_vez_de_fusionarla(self, db):
        # Si cambia la definición del derivado, los puntos viejos no deben
        # sobrevivir contaminando la calibración.
        store.upsert_series("etf_flow_30d", [("2020-01-01", 999.0)])
        store.upsert_series(etf.FLOW_USD, [("2024-02-01", 10.0)])
        etf.derive_flow_30d()
        fechas = [p["d"] for p in store.get_series("etf_flow_30d")]
        assert "2020-01-01" not in fechas


class TestAlmacenReemplazo:
    def test_replace_borra_lo_anterior(self, db):
        store.upsert_series("m", [("2026-01-01", 1.0), ("2026-01-02", 2.0)])
        store.replace_series("m", [("2026-01-03", 3.0)])
        serie = store.get_series("m")
        assert len(serie) == 1 and serie[0]["d"] == "2026-01-03"

    def test_replace_con_lista_vacia_deja_la_serie_vacia(self, db):
        store.upsert_series("m", [("2026-01-01", 1.0)])
        store.replace_series("m", [])
        assert store.get_series("m") == []
