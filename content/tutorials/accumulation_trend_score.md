## Qué mide

Casi todos los indicadores de este panel miran la **oferta**: quién está en pérdida, quién está vendiendo, cuánto duele. El Accumulation Trend Score es de los pocos que mira la **demanda**: ¿están las carteras grandes comprando o vendiendo?

Devuelve un número entre 0 y 1:

- **Cerca de 1** → acumulación fuerte y generalizada.
- **Cerca de 0** → distribución fuerte.
- **Alrededor de 0.5** → sin tendencia clara.

## Cómo se calcula

Combina dos cosas:

1. **El cambio de saldo** de cada entidad on-chain en el último mes.
2. **El tamaño** de esa entidad, como ponderación.

Es decir: que una cartera de 10.000 BTC aumente su posición pesa mucho más que la misma variación porcentual en una de 0.5 BTC. El resultado se normaliza a la escala 0-1.

Un detalle importante: usa **entidades**, no direcciones. Los proveedores aplican heurísticas de agrupación para juntar las múltiples direcciones que controla un mismo actor. Eso mejora mucho la señal, pero también introduce una capa de estimación que no existe en indicadores puramente contables como el SOPR.

## Por qué funciona

En los suelos de ciclo se observa un patrón consistente: **mientras el precio hace mínimos, las carteras grandes acumulan.** Es la transferencia de manos débiles a manos fuertes, medida directamente en vez de inferida.

Y funciona al revés en los techos: cerca de las cimas, las entidades grandes distribuyen a los compradores minoristas que llegan tarde. El indicador cae hacia 0 mientras el precio sube, una divergencia que ha sido una señal de aviso útil.

### Cómo leerlo

| Zona | Score | Qué significa |
|---|---|---|
| Distribución fuerte | menor a 0.2 | Las carteras grandes están vendiendo. |
| Distribución | 0.2 a 0.4 | Salida neta. |
| Neutral | 0.4 a 0.6 | Sin tendencia. |
| Acumulación | 0.6 a 0.8 | Entrada neta. |
| **Acumulación fuerte** | **mayor a 0.8** | **Compra generalizada de carteras grandes.** |

Lecturas en suelos: **0.85** en diciembre de 2018, **0.90** en marzo de 2020 y **0.88** en noviembre de 2022.

### Dónde ha fallado

> **La agrupación de entidades es una estimación, no un hecho.** Las heurísticas que juntan direcciones bajo una misma entidad se equivocan, y se equivocan más ahora que hay custodios institucionales enormes. Una redistribución interna de un ETF puede leerse como acumulación o distribución masiva según cómo la clasifique el proveedor.

> **No distingue compra de custodia.** Cuando un ETF recibe monedas de un creador autorizado, aparece como acumulación de una entidad gigante. Puede que detrás haya demanda real, o puede que sea una simple reorganización operativa.

> **Es de reacción rápida y da muchas señales.** Su ventana es de un mes, así que oscila bastante. Aparece en zona de acumulación varias veces por ciclo sin que sean suelos.

### Cómo usarlo en la práctica

Su valor está en la **independencia**: mide algo que ningún otro indicador del panel mide. Los de valoración le dicen que el precio está barato; este le dice si además hay alguien comprando.

La combinación más interesante es la **divergencia**: precio haciendo mínimos nuevos mientras el Accumulation Trend Score sube hacia 0.8. Eso significa que las manos fuertes están absorbiendo la oferta que sueltan las débiles, que es literalmente lo que ocurre en un suelo.
