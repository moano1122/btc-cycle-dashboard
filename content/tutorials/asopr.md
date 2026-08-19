## Qué mide

SOPR significa *Spent Output Profit Ratio*: **el ratio de beneficio de las monedas que se mueven cada día.**

Es una pregunta distinta a la del MVRV. El MVRV mira la ganancia *en papel* de todo el mundo. El SOPR mira solo a **quienes efectivamente mueven monedas hoy**, y pregunta si lo están haciendo con ganancia o con pérdida.

Es la diferencia entre "cuánto vale mi cartera" y "a qué precio estoy vendiendo de verdad".

## Cómo se calcula

Para cada output gastado en la cadena:

```
SOPR de ese output = Precio al que se gastó / Precio al que se creó
```

El SOPR del día es el agregado de todos ellos. La **a** de aSOPR significa *adjusted*: se excluyen los outputs con vida menor a una hora, que son casi siempre movimientos internos de exchanges y no representan decisiones económicas reales. Esa limpieza importa mucho.

- **aSOPR mayor a 1** → en promedio se está vendiendo con ganancia.
- **aSOPR menor a 1** → en promedio se está vendiendo con pérdida.

Este panel lo muestra **suavizado a 30 días**, porque el dato diario es tan ruidoso que a simple vista no dice nada.

## Por qué funciona

El SOPR captura un comportamiento humano muy consistente: **a la gente le cuesta vender en pérdida.** Es aversión a la pérdida en estado puro, y deja una firma clara en los datos.

De ahí salen dos usos:

**1. El nivel 1.0 como línea de batalla.** En un mercado alcista, cuando el aSOPR se acerca a 1 desde arriba, aparecen compradores: nadie quiere vender en su punto de equilibrio, así que la presión vendedora se seca y el precio rebota. El nivel 1.0 actúa como soporte. En un mercado bajista pasa lo contrario: cada vez que el aSOPR intenta superar 1, sale gente a vender en su punto de equilibrio y el precio se rechaza.

**2. Los extremos como capitulación.** Cuando el aSOPR cae claramente por debajo de 1 y se queda ahí, significa que hay ventas masivas con pérdidas materializadas. Eso es rendición, y la rendición agota la oferta.

### Cómo leerlo

| Zona | aSOPR (30d) | Qué significa |
|---|---|---|
| Toma de ganancias | mayor a 1.03 | Realización agresiva de beneficios. |
| Alcista | 1.0 a 1.03 | Ventas con ganancia moderada. |
| **Estrés** | **0.98 a 1.0** | **Se empieza a vender en pérdida.** |
| **Capitulación** | **menor a 0.96** | **Rendición generalizada.** |

Lecturas en suelos: **0.94** en 2015, **0.95** en diciembre de 2018, **0.95** en marzo de 2020 y **0.96** en noviembre de 2022.

### La señal más útil no es el mínimo

Aquí hay un matiz que vale oro y que casi nadie explica bien: **el suelo del precio no coincide con el mínimo del aSOPR, sino con su recuperación por encima de 1.**

La secuencia histórica es siempre la misma:

1. El aSOPR se hunde bajo 1 → empieza la capitulación.
2. Se queda bajo 1 durante semanas o meses → la capitulación se agota.
3. **Cruza de vuelta por encima de 1 y se mantiene ahí** → la oferta en pérdida se acabó; los que quedan solo venden con ganancia.

El paso 3 es la confirmación. Llega después del mínimo del precio, así que le hará perder los primeros puntos porcentuales del rebote, pero reduce muchísimo la probabilidad de comprar demasiado pronto.

### Dónde ha fallado

> **Es extremadamente ruidoso sin suavizar.** El dato diario cruza el nivel 1.0 constantemente sin significar nada. Cualquier análisis serio usa una media de al menos 7 días; este panel usa 30.

> **Las monedas perdidas y los movimientos internos lo contaminan.** El ajuste de una hora limpia buena parte del ruido de exchanges, pero no todo. Movimientos de custodia de ETFs, reestructuraciones de wallets institucionales y consolidaciones de UTXOs siguen apareciendo como "gasto" cuando no hubo ninguna decisión de venta.

### Cómo usarlo en la práctica

Úselo como **confirmación de que la fase de capitulación terminó**, no como detector del mínimo. Si su objetivo es acumular durante meses, el aSOPR bajo 1 le dice que está dentro de la ventana. Si su objetivo es concentrar una compra grande, esperar el cruce sostenido sobre 1 es más caro pero mucho más seguro.
