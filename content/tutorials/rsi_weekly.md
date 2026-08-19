## Qué mide

El RSI (*Relative Strength Index*) de 14 periodos aplicado a **velas semanales**. Es el único indicador puramente técnico con peso relevante en este panel, y está aquí por una razón muy concreta que se explica abajo.

## Cómo se calcula

```
RSI = 100 − 100 / (1 + RS)
RS  = Media de las subidas de las últimas 14 semanas / Media de las bajadas
```

Se usa el suavizado de Wilder, que es la convención estándar y la que usa TradingView. Este panel lo calcula localmente a partir de los cierres de Binance, sin gastar cupo de API.

El resultado oscila entre 0 y 100:

- **Por encima de 70** → sobrecompra.
- **Por debajo de 30** → sobreventa.

## Por qué está en un panel on-chain

Porque en marco semanal, en bitcoin, el RSI bajo 30 es un evento **extraordinariamente raro**.

En diario, el RSI cruza 30 varias veces al año y no significa gran cosa. Pero al agregar a velas semanales se filtra casi todo el ruido, y el resultado es que **el RSI semanal solo ha bajado de 30 en un puñado de ocasiones en toda la historia de bitcoin**: el bear market de 2015, el de 2018 y el de 2022.

En los tres casos marcó la zona del mínimo semanal del ciclo.

No es un indicador con una teoría económica detrás. Es una regularidad estadística sobre un mercado que rara vez alcanza ese grado de sobreventa en marco largo.

### Cómo leerlo

| Zona | RSI semanal | Qué significa |
|---|---|---|
| Sobrecompra extrema | mayor a 80 | Solo en bull markets parabólicos. |
| Alcista | 55 a 70 | Tendencia sana. |
| Neutral | 40 a 55 | Sin dirección clara. |
| **Debilidad** | **30 a 40** | **Bear market establecido.** |
| **Sobreventa extrema** | **menor a 30** | **Muy poco frecuente. Zona de suelo.** |

Lecturas en suelos: **28** en enero de 2015, **29** en diciembre de 2018, **31** en marzo de 2020 y **26** en junio de 2022.

**Contexto de agosto de 2026:** el RSI semanal está en **41**. Débil, pero todavía no en la zona rara.

### Dónde ha fallado

> **Un indicador puramente técnico no sabe nada del activo.** El RSI mide únicamente la magnitud relativa de las velas recientes. Un RSI de 25 en un activo en quiebra terminal se ve igual que uno en el suelo de un ciclo. Toda su utilidad depende de la premisa de que bitcoin sigue en una tendencia estructural alcista de largo plazo; si esa premisa falla, el indicador no vale nada.

> **Puede quedarse abajo mucho tiempo.** En junio de 2022 tocó 26; el precio siguió cayendo otro 35% hasta noviembre. La sobreventa puede profundizarse.

> **El mínimo de RSI y el mínimo de precio rara vez coinciden.** En 2022 el mínimo de RSI fue en junio y el de precio en noviembre. Buscar la coincidencia exacta es perder el tiempo.

### Cómo usarlo en la práctica

Como **corroboración externa** al bloque on-chain. Su virtud es que es completamente independiente: no comparte insumos con el MVRV, el SOPR ni ninguno de los demás. Cuando un indicador técnico y uno on-chain coinciden, la señal es más informativa que cuando coinciden dos on-chain que comparten denominador.

Además es el único indicador del panel que usted puede verificar en cualquier plataforma de gráficos en diez segundos, lo cual es una ventaja práctica nada despreciable.
