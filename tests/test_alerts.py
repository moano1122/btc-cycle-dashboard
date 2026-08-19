"""Tests del sistema de alertas.

Lo que se prueba aquí es sobre todo lo que el sistema NO debe hacer: no avisar
veinte veces del mismo cruce, no oscilar alrededor del umbral, y no disparar
con datos viejos. Una alerta de más es tan dañina como una de menos: si el canal
se llena de ruido, se ignora justo cuando importa.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from backend import alerts, store
from backend.catalog import BY_ID


def hoy(delta=0):
    return (datetime.now(timezone.utc).date() - timedelta(days=delta)).isoformat()


@pytest.fixture()
def sin_telegram(monkeypatch):
    """Evita cualquier salida a la red durante los tests."""
    enviados = []
    monkeypatch.setattr(alerts, "TELEGRAM_ENABLED", False)
    monkeypatch.setattr(alerts, "send_telegram", lambda t: enviados.append(t) or False)
    return enviados


class TestHisteresis:
    def test_arma_al_cruzar_hacia_abajo(self):
        assert alerts._crosses("x", 0.5, 1.0, "below", armed=False) is True

    def test_no_vuelve_a_armar_si_ya_estaba_armado(self):
        # Esta es la regla que evita un mensaje por cada chequeo.
        assert alerts._crosses("x", 0.5, 1.0, "below", armed=True) is None

    def test_no_desarma_dentro_del_margen(self):
        # 1.02 supera el umbral pero no el 3% de histéresis (1.03).
        assert alerts._crosses("x", 1.02, 1.0, "below", armed=True) is None

    def test_desarma_al_superar_el_margen(self):
        assert alerts._crosses("x", 1.04, 1.0, "below", armed=True) is False

    def test_arma_al_cruzar_hacia_arriba(self):
        assert alerts._crosses("x", 50.0, 45.0, "above", armed=False) is True

    def test_no_desarma_dentro_del_margen_hacia_arriba(self):
        # Umbral 45, margen 3% = 1.35. 44.0 sigue dentro de la zona muerta.
        assert alerts._crosses("x", 44.0, 45.0, "above", armed=True) is None

    def test_desarma_hacia_arriba_al_superar_el_margen(self):
        assert alerts._crosses("x", 43.0, 45.0, "above", armed=True) is False

    def test_el_valor_exacto_del_umbral_arma(self):
        assert alerts._crosses("x", 1.0, 1.0, "below", armed=False) is True

    def test_umbral_cero_usa_margen_absoluto(self):
        # Con umbral 0 el margen porcentual sería 0 y el sistema oscilaría en
        # cada decimal. Se usa un margen absoluto de 0.03.
        assert alerts._crosses("x", 0.01, 0.0, "below", armed=True) is None
        assert alerts._crosses("x", 0.05, 0.0, "below", armed=True) is False


class TestEvaluacion:
    def test_primer_cruce_genera_un_evento(self, serie, sin_telegram):
        ind = BY_ID["mvrv_zscore"]
        serie("mvrv_zscore", [(hoy(), ind.trigger - 0.1)])
        eventos = alerts.evaluate(send=False)
        ids = [e["title"] for e in eventos]
        assert any("MVRV Z-Score" in t for t in ids)

    def test_el_segundo_chequeo_no_repite_el_aviso(self, serie, sin_telegram):
        ind = BY_ID["mvrv_zscore"]
        serie("mvrv_zscore", [(hoy(), ind.trigger - 0.1)])
        alerts.evaluate(send=False)
        segundos = [e for e in alerts.evaluate(send=False) if e.get("id")]
        titulos = [e["title"] for e in segundos]
        assert not any("MVRV Z-Score" in t for t in titulos)

    def test_los_datos_rancios_no_disparan(self, serie, sin_telegram):
        ind = BY_ID["mvrv_zscore"]
        serie("mvrv_zscore", [(hoy(30), ind.trigger - 0.1)])
        eventos = alerts.evaluate(send=False)
        assert not any("MVRV" in e["title"] for e in eventos)

    def test_avisa_tambien_de_la_salida_de_la_zona(self, serie, sin_telegram):
        ind = BY_ID["mvrv_zscore"]
        serie("mvrv_zscore", [(hoy(), ind.trigger - 0.1)])
        alerts.evaluate(send=False)
        margen = abs(ind.trigger) * alerts.HYSTERESIS if ind.trigger else alerts.HYSTERESIS
        serie("mvrv_zscore", [(hoy(), ind.trigger + margen + 0.5)])
        eventos = alerts.evaluate(send=False)
        assert any("salió" in e["title"] for e in eventos)

    def test_el_primer_arranque_no_alerta_de_banda(self, serie, sin_telegram):
        # Al abrir la herramienta por primera vez no debe llegar un aviso de
        # cambio de banda: no hubo cambio, es el estado inicial.
        serie("mvrv_zscore", [(hoy(), 0.5)])
        eventos = alerts.evaluate(send=False)
        assert not any(e["title"].startswith("📊") for e in eventos)

    def test_avisa_al_cambiar_de_banda(self, serie, sin_telegram):
        serie("mvrv_zscore", [(hoy(), 2.5)])
        alerts.evaluate(send=False)          # fija la banda inicial
        serie("mvrv_zscore", [(hoy(), -0.35)])
        eventos = alerts.evaluate(send=False)
        assert any("score de suelo" in e["title"] for e in eventos)

    def test_los_eventos_quedan_registrados(self, serie, sin_telegram):
        ind = BY_ID["nupl"]
        serie("nupl", [(hoy(), ind.trigger - 0.1)])
        alerts.evaluate(send=False)
        assert len(store.recent_alerts()) >= 1

    def test_no_envia_a_telegram_si_no_esta_configurado(self, serie, sin_telegram):
        ind = BY_ID["nupl"]
        serie("nupl", [(hoy(), ind.trigger - 0.1)])
        alerts.evaluate(send=True)
        eventos = store.recent_alerts()
        assert eventos and eventos[0]["delivered"] == 0

    def test_el_mensaje_incluye_valor_umbral_y_contexto(self, serie, sin_telegram):
        ind = BY_ID["nupl"]
        serie("nupl", [(hoy(), ind.trigger - 0.1)])
        alerts.evaluate(send=False)
        msg = store.recent_alerts()[0]["message"]
        assert "umbral" in msg
        assert "Score agregado" in msg


class TestConfiguracionTelegram:
    def test_reporta_falta_de_credenciales(self, monkeypatch):
        monkeypatch.setattr(alerts, "TELEGRAM_ENABLED", False)
        res = alerts.test_telegram()
        assert res["ok"] is False
        assert ".env" in res["detail"]
