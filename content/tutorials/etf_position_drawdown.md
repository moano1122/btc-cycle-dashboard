## Qué mide

Cuánto se ha deshecho la **posición acumulada de los ETF spot** desde su máximo
histórico, en porcentaje.

Es el análogo, del lado de la demanda, a la caída del precio desde máximos. Si la
caída del precio mide cuánto ha sufrido el mercado, esta mide **cuánto ha
desmontado su posición el mayor comprador marginal**.

## Cómo se calcula

```
Posición neta = suma acumulada de los flujos diarios, convertidos a BTC al precio de cada día
Caída = (posición actual / máximo alcanzado − 1) × 100
```

Dos precisiones importantes sobre qué es y qué no es este número:

**No son las tenencias totales de los ETF.** GBTC llegó al mercado en enero de
2024 con un stack previo de cientos de miles de BTC que nunca aparece como
"flujo". Lo que mide esta serie es cuánto ha entrado o salido **desde el
lanzamiento**, que es precisamente lo que refleja el apetito institucional.

**Es una estimación, no el conteo del custodio.** Convertir cada flujo al precio
de su día no da exactamente las mismas monedas que contarían los custodios:
vender el mismo dinero a un precio más bajo libera más BTC. Sirve para la forma
de la curva y para medir la distancia al pico, que es lo que interesa.

## Por qué funciona

La lógica es de agotamiento del vendedor, igual que en los indicadores on-chain,
pero aplicada a un actor distinto.

Los flujos de ETF tienen inercia: los asesores financieros y las carteras
institucionales rebalancean despacio y en la misma dirección durante meses. Una
vez que empieza el desmontaje, tiende a continuar. Y cuando el desmontaje se
agota —cuando ya salió quien iba a salir— desaparece una fuente permanente de
oferta, igual que ocurre con la capitulación minera.

La diferencia es que aquí **no sabemos cuánto tiene que desmontarse** antes de
agotarse, porque nunca hemos visto un ciclo completo con ETFs.

### Cómo leerlo

| Zona | Caída desde el pico | Qué significa |
|---|---|---|
| En máximos | 0% a −5% | La posición institucional está intacta o creciendo. |
| Recorte | −5% a −12% | Rebalanceo normal. |
| **Desmontaje** | **−13% a −18%** | **Salida sostenida.** |
| **Extremo** | **menor a −18%** | **Lo más profundo registrado: −20.2% en julio de 2026.** |

**Contexto de agosto de 2026:** la caída es del **−17.5%**, en el percentil 5.5 de
su propia historia. Es decir, la posición de los ETF está más deshecha que en el
94% de los días desde que existen. El máximo se alcanzó el **9 de octubre de
2025**, el mismo momento que el techo del precio.

Este es el indicador de los ETF que sí está dando señal, frente al flujo de 30
días que está plano.

### Dónde falla

> **Cero suelos de ciclo.** Es la limitación de fondo y no tiene arreglo con más
> trabajo: los ETF spot existen desde enero de 2024. El rango completo de este
> indicador cubre dos años y medio, sin un solo suelo de mercado dentro. Decir
> que −17.5% es "extremo" solo significa extremo **dentro de esa ventana
> minúscula**. Un bear market completo podría llevar la posición a −40% y este
> indicador se habría saturado en 100 mucho antes, sin margen para avisar.

> **El arranque de 2024 hubo que descartarlo.** En las primeras semanas la
> posición acumulada era de unos pocos miles de BTC, así que una salida normal de
> GBTC producía caídas del 45% que no significaban nada. Ese artefacto llegó a
> fijar el anclaje de puntuación máxima antes de detectarlo. La serie ahora
> arranca en febrero de 2024, cuando la base superó los 100.000 BTC.

> **Mezcla convicción con arbitraje.** Una parte del desmontaje corresponde a
> operaciones de base entre contado y futuros que se cierran cuando el
> diferencial se comprime, no a inversores que pierden la fe.

### Cómo usarlo en la práctica

Léalo junto al **flujo neto de 30 días**, porque cuentan cosas distintas: éste
mide el daño acumulado, aquél la presión actual. La combinación que indicaría un
suelo sería una caída profunda de posición **acompañada de flujos que dejan de
ser negativos** — el equivalente institucional de que el aSOPR cruce de vuelta
por encima de 1.

Hoy tenemos la primera mitad de esa combinación pero no la segunda.
