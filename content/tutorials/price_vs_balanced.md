## Qué mide

El **Balanced Price** es otro modelo de suelo, y de los que mejor han funcionado. Este panel muestra el ratio entre el precio y ese nivel.

```
Balanced Price = Precio realizado − Precio de transferencia
```

Donde:

- **Precio realizado** = lo que el mercado *pagó* por sus monedas (el costo base agregado).
- **Precio de transferencia** = lo que el mercado ya *transfirió*, medido como valor total transferido dividido por la oferta.

## Por qué funciona

La resta tiene una interpretación bonita: **es la diferencia entre lo que se pagó y lo que ya se cobró.** Es el capital que sigue "dentro" y no se ha realizado todavía.

Cuando el precio de mercado cae hasta ese nivel, significa que el mercado está valorando bitcoin exactamente en lo que queda del capital invertido no realizado. Por debajo de ahí, el mercado estaría cotizando por debajo de su propio residuo económico.

Empíricamente es el modelo de suelo que más ajustadamente ha tocado los mínimos: **en 2015, 2018 y 2022 el precio tocó el Balanced Price casi al día del mínimo absoluto.**

### Cómo leerlo

| Zona | Precio/Balanced | Qué significa |
|---|---|---|
| Techo | mayor a 3 | Muy lejos del suelo estructural. |
| Caro | 2 a 3 | Bull avanzado. |
| Neutral | 1.4 a 2 | Tendencia normal. |
| **Suelo** | **1.0 a 1.15** | **El precio toca el modelo. Zona de mínimo.** |
| Perforación | menor a 1.0 | Muy poco frecuente y muy breve. |

Lecturas en suelos: **0.95** en 2015, **1.00** en diciembre de 2018, **1.05** en marzo de 2020 y **1.02** en noviembre de 2022.

Note la consistencia: cuatro ciclos, todos entre 0.95 y 1.05. Es de los modelos de suelo más estables que existen, mejor que el CVDD en ese aspecto.

### Dónde ha fallado

> **Comparte insumos con el MVRV.** El precio realizado está en ambos, así que las dos señales no son independientes. Si les da mucho peso a los dos, está contando parte de la misma información dos veces.

> **El precio de transferencia es sensible a la definición de "transferencia".** Los movimientos internos de exchanges, las consolidaciones de UTXOs y las operaciones de custodia de ETFs pueden inflar artificialmente el volumen transferido. Cuando eso ocurre, el precio de transferencia sube, el Balanced Price baja, y el modelo señala un suelo más profundo del que corresponde. Distintos proveedores aplican filtros distintos.

> **Su historial exitoso es corto en observaciones.** Tres o cuatro toques limpios es un historial impresionante pero estadísticamente insuficiente para tratarlo como ley.

### Cómo usarlo en la práctica

Junto con el CVDD, define un **rango de suelo estructural**: el Balanced Price suele estar por encima del CVDD, así que entre ambos queda una banda. Históricamente el mínimo de ciclo se ha formado dentro de esa banda.

Es información valiosa para planificar, distinta de la que dan los osciladores. Los osciladores le dicen *cuándo*; estos modelos le dicen *dónde*.
