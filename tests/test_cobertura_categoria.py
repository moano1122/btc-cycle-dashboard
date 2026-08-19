"""Tests de la cobertura por categoría.

El score global puede ocultar que categorías enteras no tienen ningún dato. Si
Flujos y Sentimiento están al 0%, el número que se muestra no es un score del
catálogo sino de las categorías que sobrevivieron, y eso tiene que ser visible.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from backend import scoring
from backend.catalog import INDICATORS


def hoy():
    return datetime.now(timezone.utc).date().isoformat()


def cat(snap, key):
    return next(c for c in snap["categories"] if c["key"] == key)


class TestCoberturaPorCategoria:
    def test_todas_las_categorias_aparecen_aunque_esten_vacias(self, db):
        snap = scoring.snapshot()
        assert {c["key"] for c in snap["categories"]} == {i.category for i in INDICATORS}

    def test_categoria_sin_datos_reporta_cero_y_score_nulo(self, db):
        c = cat(scoring.snapshot(), "flujos")
        assert c["coverage_pct"] == 0.0
        assert c["score"] is None, "sin datos no debe inventarse un score de categoría"

    def test_categoria_completa_reporta_cien(self, serie):
        # Técnico tiene 5 indicadores; con todos presentes debe dar 100%.
        for ind in INDICATORS:
            if ind.category == "tecnico":
                serie(ind.id, [(hoy(), ind.anchors[0][0])])
        assert cat(scoring.snapshot(), "tecnico")["coverage_pct"] == 100.0

    def test_cobertura_parcial_se_calcula_sobre_el_peso(self, serie):
        # Un solo indicador de Valoración presente: la cobertura debe ser su peso
        # sobre el peso total de la categoría, no 1 entre el número de miembros.
        valoracion = [i for i in INDICATORS if i.category == "valoracion"]
        elegido = valoracion[0]
        serie(elegido.id, [(hoy(), elegido.anchors[0][0])])
        c = cat(scoring.snapshot(), "valoracion")
        esperado = round(100.0 * elegido.weight / sum(i.weight for i in valoracion), 0)
        assert c["coverage_pct"] == esperado
        assert c["count"] == 1
        assert c["count_total"] == len(valoracion)

    def test_los_datos_rancios_no_cuentan_como_cobertura(self, serie):
        viejo = (datetime.now(timezone.utc).date() - timedelta(days=40)).isoformat()
        for ind in INDICATORS:
            if ind.category == "tecnico":
                serie(ind.id, [(viejo, ind.anchors[0][0])])
        assert cat(scoring.snapshot(), "tecnico")["coverage_pct"] == 0.0

    def test_la_cobertura_global_es_la_suma_de_las_parciales(self, serie):
        for ind in list(INDICATORS)[:6]:
            serie(ind.id, [(hoy(), ind.anchors[0][0])])
        snap = scoring.snapshot()
        w = sum(c["weight"] for c in snap["categories"])
        wt = sum(c["weight_total"] for c in snap["categories"])
        assert round(100.0 * w / wt, 1) == snap["coverage_pct"]

    def test_las_categorias_se_ordenan_por_peso_total(self, db):
        # Por peso TOTAL y no por el disponible: si no, el orden bailaría cada
        # vez que llega o falta un dato.
        pesos = [c["weight_total"] for c in scoring.snapshot()["categories"]]
        assert pesos == sorted(pesos, reverse=True)
