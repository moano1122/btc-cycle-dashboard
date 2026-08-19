# BTC Indicators — detección de suelo de ciclo

Dashboard local que consolida 30 indicadores on-chain, técnicos y de flujo institucional de bitcoin, los
traduce a una puntuación común de "suelo de mercado", los combina en un score
ponderado editable y avisa por Telegram cuando cruzan sus umbrales.

Cada indicador trae un tutorial completo: qué mide, cómo se calcula, por qué
funciona, cuál fue su lectura en los suelos de 2015, 2018, marzo 2020 y
noviembre 2022, y **dónde ha fallado**.

---

## Arranque rápido

```bash
pip install -r requirements.txt
```

```bash
python run.py
```

Abre el navegador en `http://127.0.0.1:8848`.

Otros comandos:

```bash
python run.py --refresh
```

```bash
python run.py --status
```

---

## Configuración

Copie `.env.example` a `.env` y rellene:

### 1. API key de datos on-chain (importante)

Regístrese gratis en **bitcoin-data.com** y copie su API key a `BITCOIN_DATA_API_KEY`.

Sin key el cupo es de **10 peticiones por hora y 15 al día**, lo que no alcanza
para los 22 indicadores on-chain del catálogo. El sistema no se rompe —prioriza,
cachea y marca lo que quedó sin refrescar— pero la cobertura será baja.

Si sube a un plan de pago, ajuste también `BITCOIN_DATA_REQ_PER_HOUR` y
`BITCOIN_DATA_REQ_PER_DAY` a los límites de su plan. El sistema los respeta de
forma estricta y nunca los excede.

### 2. Telegram (opcional)

1. Hable con `@BotFather` → `/newbot` → copie el token a `TELEGRAM_BOT_TOKEN`.
2. Hable con `@userinfobot` → copie su ID numérico a `TELEGRAM_CHAT_ID`.
3. Pruebe el envío con el botón del dashboard.

---

## Cómo funciona

### Fuentes de datos

| Fuente | Qué aporta | Costo | Historia |
|---|---|---|---|
| **bitcoin-data.com** | 22 métricas on-chain (MVRV, SOPR, NUPL, Puell, Reserve Risk…) | gratis con key | 4 años |
| **Coin Metrics** | MVRV, precio, emisión, hashrate y flujos de exchange | gratis, sin key | **desde 2010** |
| **Binance** | Cierres diarios de BTCUSDT | gratis, sin límite | desde 2017 |
| **Farside Investors** | Flujos diarios de los ETF spot, por fondo y agregados | gratis | desde ene-2024 |

Los flujos de ETF cubren el punto ciego de todo el bloque on-chain: cuando alguien
compra un ETF spot, la operación se ejecuta contra custodios y mesas OTC y **no
deja huella en la cadena**. La posición acumulada de los ETF hizo máximo el 9 de
octubre de 2025, el mismo día que el precio, en un techo que ningún indicador
on-chain señaló.

Coin Metrics es lo que permite calibrar contra **tres suelos de ciclo** (2015,
2018 y 2022) en vez de uno solo. Sus series se guardan con prefijo `cm_` y nunca
sobrescriben las del proveedor principal: `reconcile.py` compara ambas en el
tramo solapado y solo extiende la historia hacia atrás si coinciden.

Todo lo derivable del precio —medias móviles, Mayer, RSI semanal y mensual,
caída desde máximos— se calcula localmente desde Binance. Eso libera unas seis
peticiones diarias del cupo on-chain para las métricas irremplazables.

### Arquitectura de caché

El dashboard **siempre lee de SQLite, nunca de la red**. Si la API está caída o
el cupo agotado, la herramienta sigue funcionando con el último dato bueno y lo
marca como rancio.

Es una decisión deliberada: una decisión de compra no debe depender de que un
proveedor externo responda en ese instante.

### Prioridad de refresco

Como el cupo gratuito no alcanza para todo, los indicadores se refrescan por
prioridad: los de mayor peso a diario (tier 1), los secundarios cada dos días
(tier 2) y los marginales semanalmente (tier 3). El orden es estable, así que si
el cupo se agota a mitad de un ciclo, la siguiente pasada retoma donde se quedó.

### El score agregado

Cada indicador se traduce a una escala 0-100 mediante interpolación entre
anclajes calibrados con las lecturas reales de los suelos históricos. El score
final es el promedio ponderado.

**Renormalización por cobertura:** si faltan datos de varios indicadores, el
score se calcula solo con los disponibles y se reporta el porcentaje de
cobertura. Un score de 72 con 40% de cobertura no vale lo mismo que uno de 72
con 95%, y la interfaz muestra esa diferencia en vez de esconderla.

Los pesos son editables desde el dashboard y se guardan.

### Alertas

- Solo se avisa **en el cruce**, no mientras dure la condición.
- **Histéresis del 3%** para evitar mensajes por oscilaciones alrededor del umbral.
- Los **datos rancios no disparan** alertas.

---

## Refresco automático

El servidor intenta refrescar cada hora mientras está abierto, respetando el
cupo: un intento sin cupo disponible no cuesta nada y así el catálogo se va
rellenando conforme se renueva la ventana horaria.

Para que corra sin tener el dashboard abierto, cree una tarea programada:

```bash
schtasks /create /tn "BTC Indicators" /tr "python D:\claude_projects\btc_indicators\run.py --refresh" /sc hourly
```

---

## Tests

```bash
python -m pytest tests/ -q
```

198 tests que cubren la interpolación de anclajes, la renormalización por
cobertura, la histéresis de las alertas, el control de cupo, la matemática del
RSI y las medias móviles, la extracción de valores de la API y todos los
endpoints HTTP.

