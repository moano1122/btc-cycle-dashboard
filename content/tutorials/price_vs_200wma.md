## Qué mide

La media móvil de **200 semanas** —unos cuatro años, aproximadamente un ciclo de
halving completo— es la línea de suelo más citada del análisis de bitcoin.

Este indicador muestra el **ratio** entre el precio y esa media:

- **Ratio 3.0** → el precio está tres veces por encima de su media de cuatro años.
- **Ratio 1.0** → el precio está exactamente sobre la media.
- **Ratio 0.66** → el precio está un 34% por debajo.

```
Ratio = Precio de cierre / Media simple de los últimos 1.400 días
```

Se calcula localmente desde los cierres diarios de Binance, sin gastar cupo de la
API on-chain.

## Corrección importante sobre este indicador

> **La versión popular de este indicador es falsa, y conviene saberlo.**
>
> Se repite mucho que "el precio de bitcoin nunca ha perforado su media de 200
> semanas de forma duradera" y que en noviembre de 2022 "solo la tocó y rebotó".
> Los datos de esta misma herramienta dicen otra cosa:
>
> - El **21 de noviembre de 2022** el precio cerró en 15.781 dólares con la media
>   de 200 semanas en **23.994**. El ratio fue **0.658**: un **34% por debajo**.
> - El precio se mantuvo por debajo de la media **210 días consecutivos**, del 19
>   de agosto de 2022 al 16 de marzo de 2023. Siete meses, no unos días.
> - En total ha pasado **el 18% de los días** por debajo de la media dentro de la
>   ventana que esta herramienta puede medir.
>
> No es una línea infranqueable. Es una media móvil como cualquier otra, y el
> precio la atraviesa con normalidad en los mercados bajistas profundos.

## Por qué sigue siendo útil

Aunque la versión mitológica sea falsa, el indicador conserva valor real: **la
media de 200 semanas es el precio promedio de un ciclo completo.** Al abarcar
cuatro años incluye un techo, un bear market y una recuperación, así que se mueve
despacio y funciona como referencia estable del centro de gravedad del precio.

Lo que informa no es "aquí está el suelo", sino **en qué parte de su rango de
largo plazo está cotizando el precio**. Eso es útil para dimensionar compras.

### Cómo leerlo

Los umbrales de esta herramienta están derivados de la distribución real
observada, no de la literatura:

| Zona | Ratio | Percentil histórico |
|---|---|---|
| Extremo alcista | mayor a 2.4 | 90% superior |
| Caro | 1.7 a 2.4 | — |
| Neutral | 1.24 a 1.7 | mediana en 1.24 |
| Débil | 1.0 a 1.24 | — |
| **Zona de suelo** | **menor a 0.88** | **8% inferior** |
| Extremo | 0.66 a 0.71 | mínimo observado |

**Contexto de agosto de 2026:** el ratio está en **1.010**, en el percentil 19 de
su rango observado. El precio está justo sobre la media.

Y aquí está la lectura que importa: **estar sobre la media de 200 semanas no es
una señal de suelo.** En 2022 el suelo se formó un 34% por debajo. Si ese
precedente se repitiera, con la media hoy en unos 64.000 dólares, implicaría un
precio en torno a los 42.000. Con el ratio en 1.01 no estamos cerca de eso.

### Dónde ha fallado

> **La media sube mientras el precio cae, y eso engaña.** La ventana de cuatro
> años todavía incluye los precios altos de 2024-2025, así que la media de 200
> semanas sigue ascendiendo. El ratio puede acercarse a 1 sin que el precio baje,
> simplemente porque la media lo alcanza por arriba. Buena parte de la lectura
> actual de 1.01 es exactamente eso.

> **Es rezagado por construcción.** Una media de 1.400 días reacciona lentísimo.
> Si bitcoin entrara en un régimen de rendimientos estructuralmente más bajos, la
> media tardaría años en reflejarlo y el indicador señalaría "barato" de forma
> persistente y equivocada.

> **La calibración descansa en un solo suelo.** El plan gratuito de datos da
> cuatro años de historia, y la serie del ratio necesita 1.400 días previos para
> arrancar, así que empieza en junio de 2021. Dentro de esa ventana hay
> exactamente **un** suelo de ciclo. Los umbrales de arriba son honestos respecto
> a los datos disponibles, pero una observación no es una regularidad.

### Cómo usarlo en la práctica

Como **contexto de nivel**, nunca como disparador. Su mensaje es "el precio está
en la parte baja de su rango de largo plazo", que ayuda a dimensionar compras
pero no dice nada sobre si el suelo ya se formó.

Y con la corrección de arriba en mente: si usted esperaba que tocar la media de
200 semanas fuera la señal, el precedente de 2022 sugiere que la señal real está
bastante más abajo.
