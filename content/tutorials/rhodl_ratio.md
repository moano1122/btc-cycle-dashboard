## Qué mide

RHODL Ratio, de Philip Swift, compara **el valor de las monedas movidas recientemente contra el de las movidas hace uno o dos años.**

```
RHODL = Banda RHODL de 1 semana / Banda RHODL de 1-2 años
```

Las "bandas RHODL" salen de las *Realized Cap HODL Waves*: la capitalización realizada desglosada según cuánto tiempo llevaba quieta cada moneda.

## Por qué funciona

Mide **rotación de manos**, que es la firma característica de las fases de un ciclo.

**En un techo**, entra una avalancha de compradores nuevos. La banda de 1 semana se infla porque hay muchísimo capital fresco moviéndose. El ratio se dispara.

**En un suelo**, casi nadie mueve monedas. La banda de una semana se seca mientras la de 1-2 años sigue engordando con las monedas que llevan ahí desde el ciclo anterior. El ratio se hunde.

En una frase: **el RHODL mide cuánta gente nueva está entrando en relación con cuánta gente lleva tiempo dentro.** Los techos son fiestas llenas de recién llegados; los suelos están vacíos.

### Cómo leerlo

Los valores absolutos son grandes y poco intuitivos (van de cientos a decenas de miles), así que lo importante es la posición dentro del rango histórico:

| Zona | RHODL | Qué significa |
|---|---|---|
| Techo | mayor a 20.000 | Avalancha de compradores nuevos. Marcó 2013, 2017 y 2021. |
| Caro | 5.000 a 20.000 | Bull avanzado. |
| Neutral | 1.500 a 5.000 | Tendencia normal. |
| **Suelo** | **menor a 1.000** | **Nadie está entrando. La oferta está congelada.** |

Lecturas aproximadas en suelos: **350** en 2015, **500** en diciembre de 2018, **900** en marzo de 2020 y **700** en noviembre de 2022.

### Dónde ha fallado

> **Tiene deriva estructural.** Igual que el Reserve Risk, el RHODL depende de cantidades acumuladas que crecen con el tiempo, así que los umbrales absolutos de un ciclo no se trasladan bien al siguiente. Los suelos han ido de 350 a 900. Léalo siempre en relación con su propio rango reciente, nunca contra un número fijo heredado de un artículo de 2019.

> **Es mucho mejor marcando techos que suelos.** Su reputación viene de haber señalado con claridad las cimas de 2013, 2017 y 2021. En los suelos su señal es más difusa: la parte baja del rango es amplia y el indicador puede quedarse ahí muchos meses.

> **Depende de la metodología de bandas del proveedor.** No hay un estándar sobre cómo se construyen las HODL waves de capitalización realizada, así que los valores no son comparables entre fuentes.

### Cómo usarlo en la práctica

En este panel tiene peso bajo y se refresca semanalmente, porque su aporte para detectar suelos es limitado y consume cupo de API.

Guárdelo para cuando el ciclo se dé la vuelta: **es de los mejores indicadores que existen para el problema opuesto**, decidir cuándo vender. Cuando llegue ese momento, suba su peso y active el modo de techo.
