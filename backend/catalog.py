"""Catálogo de indicadores.

Este es el corazón intelectual del sistema. Cada entrada define QUÉ se mide,
DE DÓNDE sale, CÓMO se traduce a una puntuación de suelo 0-100, y CUÁL fue su
lectura en los suelos de ciclo anteriores.

Sobre `anchors`
---------------
Cada indicador tiene una escala propia y no comparable con las demás: un MVRV
Z-Score de 0 y un Puell de 0.5 son ambos "zona de suelo" pero viven en unidades
distintas. `anchors` es una lista de pares (valor_del_indicador, puntuación_de_suelo)
que traduce cualquiera de esas escalas a un 0-100 común, interpolando
linealmente entre puntos. 100 = señal máxima de suelo. 0 = lo contrario.

Sobre `calibration` — LEER ANTES DE TOCAR UN UMBRAL
--------------------------------------------------
Los anclajes se fijaron primero con los valores publicados en la literatura, y
al confrontarlos con las series reales del proveedor resultaron **incorrectos en
cinco indicadores**, en algunos casos por un factor de casi 3. Este proveedor
escala varias series de forma distinta a las fuentes habituales:

    indicador            suelo nov-2022 según   suelo nov-2022
                         la literatura          real en estos datos
    price_vs_cvdd        1.20                   3.36
    price_vs_balanced    1.02                   1.40
    reserve_risk         0.0016                 0.000409
    price_vs_200wma      1.02                   0.658
    nupl                 -0.15                  -0.284

El caso de `price_vs_200wma` es el más instructivo: la creencia de que el precio
"nunca perfora la media de 200 semanas" es simplemente falsa. En 2022 cotizó un
34% por debajo durante 210 días seguidos.

Por eso cada indicador declara `calibration`:

  - "datos"      → los anclajes salen de la distribución observada del propio
                   proveedor, con el percentil 8 como umbral de disparo y el
                   suelo del 21-nov-2022 como referencia de puntuación ~78-90.
                   Regenerables con `python scripts/calibrate.py`.
  - "literatura" → todavía sin datos suficientes para verificar. Los umbrales
                   vienen de fuentes publicadas y **pueden estar en otra escala**.
                   La interfaz los marca como no verificados.

LIMITACIÓN QUE NO SE PUEDE MAQUILLAR: el plan gratuito da 4 años de historia, así
que la ventana de calibración contiene UN suelo de ciclo (noviembre de 2022). Una
observación no es una regularidad estadística. Con un plan de pago que dé historia
completa, volver a correr el calibrador mejoraría esto sustancialmente.

Sobre `weight`
--------------
Peso por defecto en el score agregado, de 1 a 12. Refleja qué tan limpio ha
sido el historial del indicador marcando suelos, no qué tan famoso es. Usted
puede ajustarlos desde la interfaz; estos son solo el punto de partida.

ADVERTENCIA IMPORTANTE
----------------------
Los umbrales verificados descansan sobre UN suelo de ciclo (nov-2022), que es
lo que permite la historia disponible. Los no verificados vienen de literatura
sobre 4 suelos, en escalas que pueden no coincidir con este proveedor. Además, el techo de octubre de 2025 pasó sin que
ningún indicador on-chain mayor diera señal limpia de venta, lo que sugiere
que la entrada de los ETFs spot y los tesoros corporativos alteró la mecánica
del mercado. Trate cada número como una probabilidad, no como una certeza.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Category = Literal["valoracion", "holders", "mineros", "comportamiento", "tecnico", "flujos", "sentimiento"]

CATEGORY_LABELS: dict[str, str] = {
    "valoracion": "Valoración",
    "holders": "Holders",
    "mineros": "Mineros",
    "comportamiento": "Comportamiento",
    "tecnico": "Técnico",
    "flujos": "Flujos",
    "sentimiento": "Sentimiento",
}


@dataclass(frozen=True)
class Indicator:
    id: str
    label: str
    category: Category
    weight: int
    # "onchain" -> se pide a bitcoin-data.com; "derived" -> se calcula local
    source: Literal["onchain", "derived"]
    endpoint: str | None
    # Pares (valor, puntuación 0-100). Ver docstring del módulo.
    anchors: list[tuple[float, float]]
    # Umbral de disparo de alerta y dirección.
    trigger: float
    trigger_dir: Literal["below", "above"]
    unit: str = ""
    decimals: int = 2
    # Suavizado en días. Algunos indicadores (SOPR) son ruidosos a diario y su
    # señal solo es legible como media móvil.
    smooth_days: int = 0
    # Lectura del indicador en suelos de ciclo anteriores, para anotar gráficas.
    historic: dict[str, float] = field(default_factory=dict)
    summary: str = ""
    # Prioridad de refresco: 1 = todos los días, 2 = día por medio, 3 = semanal.
    # Existe porque el cupo gratuito de la API no alcanza para refrescar los 20+
    # indicadores on-chain a diario.
    refresh_tier: int = 1
    invert_chart: bool = False
    # De dónde salen los anclajes: "datos" = derivados de la distribución
    # real del proveedor; "literatura" = tomados de fuentes publicadas y
    # todavía sin verificar contra la serie. Se muestra en la interfaz.
    calibration: str = "literatura"


INDICATORS: list[Indicator] = [
    # =======================================================================
    # VALORACIÓN — ¿está BTC barato contra el costo real que pagó el mercado?
    # =======================================================================
    Indicator(
        id="mvrv_zscore",
        label="MVRV Z-Score",
        category="valoracion",
        weight=12,
        source="onchain",
        endpoint="mvrv-zscore",
        anchors=[(-0.687038, 100), (-0.340676, 94), (-0.217509, 86), (-0.011615, 76), (0.450228, 64), (1.2132, 48), (2.22045, 28), (3.64555, 12), (11.7543, 0)],
        trigger=-0.491538,
        trigger_dir="below",
        decimals=3,
        historic={"suelo 2015": -0.598411, "suelo 2018": -0.491538, "suelo 2022": -0.3599},
        summary="Cuánto se aleja el precio de mercado del costo base agregado, medido en desviaciones estándar. El indicador con mejor historial marcando suelos.",
        refresh_tier=1,
        calibration="datos",
    ),
    Indicator(
        id="mvrv",
        label="MVRV Ratio",
        category="valoracion",
        weight=5,
        source="onchain",
        endpoint="mvrv",
        anchors=[(0.386829, 100), (0.76045, 94), (0.84392, 86), (0.994574, 76), (1.28453, 64), (1.72149, 48), (2.23533, 28), (3.00052, 12), (146.038, 0)],
        trigger=0.690481,
        trigger_dir="below",
        historic={"suelo 2015": 0.56358, "suelo 2018": 0.690481, "suelo 2022": 0.7559},
        summary="Capitalización de mercado dividida por capitalización realizada. Por debajo de 1 el tenedor promedio está en pérdida.",
        refresh_tier=2,
        calibration="datos",

    ),
    Indicator(
        id="nupl",
        label="NUPL",
        category="valoracion",
        weight=10,
        source="onchain",
        endpoint="nupl",
        anchors=[(-0.3168, 100), (-0.18944, 94), (-0.09786, 86), (0.13706, 76), (0.2287, 64), (0.4254, 48), (0.5354, 28), (0.5718, 12), (0.6402, 0)],
        trigger=-0.3168,
        trigger_dir="below",
        decimals=3,
        historic={"suelo 2022": -0.3168},
        summary="Ganancia o pérdida no realizada de toda la red como fracción de la capitalización. Negativo significa capitulación: la red entera está bajo el agua.",
        refresh_tier=1,
        calibration="datos",
    ),
    Indicator(
        id="price_vs_cvdd",
        label="Precio / CVDD",
        category="valoracion",
        weight=6,
        source="derived",
        endpoint=None,
        anchors=[(3.35817, 100), (3.55956, 94), (4.16933, 86), (4.66424, 76), (5.28604, 64), (7.3311, 48), (9.85319, 28), (10.976, 12), (12.9572, 0)],
        trigger=3.35817,
        trigger_dir="below",
        historic={"suelo 2022": 3.35817},
        summary="CVDD (Cumulative Value Days Destroyed) ha actuado como piso duro del precio en todos los ciclos. Cuando el ratio toca 1 el precio está tocando ese piso.",
        refresh_tier=2,
        calibration="datos",
    ),
    Indicator(
        id="price_vs_balanced",
        label="Precio / Balanced Price",
        category="valoracion",
        weight=5,
        source="derived",
        endpoint=None,
        anchors=[(1.37318, 100), (1.50476, 94), (1.64266, 86), (2.08425, 76), (2.33346, 64), (3.13361, 48), (3.93122, 28), (4.29193, 12), (4.9929, 0)],
        trigger=1.37318,
        trigger_dir="below",
        historic={"suelo 2022": 1.37318},
        summary="El Balanced Price resta al costo base lo que el mercado ya transfirió. El precio lo ha tocado casi exactamente en cada suelo de ciclo.",
        refresh_tier=2,
        calibration="datos",
    ),
    Indicator(
        id="aviv_zscore",
        label="AVIV Z-Score",
        category="valoracion",
        weight=6,
        source="onchain",
        endpoint="aviv-zscore",
        anchors=[(0.506527, 100), (0.570098, 94), (0.609478, 86), (0.78745, 76), (0.879196, 64), (1.16746, 48), (1.43877, 28), (1.5562, 12), (1.853, 0)],
        trigger=0.506527,
        trigger_dir="below",
        decimals=3,
        historic={"suelo 2022": 0.506527},
        summary="Versión mejorada del MVRV que usa la media real del mercado en vez del precio realizado. Corrige el sesgo de las monedas perdidas.",
        refresh_tier=2,
        calibration="datos",

    ),

    # =======================================================================
    # HOLDERS — ¿qué está haciendo cada cohorte de tenedores?
    # =======================================================================
    Indicator(
        id="sth_mvrv",
        label="STH-MVRV (manos cortas)",
        category="holders",
        weight=8,
        source="onchain",
        endpoint="sth-mvrv",
        anchors=[(0.7, 100), (0.7856, 94), (0.83, 86), (0.88, 76), (0.921, 64), (1.02, 48), (1.121, 28), (1.219, 12), (1.389, 0)],
        trigger=0.777,
        trigger_dir="below",
        decimals=3,
        historic={"suelo 2022": 0.777},
        summary="Precio dividido por el costo base de quien compró en los últimos 155 días (~5 meses). Es exactamente el indicador que usted mencionó: el precio de los holders recientes.",
        refresh_tier=1,
        calibration="datos",
    ),
    Indicator(
        id="lth_mvrv",
        label="LTH-MVRV (manos largas)",
        category="holders",
        weight=8,
        source="onchain",
        endpoint="lth-mvrv",
        anchors=[(0.774, 100), (0.824, 94), (0.9216, 86), (1.169, 76), (1.438, 64), (2.291, 48), (3.168, 28), (3.597, 12), (4.408, 0)],
        trigger=0.774,
        trigger_dir="below",
        decimals=3,
        historic={"suelo 2022": 0.774},
        summary="Lo mismo para quien lleva más de 155 días. Cuando hasta las manos fuertes están en pérdida, el mercado ha llegado a un extremo.",
        refresh_tier=1,
        calibration="datos",
    ),
    Indicator(
        id="sth_lth_convergence",
        label="Convergencia STH ↔ LTH",
        category="holders",
        weight=6,
        source="derived",
        endpoint=None,
        anchors=[(0.001, 100), (0.009, 94), (0.0576, 86), (0.1188, 76), (0.42, 64), (1.201, 48), (2.118, 28), (2.464, 12), (3.146, 0)],
        trigger=0.001,
        trigger_dir="below",
        decimals=3,
        historic={"suelo 2022": 0.001},
        summary="Distancia absoluta entre el MVRV de manos cortas y el de manos largas. Convergieron en los suelos de 2015, 2019 y 2022. Hoy siguen separados.",
        refresh_tier=1,
        calibration="datos",
    ),
    Indicator(
        id="reserve_risk",
        label="Reserve Risk",
        category="holders",
        weight=8,
        source="onchain",
        endpoint="reserve-risk",
        anchors=[(0.000409373, 100), (0.000431064, 94), (0.000499555, 86), (0.000533539, 76), (0.000596609, 64), (0.000828849, 48), (0.00111673, 28), (0.00124652, 12), (0.002384, 0)],
        trigger=0.000409373,
        trigger_dir="below",
        decimals=5,
        historic={"suelo 2022": 0.000409373},
        summary="Relación entre el precio y la convicción acumulada de los tenedores de largo plazo. Bajo = el riesgo/recompensa favorece acumular.",
        refresh_tier=1,
        calibration="datos",
    ),
    Indicator(
        id="pct_lth_in_loss",
        label="% de LTH en pérdida",
        category="holders",
        weight=5,
        source="onchain",
        endpoint="percent-lth-in-loss",
        anchors=[(0, 0), (0.0528, 28), (14.5293, 48), (26.3859, 64), (30.2037, 76), (37.4912, 86), (46.6598, 94), (50.1665, 100)],
        trigger=31.9927,
        trigger_dir="above",
        unit="%",
        decimals=1,
        historic={"suelo 2022": 31.9927},
        summary="Porcentaje de la oferta en manos largas que está bajo el agua. Los suelos históricos llegaron con más de un cuarto de las manos fuertes en pérdida.",
        refresh_tier=2,
        calibration="datos",

    ),
    Indicator(
        id="rhodl_ratio",
        label="RHODL Ratio",
        category="holders",
        weight=5,
        source="onchain",
        endpoint="rhodl-ratio",
        anchors=[(50000, 0), (20000, 10), (10000, 22), (5000, 38), (2500, 55), (1200, 75), (600, 92), (350, 100)],
        trigger=1000.0,
        trigger_dir="below",
        decimals=0,
        historic={"2015-01": 350, "2018-12": 500, "2020-03": 900, "2022-11": 700},
        summary="Compara el valor de las monedas movidas hace una semana contra las de hace 1-2 años. Bajo = la oferta está firmemente en manos de largo plazo.",
        refresh_tier=3,
    ),

    # =======================================================================
    # MINEROS — el productor marginal capitula antes que el suelo
    # =======================================================================
    Indicator(
        id="puell_multiple",
        label="Puell Multiple",
        category="mineros",
        weight=9,
        source="onchain",
        endpoint="puell-multiple",
        anchors=[(0.29354, 100), (0.435026, 94), (0.515273, 86), (0.601056, 76), (0.748145, 64), (1.09269, 48), (1.52663, 28), (2.35975, 12), (10.4902, 0)],
        trigger=0.312325,
        trigger_dir="below",
        decimals=3,
        historic={"suelo 2015": 0.312325, "suelo 2018": 0.302611, "suelo 2022": 0.346525},
        summary="Ingreso diario de los mineros contra su promedio anual. Por debajo de 0.5 minar deja de ser rentable y los mineros capitulan, lo que históricamente coincide con el suelo.",
        refresh_tier=1,
        calibration="datos",
    ),
    Indicator(
        id="hash_ribbons",
        label="Hash Ribbons",
        category="mineros",
        weight=5,
        source="onchain",
        endpoint="hashribbons",
        anchors=[(0.807143, 100), (0.931595, 94), (0.975147, 86), (0.993187, 76), (1.01233, 64), (1.03773, 48), (1.08827, 28), (1.23457, 12), (1.85863, 0)],
        trigger=0.96149,
        trigger_dir="below",
        decimals=4,
        historic={"suelo 2015": 0.994739, "suelo 2018": 0.873216, "suelo 2022": 0.96149},
        summary="Media móvil de 30 días del hashrate contra la de 60. Cuando la corta cae bajo la larga, los mineros están apagando máquinas: capitulación.",
        refresh_tier=2,
        calibration="datos",

    ),
    Indicator(
        id="miner_position_index",
        label="Miner Position Index",
        category="mineros",
        weight=3,
        source="onchain",
        endpoint="miner-position-index",
        anchors=[(4.0, 0), (2.0, 15), (1.0, 30), (0.0, 48), (-1.0, 68), (-2.0, 88), (-3.0, 100)],
        trigger=-1.0,
        trigger_dir="below",
        decimals=2,
        historic={"2018-12": -2.1, "2020-03": -1.8, "2022-11": -1.5},
        summary="Cuánto BTC están enviando los mineros a exchanges contra su media anual. Muy negativo = los mineros dejaron de vender, ya no queda presión de oferta.",
        refresh_tier=3,
    ),

    # =======================================================================
    # COMPORTAMIENTO — ¿la gente está vendiendo en pérdida?
    # =======================================================================
    Indicator(
        id="asopr",
        label="aSOPR (30d)",
        category="comportamiento",
        weight=7,
        source="onchain",
        endpoint="asopr",
        smooth_days=30,
        anchors=[(1.06, 0), (1.03, 12), (1.01, 28), (1.0, 42), (0.99, 58), (0.975, 75), (0.96, 90), (0.94, 100)],
        trigger=0.975,   # perdidas realizadas de forma sostenida
        trigger_dir="below",
        decimals=4,
        historic={"2015-01": 0.94, "2018-12": 0.95, "2020-03": 0.95, "2022-11": 0.96},
        summary="Ratio de beneficio de las monedas que se mueven. Por debajo de 1, el mercado está realizando pérdidas en agregado. Se muestra suavizado a 30 días porque a diario es demasiado ruidoso.",
        refresh_tier=1,
    ),
    Indicator(
        id="sth_sopr",
        label="STH-SOPR (14d)",
        category="comportamiento",
        weight=5,
        source="onchain",
        endpoint="sth-sopr",
        smooth_days=14,
        anchors=[(1.06, 0), (1.02, 15), (1.0, 35), (0.98, 55), (0.955, 75), (0.93, 92), (0.90, 100)],
        trigger=0.97,
        trigger_dir="below",
        decimals=4,
        historic={"2018-12": 0.92, "2020-03": 0.90, "2022-11": 0.93},
        summary="Lo mismo pero solo para las manos cortas. Son los primeros en rendirse, así que su capitulación suele preceder al suelo definitivo.",
        refresh_tier=2,
    ),
    Indicator(
        id="supply_in_loss_pct",
        label="% de oferta en pérdida",
        category="comportamiento",
        weight=6,
        source="onchain",
        endpoint="utxos-in-loss-pct",
        anchors=[(0.0038, 0), (1.0993, 12), (4.95445, 28), (15.7348, 48), (23.9554, 64), (29.5218, 76), (34.9036, 86), (37.996, 94), (42.6949, 100)],
        trigger=31.279,
        trigger_dir="above",
        unit="%",
        decimals=1,
        historic={"suelo 2022": 31.279},
        summary="Qué fracción de todas las monedas vale hoy menos de lo que costó. Más de la mitad de la red en pérdida es territorio de suelo de ciclo.",
        refresh_tier=1,
        calibration="datos",

    ),
    Indicator(
        id="vdd_multiple",
        label="VDD Multiple",
        category="comportamiento",
        weight=4,
        source="onchain",
        endpoint="vdd-multiple",
        anchors=[(3.0, 0), (2.0, 12), (1.5, 25), (1.1, 40), (0.85, 58), (0.65, 78), (0.5, 95), (0.4, 100)],
        trigger=0.7,
        trigger_dir="below",
        decimals=3,
        historic={"2015-01": 0.42, "2018-12": 0.50, "2020-03": 0.60, "2022-11": 0.55},
        summary="Valor destruido por días de tenencia, ponderado hacia los grandes tenedores antiguos. Bajo = los veteranos dejaron de vender.",
        refresh_tier=3,
    ),
    Indicator(
        id="sell_side_risk",
        label="Sell-Side Risk Ratio",
        category="comportamiento",
        weight=4,
        source="onchain",
        endpoint="sell-side-risk-ratio",
        anchors=[(0.012, 0), (0.008, 15), (0.005, 30), (0.0035, 45), (0.0022, 62), (0.0015, 80), (0.001, 95), (0.0007, 100)],
        trigger=0.002,
        trigger_dir="below",
        decimals=5,
        historic={"2018-12": 0.0012, "2020-03": 0.0016, "2022-11": 0.0014},
        summary="Beneficio y pérdida realizados contra el tamaño del mercado. Muy bajo = el mercado alcanzó equilibrio, ya casi nadie mueve monedas. Los suelos son aburridos.",
        refresh_tier=3,
    ),

    # =======================================================================
    # TÉCNICO — derivados localmente del precio, sin gastar cupo de API
    # =======================================================================
    Indicator(
        id="price_vs_200wma",
        label="Precio / MA 200 semanas",
        category="tecnico",
        weight=8,
        source="derived",
        endpoint=None,
        anchors=[(0.657723, 100), (0.82217, 94), (0.956466, 86), (1.0726, 76), (1.28794, 64), (1.82173, 48), (2.43449, 28), (4.34435, 12), (15.9113, 0)],
        trigger=0.912425,
        trigger_dir="below",
        historic={"suelo 2015": 0.912425, "suelo 2018": 1.01442, "suelo 2022": 0.657723},
        summary="La media de 200 semanas nunca ha sido perforada de forma duradera. Tocarla ha marcado el suelo de todos los ciclos.",
        refresh_tier=1,
        calibration="datos",
    ),
    Indicator(
        id="mayer_multiple",
        label="Mayer Multiple",
        category="tecnico",
        weight=6,
        source="derived",
        endpoint=None,
        anchors=[(0.232123, 100), (0.540301, 94), (0.661782, 86), (0.754937, 76), (0.87608, 64), (1.1256, 48), (1.39358, 28), (2.02227, 12), (13.0716, 0)],
        trigger=0.477181,
        trigger_dir="below",
        historic={"suelo 2015": 0.403757, "suelo 2018": 0.50825, "suelo 2022": 0.477181},
        summary="Precio dividido por la media de 200 días. Por debajo de 0.8 el precio está históricamente barato contra su propia tendencia.",
        refresh_tier=1,
        calibration="datos",
    ),
    Indicator(
        id="rsi_weekly",
        label="RSI semanal",
        category="tecnico",
        weight=5,
        source="derived",
        endpoint=None,
        anchors=[(25.7244, 100), (31.4179, 94), (34.4804, 86), (38.9407, 76), (44.827, 64), (56.4528, 48), (67.3796, 28), (78.1876, 12), (99.4381, 0)],
        trigger=27.9567,
        trigger_dir="below",
        decimals=1,
        historic={"suelo 2015": 27.9567, "suelo 2018": 28.7053, "suelo 2022": 25.7244},
        summary="RSI de 14 periodos en velas semanales. Por debajo de 30 solo ha ocurrido en los suelos de 2015, 2018 y 2022.",
        refresh_tier=1,
        calibration="datos",
    ),
    Indicator(
        id="rsi_monthly",
        label="RSI mensual",
        category="tecnico",
        weight=4,
        source="derived",
        endpoint=None,
        anchors=[(40.3442, 100), (41.8002, 94), (43.9753, 86), (46.1362, 76), (51.3043, 64), (59.2882, 48), (69.1715, 28), (82.1038, 12), (96.7381, 0)],
        trigger=43.7523,
        trigger_dir="below",
        decimals=1,
        historic={"suelo 2015": 44.5647, "suelo 2018": 43.7523, "suelo 2022": 40.3442},
        summary="RSI en velas mensuales. Rara vez baja de 30; lecturas bajo 40 han precedido subidas de entre 300% y 700%.",
        refresh_tier=1,
        calibration="datos",
    ),
    Indicator(
        id="drawdown_from_ath",
        label="Caída desde el máximo",
        category="tecnico",
        weight=5,
        source="derived",
        endpoint=None,
        anchors=[(-92.7486, 100), (-83.3586, 94), (-80.063, 86), (-74.8139, 76), (-63.872, 64), (-47.7746, 48), (-21.6031, 28), (-4.83558, 12), (0, 0)],
        trigger=-83.1871,
        trigger_dir="below",
        unit="%",
        decimals=1,
        historic={"suelo 2015": -84.5244, "suelo 2018": -83.1871, "suelo 2022": -76.6293},
        summary="Distancia porcentual al máximo histórico. Los suelos de ciclo se han formado entre -75% y -86%, con la excepción del crash relámpago de marzo de 2020.",
        refresh_tier=1,
        invert_chart=True,
        calibration="datos",
    ),

    # =======================================================================
    # FLUJOS Y SENTIMIENTO — confirmación, nunca señal principal
    # =======================================================================
    Indicator(
        id="accumulation_trend_score",
        label="Accumulation Trend Score",
        category="flujos",
        weight=5,
        source="onchain",
        endpoint="accumulation-trend-score",
        anchors=[(0.0, 0), (0.15, 15), (0.3, 30), (0.45, 45), (0.6, 62), (0.75, 80), (0.9, 95), (1.0, 100)],
        trigger=0.7,
        trigger_dir="above",
        decimals=3,
        historic={"2018-12": 0.85, "2020-03": 0.90, "2022-11": 0.88},
        summary="Mide si las carteras grandes están acumulando (cerca de 1) o distribuyendo (cerca de 0), ponderado por tamaño. Es de los pocos indicadores que mira la demanda, no la oferta.",
        refresh_tier=2,
    ),
    Indicator(
        id="exchange_netflow",
        label="Flujo neto a exchanges (7d)",
        category="flujos",
        weight=4,
        source="onchain",
        endpoint="exchange-netflow-btc",
        smooth_days=7,
        anchors=[(-167151, 100), (-16938.3, 94), (-9284.67, 86), (-5343.02, 76), (-2373.07, 64), (289.305, 48), (3311.79, 28), (7673.08, 12), (158022, 0)],
        trigger=-52318.2,
        trigger_dir="below",
        unit=" BTC",
        decimals=0,
        historic={"suelo 2015": -60180.1, "suelo 2018": -24330.6, "suelo 2022": -52318.2},
        summary="Cuánto BTC entra menos cuánto sale de los exchanges. Salidas sostenidas significan que las monedas se van a custodia propia: acumulación.",
        refresh_tier=2,
        calibration="datos",

    ),
    Indicator(
        id="etf_flow_30d",
        label="Flujo neto de ETF (30d)",
        category="flujos",
        weight=8,
        source="derived",
        endpoint=None,
        anchors=[(-7249.4, 100), (-5750.79, 94), (-4410.68, 86), (-2768.59, 76), (-435.725, 64), (2114.2, 48), (5208.75, 28), (8220.68, 12), (13205.7, 0)],
        trigger=-3993.34,
        trigger_dir="below",
        unit=" M USD",
        decimals=0,
        summary="Dinero neto que entra o sale de los ETF spot en los últimos 30 días. Es el único indicador del panel que mide al comprador institucional, que no deja huella on-chain.",
        refresh_tier=1,
    ),
    Indicator(
        id="etf_position_drawdown",
        label="Caída de posición ETF",
        category="flujos",
        weight=7,
        source="derived",
        endpoint=None,
        anchors=[(-20.172, 100), (-19.1386, 94), (-15.471, 86), (-10.7412, 76), (-7.89642, 64), (-2.23242, 48), (-0.128175, 28), (0, 0)],
        trigger=-13.3892,
        trigger_dir="below",
        unit="%",
        decimals=1,
        summary="Cuánto se ha deshecho la posición acumulada de los ETF desde su máximo. Es el análogo, del lado de la demanda, a la caída del precio desde máximos.",
        refresh_tier=1,
        invert_chart=True,
    ),
    Indicator(
        id="fear_greed",
        label="Fear & Greed",
        category="sentimiento",
        weight=3,
        source="onchain",
        endpoint="fear-greed",
        smooth_days=7,
        anchors=[(90, 0), (75, 8), (60, 20), (48, 35), (35, 52), (25, 70), (15, 90), (8, 100)],
        trigger=20.0,
        trigger_dir="below",
        decimals=0,
        historic={"2018-12": 11, "2020-03": 8, "2022-11": 20},
        summary="Índice compuesto de sentimiento del mercado. Útil solo como confirmación: el miedo extremo acompaña los suelos pero también aparece en caídas intermedias.",
        refresh_tier=2,
    ),
]


BY_ID: dict[str, Indicator] = {i.id: i for i in INDICATORS}

# Series auxiliares que no son indicadores por sí mismas pero que otros
# indicadores derivados necesitan como insumo.
SUPPORT_SERIES: dict[str, str] = {
    "btc_price": "btc-price",
    "cvdd": "cvdd",
    "balanced_price": "balanced-price",
    # SOPR sin ajustar. El endpoint `asopr` solo entrega desde noviembre de 2025
    # —289 días, sin ningún suelo de ciclo dentro—, así que se prueba esta
    # variante a ver si tiene más historia. Son métricas distintas (aSOPR
    # excluye los outputs de menos de una hora, casi siempre movimientos
    # internos de exchanges), así que NO se fusionan: se comparan y se decide.
    "sopr_raw": "sopr",
}


def onchain_indicators() -> list[Indicator]:
    return [i for i in INDICATORS if i.source == "onchain"]


def derived_indicators() -> list[Indicator]:
    return [i for i in INDICATORS if i.source == "derived"]


def default_weights() -> dict[str, int]:
    return {i.id: i.weight for i in INDICATORS}


def to_dict(ind: Indicator) -> dict[str, Any]:
    return {
        "id": ind.id,
        "label": ind.label,
        "category": ind.category,
        "category_label": CATEGORY_LABELS[ind.category],
        "default_weight": ind.weight,
        "source": ind.source,
        "trigger": ind.trigger,
        "trigger_dir": ind.trigger_dir,
        "unit": ind.unit,
        "decimals": ind.decimals,
        "smooth_days": ind.smooth_days,
        "historic": ind.historic,
        "summary": ind.summary,
        "anchors": ind.anchors,
        "invert_chart": ind.invert_chart,
    }
