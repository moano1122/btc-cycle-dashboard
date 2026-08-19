## Qué mide

Reserve Risk, creado por el analista Hans Hauge, intenta cuantificar algo que suena inasible: **la relación entre el precio y la convicción acumulada de quienes no venden.**

La idea de fondo: cada día que un tenedor de largo plazo decide *no* vender, está pagando un costo de oportunidad. Sumados a lo largo de años, esos costos de oportunidad forman una especie de "banco de convicción". Reserve Risk compara ese banco con el precio actual.

- **Reserve Risk bajo:** mucha convicción acumulada, precio barato. El riesgo asumido es pequeño frente a la recompensa potencial.
- **Reserve Risk alto:** poca convicción relativa, precio caro. Los veteranos están vendiendo y usted estaría comprándoles.

## Cómo se calcula

```
Reserve Risk = Precio / HODL Bank
```

Donde el **HODL Bank** es la suma acumulada de los *Coin Days Destroyed* ponderados por edad y valorados en dólares. En lenguaje llano: cada vez que una moneda vieja se mueve, "destruye" los días que llevaba acumulados; el HODL Bank mide el inventario de días no destruidos, es decir, la paciencia colectiva que sigue intacta.

El resultado es un número muy pequeño, típicamente entre 0.001 y 0.03. Por eso este panel lo muestra con cinco decimales.

## Por qué funciona

Combina dos señales en un solo número, y esa es su gracia:

1. **El numerador (precio)** sube en las burbujas.
2. **El denominador (convicción)** sube cuando los veteranos aguantan y baja cuando empiezan a mover monedas.

En un techo de ciclo las dos cosas empujan en la misma dirección: el precio está alto **y** los veteranos están vendiendo. El ratio se dispara.

En un suelo pasa lo contrario: el precio está por los suelos **y** nadie con monedas viejas las está moviendo. El ratio se hunde.

Es de los pocos indicadores que integra explícitamente la dimensión **tiempo**, no solo precio y volumen.

### Cómo leerlo

| Zona | Reserve Risk | Qué significa |
|---|---|---|
| Techo | mayor a 0.02 | Los veteranos están distribuyendo a precios altos. |
| Caro | 0.008 a 0.02 | Bull avanzado. |
| Neutral | 0.003 a 0.008 | Sin extremos. |
| **Suelo** | **menor a 0.002** | **Riesgo/recompensa históricamente favorable.** |

Lecturas en suelos: **0.0010** en 2015, **0.0015** en 2018, **0.0018** en marzo de 2020 y **0.0016** en noviembre de 2022.

### Dónde ha fallado

> **Tiene una deriva estructural a la baja.** El HODL Bank es una suma **acumulada**: solo crece con el tiempo. Eso significa que los valores de Reserve Risk de 2015 no son estrictamente comparables con los de 2026, y que el indicador tiende a marcar valores cada vez más bajos ciclo tras ciclo. Los umbrales absolutos envejecen mal. La forma correcta de leerlo es **relativa a su propio rango de los últimos años**, que es lo que hace la escala de este panel.

> **Es opaco.** A diferencia del MVRV, que se puede explicar en una frase, Reserve Risk depende de decisiones de modelado en la ponderación por edad que no están estandarizadas. Dos proveedores pueden publicar valores distintos para la misma fecha. No lo use como única fuente de verdad.

### Cómo usarlo en la práctica

Su valor está en que **no correlaciona perfectamente con los indicadores de valoración**. MVRV, NUPL y AVIV miran todos el costo base desde ángulos parecidos, así que se mueven juntos y confirmarse entre ellos aporta poco. Reserve Risk introduce la dimensión temporal, que es información genuinamente distinta.

Cuando MVRV Z-Score y Reserve Risk marcan suelo a la vez, la señal es más sólida que dos indicadores de valoración coincidiendo.
