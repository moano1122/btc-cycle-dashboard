## Qué mide

El Puell Multiple mira el mercado desde el lado de la **oferta forzada**: los mineros.

Los mineros son los únicos vendedores estructurales de bitcoin. Producen monedas nuevas todos los días y tienen costos en moneda fiat —electricidad, hardware, nómina— que deben pagar sí o sí. Cuando su ingreso cae por debajo de sus costos, no tienen alternativa: venden reservas, apagan máquinas, o quiebran.

Ese momento de dolor máximo de los mineros ha coincidido con el suelo de todos los ciclos.

## Cómo se calcula

```
Puell Multiple = Ingreso diario de los mineros en USD / Media de 365 días de ese ingreso
```

El ingreso diario es la emisión de BTC del día multiplicada por el precio. La media anual sirve de referencia de "normalidad" para ese mismo minero.

Un valor de **1.0** significa que hoy los mineros ganan exactamente su promedio del último año. **0.4** significa que ganan un 60% menos de lo normal.

## Por qué funciona

Aquí hay una mecánica económica real, no una correlación estadística:

1. El precio cae → el ingreso de los mineros cae en la misma proporción.
2. Los mineros menos eficientes empiezan a perder dinero en cada bloque.
3. Para cubrir costos venden sus reservas → **más presión vendedora justo cuando el mercado ya está débil**.
4. Los que no aguantan apagan las máquinas → cae el hashrate → sube la dificultad relativa para los que quedan → los supervivientes ganan más por unidad de hashrate.
5. La presión vendedora se agota porque ya no queda quién venda.

El paso 5 es el suelo. El Puell Multiple detecta la fase 3-4.

Un detalle importante: el halving reinicia este ciclo artificialmente. Cuando la recompensa se corta a la mitad, el ingreso cae un 50% de golpe y el Puell se desploma sin que el precio haya bajado. **Después de cada halving hay que leer el indicador con cautela durante unos meses.**

### Cómo leerlo

| Zona | Puell | Qué significa |
|---|---|---|
| Techo | mayor a 4 | Los mineros ganan cuatro veces lo normal. Ha marcado techos de ciclo. |
| Caro | 1.5 a 4 | Minería muy rentable. |
| Neutral | 0.8 a 1.5 | Condiciones normales. |
| **Capitulación** | **menor a 0.5** | **Zona de suelo de ciclo.** |

Lecturas en suelos: **0.30** en enero de 2015, **0.31** en diciembre de 2018, **0.39** en marzo de 2020 y **0.36** en noviembre de 2022.

Es notable la consistencia: cuatro ciclos, cuatro lecturas entre 0.30 y 0.39. Pocos indicadores on-chain tienen ese grado de repetibilidad, y es la razón de su peso alto en este panel.

### Dónde ha fallado

> **El halving de abril de 2024 distorsionó la lectura durante casi un año.** El Puell cayó bajo 0.5 en el verano de 2024 sin que hubiera nada parecido a un suelo de ciclo: simplemente la recompensa se había reducido a la mitad. Fue una señal falsa de manual. Combínelo siempre con al menos un indicador de valoración (MVRV Z-Score) antes de darle peso.

> **La economía minera se profesionalizó.** Los mineros públicos de hoy tienen acceso a deuda, coberturas con derivados y contratos de energía a plazo. Pueden aguantar mucho más tiempo sin vender que los mineros de 2015, lo que puede hacer que el indicador toque zona de suelo antes de que la capitulación real ocurra.

### Cómo usarlo en la práctica

Es un indicador de **confirmación de fase**, no de timing fino. Su mensaje es "el productor marginal está sangrando", que es una condición necesaria pero no suficiente para el suelo. Mírelo junto con Hash Ribbons: cuando el Puell está bajo 0.5 **y** el hashrate ya dejó de caer, la capitulación minera está terminando.
