## Qué mide

Este es el indicador que usted mencionó: **el precio al que compraron los que entraron hace poco.**

La cadena de bloques sabe exactamente cuándo se movió cada moneda por última vez y a qué precio. Con eso se puede separar a los tenedores en dos grupos:

- **STH (Short-Term Holders):** monedas movidas en los últimos **155 días** (~5 meses).
- **LTH (Long-Term Holders):** monedas quietas desde hace más de 155 días.

El STH-MVRV compara el precio actual con el costo base promedio del primer grupo.

## Por qué 155 días y no otro número

No es arbitrario. Al analizar la probabilidad de que una moneda se mueva en función de cuánto lleva quieta, se encuentra una transición: **alrededor de los cinco meses, la probabilidad de que una moneda se gaste cae bruscamente y ya no vuelve a subir**. Quien aguantó ese tiempo dejó de ser un especulador y pasó a ser un tenedor.

155 días es donde está esa transición estadística.

## Cómo se calcula

```
STH-MVRV = Precio actual / Precio realizado de los STH
```

Donde el *precio realizado de los STH* es el costo base promedio de todas las monedas movidas en los últimos 155 días.

- **STH-MVRV = 1.20** → los compradores recientes tienen un 20% de ganancia media.
- **STH-MVRV = 0.85** → están un 15% en pérdida.

## Por qué funciona

Los tenedores de corto plazo son **la oferta marginal del mercado**. Son quienes venden cuando hay pánico, porque su convicción es baja y su pérdida es reciente y dolorosa.

El costo base de este grupo funciona como un **nivel de soporte y resistencia psicológico real**, no dibujado sobre un gráfico:

- En mercados alcistas, el precio rebota una y otra vez sobre este nivel. Cada caída hasta ahí encuentra compradores que promedian a la baja.
- En mercados bajistas, el precio pasa a cotizar **por debajo** y ese mismo nivel se convierte en techo: cada intento de recuperación choca contra vendedores que quieren salir en su punto de equilibrio.

**El cruce sostenido de un régimen al otro es una de las señales de cambio de tendencia más limpias que existen on-chain.**

### Cómo leerlo

| Zona | STH-MVRV | Qué significa |
|---|---|---|
| Sobrecalentado | mayor a 1.3 | Compradores recientes con mucha ganancia: hay incentivo para tomar beneficios. |
| Alcista sano | 1.0 a 1.2 | El precio se apoya en el costo base reciente. |
| **Estrés** | **0.85 a 1.0** | **Manos cortas en pérdida.** |
| **Capitulación** | **menor a 0.85** | **Zona de suelo.** |

Lecturas en suelos: **0.70** en 2015, **0.74** en 2018, **0.72** en marzo de 2020 y **0.76** en noviembre de 2022.

**Contexto de agosto de 2026:** el STH-MVRV ronda **0.84**. El precio lleva más de nueve meses por debajo del costo base de los compradores recientes, lo que es la firma característica de un mercado bajista establecido. Pero 0.84 todavía no es 0.76.

### Dónde ha fallado

> **Se recupera rápido y puede dar falsas señales de fin de bear.** Como la ventana es de solo 155 días, el costo base de los STH se recalcula continuamente. En un rebote fuerte dentro de un mercado bajista, el indicador vuelve por encima de 1 y parece que empezó el bull. Pasó en agosto de 2019 y de nuevo en marzo de 2024. **Un cruce sobre 1 solo cuenta si se sostiene varias semanas.**

> **No distingue tamaño.** Un ballena que compró 5.000 BTC pesa lo mismo en el promedio que muchos compradores pequeños. En periodos con actividad institucional concentrada, el promedio puede no representar a la mayoría de participantes.

### Cómo usarlo en la práctica

Combínelo con el LTH-MVRV. La señal más fiable de suelo de ciclo no es que el STH-MVRV baje mucho, sino que **STH-MVRV y LTH-MVRV converjan**: significa que ya no hay diferencia entre lo que pagó el especulador reciente y lo que pagó el veterano, es decir, que todas las cohortes están igual de golpeadas. Ese es el propósito del indicador *Convergencia STH ↔ LTH* de este panel.
