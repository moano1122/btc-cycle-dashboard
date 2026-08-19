## Qué mide

CVDD significa *Cumulative Value Days Destroyed*. Es un **modelo de piso duro**: una línea que, históricamente, el precio de bitcoin ha tocado exactamente en los suelos de ciclo y casi nunca ha perforado.

Este panel muestra el **ratio precio / CVDD**, de modo que:

- **Ratio 1.0** → el precio está tocando el piso histórico.
- **Ratio 3.0** → el precio está tres veces por encima.

## Cómo se calcula

```
CVDD = Valor acumulado destruido en USD / (días desde el génesis × 6.000.000)
```

El "valor destruido" acumula, para cada transacción de la historia, el número de monedas movidas multiplicado por los días que llevaban quietas y por el precio al que se movieron. En otras palabras: **suma todo el capital que ha cambiado de manos, ponderado por cuánto tiempo llevaba inmóvil.**

Dividirlo por el tiempo transcurrido convierte esa suma en una especie de **suelo de precio que crece con la adopción**. La constante 6.000.000 es un factor de escala empírico que Willy Woo, su creador, ajustó para que la línea coincidiera con los mínimos históricos.

## Por qué funciona

El argumento es de transferencia de riqueza. Cada vez que monedas viejas se mueven, capital paciente pasa a manos nuevas. El CVDD mide la acumulación de esas transferencias.

Cuando el precio cae hasta el nivel del CVDD, significa que **el precio de mercado ha convergido con el precio promedio al que se ha transferido la riqueza a lo largo de toda la historia de la red.** Eso ha marcado el punto de máxima transferencia de manos débiles a manos fuertes.

### Cómo leerlo

| Zona | Precio/CVDD | Qué significa |
|---|---|---|
| Techo | mayor a 4 | Muy lejos del piso. |
| Caro | 2.5 a 4 | Bull avanzado. |
| Neutral | 1.7 a 2.5 | Tendencia normal. |
| **Cerca del piso** | **1.0 a 1.3** | **Zona de suelo histórico.** |
| Perforación | menor a 1.0 | Prácticamente no ha ocurrido. |

Lecturas en suelos: **1.00** en 2015, **1.05** en diciembre de 2018, **1.12** en marzo de 2020 y **1.20** en noviembre de 2022.

### Dónde ha fallado

> **La constante de 6 millones es un ajuste a los datos, no una derivación teórica.** Willy Woo la eligió porque hacía que la línea coincidiera con los mínimos conocidos en el momento en que creó el indicador. Eso es sobreajuste por definición. Que haya seguido funcionando después es interesante, pero no convierte la constante en una ley.

> **Los suelos se han ido alejando del piso.** 1.00 → 1.05 → 1.12 → 1.20. Cada ciclo el precio ha tocado el CVDD con menos precisión. Si la tendencia continúa, el próximo suelo podría formarse en 1.3 o 1.4 sin que el precio se acerque nunca a la línea, y esperar el toque exacto le haría perder el suelo entero.

> **Es un modelo, no una medición.** A diferencia del MVRV o el SOPR, que salen de la contabilidad de la cadena, el CVDD incorpora una decisión de diseño arbitraria. Trátelo con más escepticismo que a los indicadores puramente contables.

### Cómo usarlo en la práctica

Como **referencia de rango extremo**, no como objetivo de precio. Su utilidad es contestar "¿cuánto más podría caer esto razonablemente?", que es una pregunta de gestión de riesgo, no de timing.

Si usted planea escalonar compras a lo largo de un bear market, el nivel del CVDD es un lugar defendible para colocar el último y mayor tramo.