Los tests del catálogo no son decorativos: fueron los que detectaron que dos
indicadores disparaban su alerta en zona neutra de su propia escala, y que la
calibración de las series semanales no registraba su suelo de referencia.

```bash
python scripts/calibrate.py
```

Regenera los anclajes desde la distribución real de los datos en caché. Correrlo
después de conseguir historia completa (plan de pago) mejoraría notablemente la
calibración.

---

## Verificación contra fuentes públicas

Los valores del sistema se contrastaron contra sitios públicos independientes en
las mismas fechas:

| Métrica | Fecha | Este sistema | Fuente pública | Desvío |
|---|---|---|---|---|
| Puell Multiple | 2026-07-28 | 0.6455 | 0.65 | 0.7% |
| MVRV Z-Score | 2026-08-08 | 0.4184 | 0.42 | 0.4% |
| MVRV Ratio | 2026-08 | 1.2349 | 1.24 | 0.4% |
| Precio realizado | 2026-08 | $52.656 | $52.330 | 0.6% |

Además, los dos proveedores de datos coinciden entre sí en el tramo que solapan:
correlación 1.0000 en precio, 0.9972 en MVRV, 0.9995 en MVRV Z-Score y 0.9941 en
Hash Ribbons.

---

## Calibración: lo que salió mal la primera vez

Los umbrales iniciales venían de la literatura publicada. Al confrontarlos con
las series reales del proveedor, **cinco estaban equivocados**, porque
bitcoin-data.com escala varias series de forma distinta a las fuentes habituales:

| Indicador | Suelo nov-2022 según literatura | Suelo nov-2022 real |
|---|---|---|
| Precio / CVDD | 1.20 | **3.36** |
| Precio / MA 200 semanas | 1.02 | **0.658** |
| NUPL | −0.15 | **−0.284** |
| Precio / Balanced Price | 1.02 | **1.40** |
| Reserve Risk | 0.0016 | **0.000409** |

El caso de la MA de 200 semanas es el más instructivo, porque el error no era del
proveedor sino de la creencia popular: se repite que el precio "nunca perfora esa
media de forma duradera", y los datos muestran que en 2022 cotizó **34% por
debajo durante 210 días seguidos**.

### Cómo se calibra ahora

Dos cosas separadas, y la distinción importa:

- **La forma de la escala** sale de los percentiles de toda la historia
  disponible. Anclarla solo a los suelos falla cuando hay pocos: con un único
  suelo conocido, la curva entre ese punto y la mediana se vuelve una recta
  larguísima que regala puntuación.
- **El umbral de alerta** sale de la **mediana de los suelos de ciclo**. Se usa
  la mediana y no el suelo más flojo porque en 2018 el precio apenas rozó su
  media de 200 semanas (1.014) mientras que en 2022 se hundió a 0.658: anclar al
  más flojo haría saltar la alerta con un simple roce.

Marzo de 2020 se registra pero no calibra: fue un shock de liquidez de dos
semanas, no un suelo por agotamiento, y muchos indicadores no llegaron a
extremos.

Cada indicador muestra en el dashboard cuántos ciclos respaldan su umbral:

- **3 ciclos** — 10 indicadores, entre ellos MVRV Z-Score, Puell, Mayer, RSI y la
  caída desde máximos.
- **1 ciclo** — 10 indicadores que solo tiene el proveedor de 4 años.
- **sin respaldo** — 8 indicadores todavía sin datos suficientes.

---

## Advertencias

Léalas antes de tomar decisiones con esto:

1. **Tres suelos de ciclo siguen siendo una muestra pequeña.** Diez indicadores
   se calibran contra 2015, 2018 y 2022; los otros diez, solo contra 2022. Ni
   tres ni uno son suficientes para una inferencia estadística sólida. El
   dashboard marca cuántos respaldan cada umbral: fíjese en esa etiqueta antes de
   confiar en una señal.

2. **En el techo de octubre de 2025 ningún indicador on-chain mayor dio señal
   limpia de venta** antes de la caída del 52% que siguió. La entrada de los ETFs
   spot y los tesoros corporativos cambió quién compra y cómo, y los umbrales
   heredados de ciclos anteriores pueden estar sesgados.

3. **Los suelos se han ido haciendo menos profundos ciclo tras ciclo.** Caídas
   de −86%, −84%, −77%. NUPL de −0.25, −0.16, −0.15. Esperar los extremos de 2018
   probablemente signifique perderse el suelo.

4. **Varios indicadores comparten insumos.** MVRV, NUPL, AVIV y Balanced Price
   usan todos el precio realizado. Que coincidan no son cuatro confirmaciones
   independientes.

5. **Esto no es asesoría financiera.** Es una herramienta para organizar
   información. La decisión es suya.

---

## Estructura

```
backend/
  catalog.py      definición de los 30 indicadores, umbrales y anclajes
  scoring.py      motor de puntuación y score agregado
  refresh.py      orquestador con presupuesto de API
  derived.py      indicadores calculados localmente
  alerts.py       evaluación de disparos y Telegram
  store.py        caché SQLite
  api.py          rutas HTTP
  sources/
    bitcoin_data.py   cliente on-chain con control de cupo
    market.py         precio desde Binance
  reconcile.py    fusión entre proveedores con verificación previa
  sources/coinmetrics.py   historia larga y gratuita desde 2010
  sources/etf.py           flujos de los ETF spot (Farside)
scripts/
  calibrate.py    deriva los anclajes de los suelos de ciclo reales
tests/            198 tests
frontend/         dashboard (HTML + CSS + JS, sin build)
content/tutorials/  28 tutoriales en markdown
data/cache.db     caché local (no se sube a git)
```

Para añadir un indicador: agréguelo a `INDICATORS` en `catalog.py` y escriba
`content/tutorials/<id>.md`. El resto del sistema lo recoge solo.
