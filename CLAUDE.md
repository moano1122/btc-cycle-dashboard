# Contexto del proyecto

Dashboard local de indicadores on-chain de bitcoin para detectar el suelo del
bear market. El usuario toma decisiones de compra reales con esta herramienta,
así que la corrección de los datos y la honestidad sobre la incertidumbre pesan
más que cualquier otra consideración.

## Reglas de trabajo en este repo

- **Nunca inventar valores de indicadores.** Si un dato no está en caché, la
  interfaz debe decir "sin datos", no estimar ni interpolar hacia el presente.
- **La cobertura siempre visible.** Cualquier score agregado debe ir acompañado
  del porcentaje de indicadores que realmente lo alimentan.
- **Documentar dónde falla cada indicador.** Cada tutorial tiene una sección de
  fallos conocidos. No es opcional: es lo que evita que la herramienta se use
  con exceso de confianza.
- **Respetar el presupuesto de API.** El plan gratuito son 10 req/hora y 15/día.
  El control de cupo vive en `sources/bitcoin_data.py` y se persiste en SQLite.
  Nunca añadir una llamada que lo salte.
- **Preferir cálculo local.** Si algo se puede derivar del precio de Binance
  (gratis e ilimitado), calcúlelo en `derived.py` en vez de gastar cupo.

## Arquitectura

- `backend/catalog.py` — fuente única de verdad de los 28 indicadores: umbrales,
  anclajes de puntuación, pesos, lecturas históricas y tier de refresco.
- `backend/scoring.py` — interpolación por anclajes y score ponderado con
  renormalización por cobertura.
- `backend/refresh.py` — orquestador que prioriza por (tier, peso) dentro del cupo.
- `backend/store.py` — SQLite. El dashboard lee siempre de aquí, nunca de la red.
- `frontend/` — sin build ni framework. HTML + CSS + JS plano, ECharts y marked
  por CDN.
- `content/tutorials/<id>.md` — un tutorial por indicador, mismo `id` del catálogo.

## Añadir un indicador

1. Entrada nueva en `INDICATORS` (`catalog.py`), con anclajes calibrados sobre
   lecturas reales de suelos históricos, no inventados.
2. `content/tutorials/<id>.md` con la misma estructura que los existentes,
   incluida la sección de fallos.
3. Si es derivado, añadir el cálculo a `derived.recompute_all()`.

No hace falta tocar el frontend ni la API: ambos recorren el catálogo.

## Estado de los datos

En agosto de 2026 el proveedor on-chain solo tiene datos si hay API key
configurada en `.env`. Sin key el cupo se agota en minutos. El bloque de
indicadores técnicos (Binance) funciona siempre.
