## Qué mide

El MVRV Z-Score responde a una pregunta muy concreta: **¿cuánto se ha alejado el precio de mercado de lo que la gente realmente pagó por sus bitcoins?**

Hay dos formas de valorar toda la red:

- **Valor de mercado (Market Value):** todos los BTC en circulación multiplicados por el precio de hoy. Es lo que valdría la red si todo el mundo pudiera vender ahora mismo a precio actual.
- **Valor realizado (Realized Value):** cada BTC valorado al precio que tenía **el día en que se movió por última vez**. Es el costo base agregado de la red: cuánto dinero real hay dentro.

Cuando el valor de mercado se dispara muy por encima del realizado, hay mucha ganancia en papel y poca sustancia. Cuando cae por debajo, el mercado entero está comprando por menos de lo que costó.

## Cómo se calcula

```
MVRV Z-Score = (Valor de mercado − Valor realizado) / desviación estándar del valor de mercado
```

Los dos primeros términos dan la brecha en dólares. Dividir por la desviación estándar la convierte en un número comparable a través del tiempo: sin ese paso, una brecha de 10.000 millones significaría cosas distintas en 2013 y en 2026, porque la red creció tres órdenes de magnitud.

El resultado se lee como cualquier Z-score estadístico: **cuántas desviaciones estándar** se aleja el precio de su costo base.

## Por qué funciona

La lógica es de flujo de capital, no de gráficos. El valor realizado solo sube cuando alguien mueve monedas a un precio más alto, es decir, cuando entra dinero nuevo. Es una especie de suelo pegajoso: baja muy despacio, porque para bajarlo hay que vender en pérdida.

El precio de mercado, en cambio, es reflejo puro del último trade. Puede desplomarse en semanas.

Cuando el precio cae por debajo del costo base agregado, quien vende lo hace **realizando pérdidas reales**. Eso agota a los vendedores: los que quedan son los que no van a vender a ningún precio. Históricamente ese agotamiento es lo que forma el suelo.

### Cómo leerlo

| Zona | Lectura | Qué significa |
|---|---|---|
| Euforia | mayor a 7 | Techo de ciclo. Solo se ha visto en 2013, 2017 y 2021. |
| Caro | 3 a 7 | Bull avanzado. |
| Neutral | 1 a 3 | Mercado en tendencia sin extremos. |
| Valor | 0 a 1 | Por debajo de la media del ciclo. |
| **Suelo** | **menor a 0** | **El mercado cotiza bajo su costo base. Zona verde.** |

En noviembre de 2022, con BTC en unos 16.000 dólares, el Z-Score marcó **−0.286**. En el crash de covid de marzo de 2020 llegó a **−0.20**. En diciembre de 2018, alrededor de **−0.28**. En enero de 2015, cerca de **−0.40**.

Fíjese en el patrón: los suelos no ocurren en un número mágico único, sino en una **franja** entre −0.2 y −0.4. Por eso el sistema no usa un interruptor de encendido/apagado sino una escala continua.

### Dónde ha fallado

> **Este indicador es lento y llega tarde a los techos.** Marcó bien todos los suelos, pero en el ciclo 2024-2025 nunca alcanzó los extremos de euforia de ciclos anteriores antes de la caída de octubre de 2025. La entrada de los ETFs spot cambió quién compra y cómo: los flujos institucionales mueven precio sin mover monedas on-chain al mismo ritmo, lo que comprime el indicador.

> **El valor realizado sobreestima el costo base real.** Aproximadamente entre 3 y 4 millones de BTC están perdidos para siempre (llaves extraviadas, monedas de Satoshi). Esas monedas siguen contando en el cálculo con un costo base cercano a cero, lo que empuja el valor realizado hacia abajo y el ratio hacia arriba. El indicador **AVIV Z-Score** de este mismo panel corrige justamente ese sesgo, y por eso vale la pena mirarlos juntos.

### Cómo usarlo en la práctica

Sirve para **calibrar el tamaño de sus compras, no para elegir el día exacto**. En 2022 el Z-Score estuvo bajo cero durante unos cuatro meses, y el precio se movió en un rango del 30% dentro de esa ventana. Nadie compra el mínimo exacto. Lo que este indicador le dice es cuándo está usted dentro de la ventana donde comprar ha sido históricamente favorable.
