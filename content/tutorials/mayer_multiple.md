## Qué mide

El Mayer Multiple, propuesto por Trace Mayer, es la versión de plazo medio del indicador anterior: **el precio dividido por su media móvil de 200 días.**

Donde la media de 200 semanas mide la posición dentro del ciclo completo, la de 200 días mide la posición dentro de la tendencia del último medio año. Es más rápido y más ruidoso.

## Cómo se calcula

```
Mayer Multiple = Precio de cierre / Media simple de 200 días
```

Se calcula localmente a partir de los cierres de Binance; no consume cupo de la API on-chain.

## Por qué funciona

La media de 200 días es probablemente la referencia técnica más observada de todos los mercados financieros. Eso le da una cualidad autocumplida: mucha gente compra cuando el precio la recupera y vende cuando la pierde, así que actúa como soporte y resistencia real.

En bitcoin además tiene una propiedad estadística útil: la distribución histórica del Mayer Multiple está fuertemente sesgada. La mediana histórica ronda **1.4**, y los valores por debajo de 0.8 representan una fracción pequeña de todos los días de la historia de bitcoin. Comprar en ese decil bajo ha tenido, históricamente, mejores retornos a 12 meses que comprar en cualquier otro.

### Cómo leerlo

| Zona | Mayer | Qué significa |
|---|---|---|
| Burbuja | mayor a 2.4 | El propio Mayer identificó este nivel como el punto donde el riesgo se dispara. |
| Caro | 1.5 a 2.4 | Bull en marcha. |
| Neutral | 1.0 a 1.5 | Tendencia normal. |
| **Barato** | **0.8 a 1.0** | **Por debajo de la tendencia semestral.** |
| **Extremo** | **menor a 0.8** | **Decil bajo histórico.** |

Lecturas en suelos: **0.55** en 2015, **0.62** en diciembre de 2018, **0.60** en marzo de 2020 y **0.70** en noviembre de 2022.

**Contexto de agosto de 2026:** el Mayer está en **0.93**. Por debajo de la media de 200 días, pero lejos del 0.6-0.7 de los suelos anteriores.

### Dónde ha fallado

> **Da muchas señales.** Es el indicador con más falsos positivos del panel. El Mayer Multiple ha bajado de 0.8 decenas de veces en la historia de bitcoin, y la mayoría no fueron suelos de ciclo sino correcciones dentro de tendencias mayores. Por eso su peso por defecto aquí es moderado.

> **No sabe nada de valoración.** Solo compara el precio consigo mismo. Si bitcoin cayera un 90% y se quedara plano un año, el Mayer volvería a 1.0 sin que nada fundamental hubiera mejorado. Los indicadores on-chain sí distinguen esa situación.

### Cómo usarlo en la práctica

Piénselo como un **medidor de sobreextensión de corto plazo dentro de una tesis ya formada por otros indicadores**. Si el MVRV Z-Score y el NUPL ya le dicen que está en zona de acumulación, el Mayer le ayuda a decidir si este mes concreto es un momento más o menos favorable para ejecutar una compra dentro de esa ventana.

Como señal independiente de suelo de ciclo, no es fiable.
