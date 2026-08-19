"""Tests del cliente de datos on-chain.

Dos zonas de riesgo:

1. **La extracción del valor.** Cada endpoint devuelve el número bajo una clave
   distinta ("mvrvZscore", "puellMultiple"...), así que se detecta por
   descarte. Si esa detección agarra el timestamp en vez del valor, el sistema
   guardaría 1786838400 como si fuera un MVRV y nadie lo notaría a simple vista.

2. **El control de cupo.** El plan gratuito son 15 peticiones al día. Excederlo
   devuelve 429 y bloquea la cuenta el resto del día.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from backend import store
from backend.sources import bitcoin_data as bd


class TestExtraccionDeValor:
    def test_encuentra_el_valor_ignorando_las_fechas(self):
        fila = {"d": "2026-08-16", "unixTs": 1786838400, "mvrvZscore": 0.3592}
        assert bd._pick_value(fila) == pytest.approx(0.3592)

    def test_no_confunde_el_timestamp_con_el_valor(self):
        # El fallo más peligroso posible de este módulo.
        fila = {"unixTs": 1786838400, "d": "2026-08-16", "puellMultiple": 0.834}
        assert bd._pick_value(fila) == pytest.approx(0.834)

    def test_acepta_valores_numericos_en_texto(self):
        assert bd._pick_value({"d": "2026-01-01", "x": "1.25"}) == pytest.approx(1.25)

    def test_devuelve_none_si_no_hay_numero(self):
        assert bd._pick_value({"d": "2026-01-01", "nota": "sin datos"}) is None

    def test_ignora_booleanos(self):
        assert bd._pick_value({"d": "2026-01-01", "activo": True}) is None

    def test_admite_valores_negativos(self):
        assert bd._pick_value({"d": "2026-01-01", "nupl": -0.284}) == pytest.approx(-0.284)

    @pytest.mark.parametrize("clave", ["d", "day", "theDay", "date"])
    def test_reconoce_las_variantes_de_fecha(self, clave):
        assert bd._pick_date({clave: "2026-08-16", "v": 1.0}) == "2026-08-16"

    def test_recorta_las_fechas_con_hora(self):
        assert bd._pick_date({"d": "2026-08-16T00:00:00Z", "v": 1.0}) == "2026-08-16"

    def test_convierte_desde_timestamp_unix(self):
        assert bd._pick_date({"unixTs": 1786838400, "v": 1.0}) is not None

    def test_devuelve_none_sin_fecha_reconocible(self):
        assert bd._pick_date({"v": 1.0}) is None


class TestHashRibbons:
    def test_calcula_el_ratio_entre_las_dos_medias(self):
        fila = {"d": "2026-01-01", "hashrateMa30": 900.0, "hashrateMa60": 1000.0}
        assert bd.EXTRACTORS["hash_ribbons"](fila) == pytest.approx(0.9)

    def test_devuelve_none_si_falta_una_media(self):
        assert bd.EXTRACTORS["hash_ribbons"]({"d": "2026-01-01", "ma30": 900.0}) is None

    def test_no_divide_por_cero(self):
        fila = {"d": "2026-01-01", "ma30": 900.0, "ma60": 0.0}
        assert bd.EXTRACTORS["hash_ribbons"](fila) is None


class TestPresupuesto:
    def test_arranca_con_el_cupo_intacto(self, db):
        b = bd.budget_status()
        assert b["used_hour"] == 0 and b["used_day"] == 0
        assert b["remaining_day"] == b["limit_day"]

    def test_contabiliza_cada_llamada(self, db):
        bd.store.record_call(bd.PROVIDER, "mvrv-zscore", True)
        bd.store.record_call(bd.PROVIDER, "nupl", False)
        b = bd.budget_status()
        assert b["used_hour"] == 2, "también las fallidas consumen cupo del proveedor"

    def test_bloquea_al_agotar_el_cupo_horario(self, db, monkeypatch):
        monkeypatch.setattr(bd, "REQ_PER_HOUR", 3)
        monkeypatch.setattr(bd, "REQ_PER_DAY", 100)
        for _ in range(3):
            bd.store.record_call(bd.PROVIDER, "x", True)
        assert bd._can_spend() is False

    def test_bloquea_al_agotar_el_cupo_diario(self, db, monkeypatch):
        monkeypatch.setattr(bd, "REQ_PER_HOUR", 100)
        monkeypatch.setattr(bd, "REQ_PER_DAY", 2)
        for _ in range(2):
            bd.store.record_call(bd.PROVIDER, "x", True)
        assert bd._can_spend() is False

    def test_lanza_excepcion_especifica_sin_cupo(self, db, monkeypatch):
        monkeypatch.setattr(bd, "REQ_PER_HOUR", 0)
        with pytest.raises(bd.BudgetExhausted):
            bd.fetch_metric("mvrv_zscore", "mvrv-zscore")

    def test_sin_cupo_no_toca_la_red(self, db, monkeypatch):
        monkeypatch.setattr(bd, "REQ_PER_HOUR", 0)

        def prohibido(*a, **k):
            raise AssertionError("no debe hacerse ninguna petición sin cupo")

        monkeypatch.setattr(bd.httpx, "Client", prohibido)
        with pytest.raises(bd.BudgetExhausted):
            bd.fetch_metric("mvrv_zscore", "mvrv-zscore")


class TestCabeceras:
    def test_sin_key_no_manda_autenticacion(self, monkeypatch):
        monkeypatch.setattr(bd, "BITCOIN_DATA_API_KEY", "")
        h = bd._headers()
        assert "x-api-key" not in h and "Authorization" not in h

    def test_con_key_manda_ambas_variantes(self, monkeypatch):
        monkeypatch.setattr(bd, "BITCOIN_DATA_API_KEY", "secreto")
        h = bd._headers()
        assert h["x-api-key"] == "secreto"
        assert h["Authorization"] == "Bearer secreto"


class TestAlmacen:
    def test_upsert_no_duplica_la_misma_fecha(self, db):
        store.upsert_series("m", [("2026-01-01", 1.0)])
        store.upsert_series("m", [("2026-01-01", 2.0)])
        serie = store.get_series("m")
        assert len(serie) == 1 and serie[0]["value"] == 2.0

    def test_el_ultimo_valor_ignora_los_nulos(self, db):
        store.upsert_series("m", [("2026-01-01", 5.0), ("2026-01-02", None)])
        assert store.get_latest("m")["d"] == "2026-01-01"

    def test_consulta_masiva_devuelve_el_ultimo_de_cada_serie(self, db):
        store.upsert_series("a", [("2026-01-01", 1.0), ("2026-01-05", 2.0)])
        store.upsert_series("b", [("2026-01-03", 9.0)])
        out = store.get_latest_many(["a", "b", "inexistente"])
        assert out["a"]["value"] == 2.0
        assert out["b"]["value"] == 9.0
        assert "inexistente" not in out

    def test_el_estado_conserva_el_ultimo_exito_tras_un_fallo(self, db):
        store.set_metric_state("m", status="ok", last_data_point="2026-01-01", ok=True)
        ok_previo = store.get_metric_states()["m"]["last_ok_utc"]
        store.set_metric_state("m", status="error", detail="429")
        estado = store.get_metric_states()["m"]
        assert estado["status"] == "error"
        assert estado["last_ok_utc"] == ok_previo, "no debe perderse el último éxito"
        assert estado["last_data_point"] == "2026-01-01"

    def test_los_ajustes_persisten_como_json(self, db):
        store.set_setting("k", {"a": [1, 2]})
        assert store.get_setting("k") == {"a": [1, 2]}

    def test_ajuste_inexistente_devuelve_el_valor_por_defecto(self, db):
        assert store.get_setting("no_existe", "def") == "def"

    def test_dias_desde_una_fecha(self, db):
        # En UTC, no en hora local: los proveedores publican en UTC y
        # `days_since` compara contra UTC. Mezclar ambas hacía que este test
        # fallara solo en las horas en que la fecha local y la UTC difieren.
        ayer = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
        assert store.days_since(ayer) == 1
        assert store.days_since(None) is None
        assert store.days_since("fecha-mala") is None

    def test_span_de_una_serie(self, db):
        store.upsert_series("m", [("2026-01-01", 1.0), ("2026-01-09", 2.0)])
        a, b, n = store.series_span("m")
        assert (a, b, n) == ("2026-01-01", "2026-01-09", 2)

    def test_span_de_serie_vacia(self, db):
        assert store.series_span("nada")[2] == 0
