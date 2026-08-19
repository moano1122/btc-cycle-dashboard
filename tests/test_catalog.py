"""Tests de integridad del catálogo.

El catálogo es la fuente única de verdad de umbrales y pesos. Un anclaje mal
formado no produce un error visible: produce una puntuación silenciosamente
equivocada. Estos tests existen para que eso no pase.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from backend import catalog
from backend.catalog import BY_ID, CATEGORY_LABELS, INDICATORS
from backend.scoring import interpolate

TUTORIALES = Path(__file__).resolve().parent.parent / "content" / "tutorials"


def ids():
    return [i.id for i in INDICATORS]


class TestEstructura:
    def test_los_ids_son_unicos(self):
        assert len(ids()) == len(set(ids()))

    def test_el_indice_por_id_esta_completo(self):
        assert set(BY_ID) == set(ids())

    def test_toda_categoria_tiene_etiqueta(self):
        for ind in INDICATORS:
            assert ind.category in CATEGORY_LABELS

    def test_los_onchain_declaran_endpoint(self):
        for ind in INDICATORS:
            if ind.source == "onchain":
                assert ind.endpoint, f"{ind.id} es onchain y no tiene endpoint"

    def test_los_derivados_no_declaran_endpoint(self):
        for ind in INDICATORS:
            if ind.source == "derived":
                assert ind.endpoint is None, f"{ind.id} es derivado y declara endpoint"

    def test_todo_indicador_tiene_resumen(self):
        for ind in INDICATORS:
            assert len(ind.summary) > 40, f"{ind.id} tiene un resumen demasiado escueto"

    def test_pesos_en_rango_razonable(self):
        for ind in INDICATORS:
            assert 1 <= ind.weight <= 12, f"{ind.id} tiene peso {ind.weight}"

    def test_tiers_de_refresco_validos(self):
        for ind in INDICATORS:
            assert ind.refresh_tier in (1, 2, 3)

    def test_direccion_de_umbral_valida(self):
        for ind in INDICATORS:
            assert ind.trigger_dir in ("below", "above")


class TestAnclajes:
    def test_sin_valores_duplicados(self):
        # La interpolación exige valores únicos: un duplicado la vuelve ambigua.
        for ind in INDICATORS:
            vals = [v for v, _ in ind.anchors]
            assert len(vals) == len(set(vals)), f"{ind.id} tiene anclajes duplicados"

    def test_al_menos_cuatro_anclajes(self):
        for ind in INDICATORS:
            assert len(ind.anchors) >= 4, f"{ind.id} tiene muy pocos anclajes"

    def test_puntuaciones_dentro_de_cero_cien(self):
        for ind in INDICATORS:
            for v, s in ind.anchors:
                assert 0 <= s <= 100, f"{ind.id} tiene puntuación {s}"

    def test_puntuaciones_monotonas_respecto_al_valor(self):
        for ind in INDICATORS:
            scores = [s for _, s in sorted(ind.anchors, key=lambda t: t[0])]
            creciente = scores == sorted(scores)
            decreciente = scores == sorted(scores, reverse=True)
            assert creciente or decreciente, f"{ind.id} tiene puntuaciones no monótonas"

    def test_la_interpolacion_reproduce_cada_anclaje(self):
        for ind in INDICATORS:
            for v, s in ind.anchors:
                assert interpolate(ind.anchors, v) == pytest.approx(s, abs=0.01), ind.id

    def test_cubren_el_rango_completo_de_puntuacion(self):
        for ind in INDICATORS:
            scores = [s for _, s in ind.anchors]
            assert max(scores) >= 90, f"{ind.id} nunca alcanza 90: no puede señalar suelo"
            assert min(scores) <= 10, f"{ind.id} nunca baja de 10: no puede señalar techo"

    def test_la_direccion_del_umbral_concuerda_con_los_anclajes(self):
        # Si un valor bajo debe indicar suelo, el anclaje del valor mínimo tiene
        # que ser el de puntuación más alta. Un signo invertido aquí produce el
        # score exactamente contrario al correcto.
        for ind in INDICATORS:
            orden = sorted(ind.anchors, key=lambda t: t[0])
            primero, ultimo = orden[0][1], orden[-1][1]
            if ind.trigger_dir == "below":
                assert primero > ultimo, f"{ind.id}: dir 'below' pero valor bajo puntúa menos"
            else:
                assert primero < ultimo, f"{ind.id}: dir 'above' pero valor alto puntúa menos"

    def test_el_umbral_de_disparo_puntua_alto(self):
        # Cruzar el umbral debe significar algo: si el trigger puntúa 40, la
        # alerta se dispararía en territorio neutro.
        for ind in INDICATORS:
            s = interpolate(ind.anchors, ind.trigger)
            assert s >= 60, f"{ind.id}: su umbral {ind.trigger} solo puntúa {s:.0f}"

    def test_el_umbral_cae_dentro_del_rango_de_anclajes(self):
        for ind in INDICATORS:
            vals = [v for v, _ in ind.anchors]
            assert min(vals) <= ind.trigger <= max(vals), (
                f"{ind.id}: umbral {ind.trigger} fuera del rango de anclajes "
                f"[{min(vals)}, {max(vals)}] — no podría dispararse nunca"
            )


class TestCalibracion:
    def test_procedencia_declarada_y_valida(self):
        for ind in INDICATORS:
            assert ind.calibration in ("datos", "literatura")

    def test_los_calibrados_con_datos_registran_el_suelo_real(self):
        for ind in INDICATORS:
            if ind.calibration == "datos":
                claves = [k for k in ind.historic if k.startswith("suelo ")]
                assert claves, f"{ind.id} dice calibrarse con datos y no guarda el suelo real"

    def test_el_suelo_de_referencia_puntua_alto(self):
        # La referencia de cada indicador es su lectura más extrema dentro de la
        # ventana del bear market de 2022, no una fecha fija: los indicadores no
        # tocan su extremo el mismo día. Hash Ribbons capituló en julio de 2022,
        # cuatro meses antes del mínimo del precio, y el 21 de noviembre estaba
        # exactamente en su mediana.
        #
        # El umbral es 70 y no 100 porque en algunos indicadores la lectura ACTUAL
        # supera a la de 2022. Eso no es un fallo de calibración: es la señal.
        for ind in INDICATORS:
            for k, v in ind.historic.items():
                if k.startswith("suelo "):
                    s = interpolate(ind.anchors, v)
                    assert s >= 70, f"{ind.id}: su suelo de referencia {v} solo puntúa {s:.0f}"

    def test_los_suelos_referencian_ciclos_reales(self):
        # Solo se calibra contra suelos de ciclo por agotamiento. Marzo de 2020
        # queda fuera a propósito: fue un shock de liquidez de dos semanas y
        # muchos indicadores no llegaron a extremos, así que incluirlo aflojaría
        # la escala.
        validos = {"2015", "2018", "2022"}
        for ind in INDICATORS:
            for k in ind.historic:
                if k.startswith("suelo "):
                    assert k.split()[1] in validos, f"{ind.id}: ciclo {k} no reconocido"

    def test_los_calibrados_con_varios_ciclos_son_los_de_mas_peso(self):
        multi = {i.id for i in INDICATORS if len([k for k in i.historic if k.startswith("suelo ")]) >= 3}
        top = sorted(INDICATORS, key=lambda i: -i.weight)[:6]
        assert len(multi) >= 8, f"solo {len(multi)} indicadores tienen 3 ciclos"
        assert any(i.id in multi for i in top), "ninguno de los de más peso tiene varios ciclos"

    def test_el_extremo_de_cada_serie_puntua_cien(self):
        # El anclaje más extremo en dirección de suelo debe valer exactamente
        # 100: es lo que ancla el resto de la escala.
        for ind in INDICATORS:
            orden = sorted(ind.anchors, key=lambda t: t[0])
            extremo = orden[0] if ind.trigger_dir == "below" else orden[-1]
            assert extremo[1] == 100, f"{ind.id}: su extremo puntúa {extremo[1]}, no 100"

    def test_hay_calibracion_con_datos_en_los_indicadores_de_mas_peso(self):
        top = sorted(INDICATORS, key=lambda i: -i.weight)[:5]
        con_datos = [i.id for i in top if i.calibration == "datos"]
        assert len(con_datos) >= 4, f"solo {con_datos} de los 5 de más peso están verificados"


class TestTutoriales:
    def test_todo_indicador_tiene_tutorial(self):
        for ind in INDICATORS:
            assert (TUTORIALES / f"{ind.id}.md").exists(), f"falta tutorial de {ind.id}"

    def test_no_hay_tutoriales_huerfanos(self):
        archivos = {p.stem for p in TUTORIALES.glob("*.md")}
        assert archivos - set(ids()) == set()

    def test_los_tutoriales_documentan_donde_falla(self):
        # Es la sección que evita que la herramienta se use con exceso de
        # confianza. No es opcional.
        for ind in INDICATORS:
            texto = (TUTORIALES / f"{ind.id}.md").read_text(encoding="utf-8")
            assert "ha fallado" in texto or "falla" in texto, f"{ind.id} no documenta fallos"

    def test_los_tutoriales_tienen_cuerpo_suficiente(self):
        for ind in INDICATORS:
            texto = (TUTORIALES / f"{ind.id}.md").read_text(encoding="utf-8")
            assert len(texto.split()) >= 250, f"{ind.id} es demasiado breve"


class TestSerializacion:
    def test_to_dict_expone_lo_que_el_frontend_necesita(self):
        d = catalog.to_dict(INDICATORS[0])
        for clave in (
            "id", "label", "category", "category_label", "default_weight",
            "source", "trigger", "trigger_dir", "unit", "decimals", "anchors",
        ):
            assert clave in d

    def test_pesos_por_defecto_cubren_todo_el_catalogo(self):
        assert set(catalog.default_weights()) == set(ids())

    def test_particion_onchain_derivados_es_completa(self):
        n = len(catalog.onchain_indicators()) + len(catalog.derived_indicators())
        assert n == len(INDICATORS)
