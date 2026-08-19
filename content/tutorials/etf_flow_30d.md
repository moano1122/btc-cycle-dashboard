## Qué mide

El dinero neto que entró o salió de los **ETF spot de bitcoin** en los últimos 30
días, en millones de dólares.

```
Flujo neto 30d = suma de los flujos diarios de los últimos 30 días
```

Positivo significa que los ETF compraron más BTC del que vendieron. Negativo, lo
contrario.

## Por qué este indicador es distinto a todos los demás del panel

Todo el resto del catálogo mira **dentro de la cadena**: qué monedas se mueven,
a qué costo se compraron, quién está en pérdida. Es un enfoque potente, pero
tiene un punto ciego enorme desde enero de 2024.

Cuando usted compra un ETF spot, no aparece en la cadena. Compra una
participación en un fondo; el fondo encarga la compra a un participante
autorizado; ese participante consigue los bitcoins en mesas OTC o de inventario
propio, y los deposita en un custodio. **El precio se mueve, y las métricas
on-chain apenas se enteran.**

Ese punto ciego tuvo una consecuencia concreta y cara: en el techo de octubre de
2025, con BTC sobre 126.000 dólares, ningún indicador on-chain mayor dio señal
limpia de venta antes de la caída del 52% que siguió.

## Lo que dicen los datos

La posición acumulada de los ETF hizo su **máximo el 9 de octubre de 2025**,
prácticamente el mismo día que el precio. Desde entonces se ha deshecho de forma
sostenida.

Pero conviene mirar el detalle antes de sacar conclusiones cómodas, porque hay un
matiz que cambia cómo usar este indicador:

| Mes | Flujo neto |
|---|---|
| Septiembre 2025 | +3.511 M |
| **Octubre 2025** (techo del precio) | **+3.425 M** |
| Noviembre 2025 | −3.467 M |
| Diciembre 2025 | −1.092 M |

**Octubre cerró todavía en positivo.** El flujo mensual no anticipó el techo: se
dio la vuelta *después*, en noviembre. Lo que sí coincidió al día fue el pico de
la posición acumulada.

La lectura honesta es que este indicador **confirma giros en semanas, no los
anticipa**. Sigue siendo valioso —confirmar en semanas es mucho mejor que no
enterarse— pero no espere que le avise antes de tiempo.

### Cómo leerlo

| Zona | Flujo 30d | Qué significa |
|---|---|---|
| Demanda fuerte | mayor a +9.000 M | Entrada institucional masiva. Se vio en diciembre de 2024. |
| Demanda sana | +2.000 a +9.000 M | Acumulación normal. |
| Neutral | −800 a +2.000 M | Sin dirección clara. |
| **Salidas** | **−4.000 a −800 M** | **El bid institucional se retira.** |
| **Capitulación** | **menor a −4.000 M** | **Salidas extremas. Peor racha: −7.249 M en junio de 2026.** |

**Contexto de agosto de 2026:** el flujo de 30 días está en **+781 M**. Ligeramente
positivo, en el percentil 35 de su historia. Ni capitulación institucional ni
demanda renovada: los ETF están, básicamente, quietos.

Ese dato es un contrapeso importante frente a los indicadores on-chain de dolor
—el % de manos largas en pérdida está en máximos—. Si el suelo de este ciclo va
a formarse, cuesta imaginar que ocurra sin que el mayor comprador marginal del
mercado haga algo.

### Dónde falla

> **No tiene ningún suelo de ciclo con el que calibrarse.** Los ETF spot nacieron
> en enero de 2024. No existían en 2015, 2018 ni 2022, así que no hay un solo
> precedente de cómo se comporta este indicador en un suelo de mercado. Sus
> umbrales salen de la distribución de sus dos años y medio de vida y **nada
> más**. El panel lo marca como "sin respaldo" por eso.

> **Confirma, no anticipa.** Como muestra la tabla de arriba, el flujo mensual
> seguía positivo el mes del techo. Trátelo como validación de un giro que otros
> indicadores ya sugieren, no como disparador.

> **Mide dólares, no convicción.** Buena parte del flujo de los ETF es actividad
> de arbitraje entre el contado y los futuros —la llamada *basis trade*—, no
> apuesta direccional. Una salida grande puede reflejar simplemente que el
> diferencial de futuros se comprimió y el arbitraje dejó de ser rentable.

> **Solo cubre los ETF de Estados Unidos.** No incluye productos europeos,
> canadienses ni asiáticos, ni las tenencias de tesoros corporativos.

### Cómo usarlo en la práctica

Su valor es que mide algo que **ningún otro indicador del panel puede ver**. Los
on-chain le dicen qué hacen las monedas; este le dice qué hace el dinero
institucional.

La combinación más informativa es la **divergencia**: si el on-chain grita suelo
pero los ETF siguen sangrando, la caída probablemente no ha terminado. Y al
revés: cuando el flujo se dé la vuelta a positivo de forma sostenida después de
meses de salidas, será una de las confirmaciones más sólidas de que el ciclo giró.
