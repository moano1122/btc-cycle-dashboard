## Qué mide

AVIV significa *Active Value to Investor Value*. Es un intento de arreglar el defecto más conocido del MVRV: **las monedas perdidas.**

## El problema que resuelve

El valor realizado, que está en el denominador del MVRV, valora cada bitcoin al precio del día en que se movió por última vez. Suena razonable hasta que uno se da cuenta de lo siguiente:

Hay entre **3 y 4 millones de BTC** —cerca del 20% de la oferta— que nunca se van a mover. Llaves perdidas en discos duros tirados a la basura, monedas de los primeros años cuyos dueños murieron o se olvidaron, el millón de BTC atribuido a Satoshi. Todas esas monedas se movieron por última vez cuando bitcoin valía céntimos, y siguen entrando en el cálculo con ese costo base ridículo.

El efecto es doble y sistemático:

1. Arrastra el valor realizado **hacia abajo**, porque incluye millones de monedas valoradas a casi cero.
2. Por tanto empuja el MVRV **hacia arriba**, haciendo que el mercado parezca más caro de lo que está.
3. Y como el porcentaje de monedas muertas cambia con el tiempo, el sesgo **no es constante**: los umbrales de MVRV de 2015 no son estrictamente comparables con los de hoy.

## Cómo se calcula

AVIV compara el valor de mercado contra la **media real del mercado** (*True Market Mean*), que se construye considerando únicamente el capital de los inversores activos: se descuentan las monedas que llevan tanto tiempo inmóviles que se consideran fuera de circulación económica, y se ajusta por el capital efectivamente invertido.

El resultado se convierte en Z-score igual que el MVRV, para que sea comparable a través del tiempo.

## Por qué funciona

Responde a la misma pregunta que el MVRV —¿está el precio por encima o por debajo del costo del capital invertido?— pero con un denominador más honesto.

En la práctica, AVIV tiende a dar señales **más simétricas entre ciclos**. Donde el MVRV muestra techos cada vez más bajos (7, luego 5, luego menos) por culpa del sesgo acumulado, AVIV mantiene mejor la escala.

### Cómo leerlo

| Zona | AVIV Z-Score | Qué significa |
|---|---|---|
| Euforia | mayor a 2 | Techo de ciclo. |
| Caro | 1 a 2 | Bull avanzado. |
| Neutral | 0 a 1 | Sin extremos. |
| **Valor** | **−0.5 a 0** | **Por debajo del costo del capital activo.** |
| **Suelo** | **menor a −1** | **Zona de capitulación.** |

Lecturas aproximadas en suelos: **−1.4** en 2015, **−1.2** en diciembre de 2018, **−1.0** en marzo de 2020 y **−1.1** en noviembre de 2022.

### Dónde ha fallado

> **Es más nuevo y menos probado.** AVIV lleva relativamente poco tiempo en circulación comparado con el MVRV. Sus lecturas en ciclos antiguos son reconstrucciones retrospectivas, no señales que alguien usara en tiempo real. Eso es una diferencia importante: es mucho más fácil que un indicador "acierte" ciclos pasados cuando se diseñó conociéndolos.

> **Depende de decisiones de modelado.** ¿A partir de cuántos años se considera una moneda muerta? ¿Se excluye del todo o se pondera? Distintos proveedores responden distinto y publican valores distintos. No hay un estándar.

> **Correlaciona mucho con el MVRV Z-Score.** En la práctica se mueven casi en paralelo. Su confirmación mutua aporta menos información de la que parece, y hay riesgo de contar dos veces la misma señal si se les da mucho peso a ambos.

### Cómo usarlo en la práctica

Trátelo como **una segunda opinión sobre el MVRV, no como un indicador independiente**. Cuando ambos coincidan, no lo interprete como dos confirmaciones: es esencialmente la misma medición hecha de dos maneras.

Su valor real aparece cuando **discrepan**. Si el MVRV Z-Score dice que aún no hay suelo pero el AVIV ya está bajo −1, la diferencia le está diciendo que el sesgo de monedas perdidas está distorsionando la lectura clásica, y probablemente convenga fiarse más del AVIV.
