## Qué mide

NUPL significa *Net Unrealized Profit/Loss*: **ganancia o pérdida no realizada neta**. Responde a: si todo el mercado cerrara posiciones hoy, ¿estaría en verde o en rojo, y por cuánto?

Es primo hermano del MVRV, pero expresado como fracción de la capitalización, lo que lo hace más intuitivo de leer.

## Cómo se calcula

```
NUPL = (Valor de mercado − Valor realizado) / Valor de mercado
```

El numerador es la ganancia total en papel de la red. Dividirlo por la capitalización lo normaliza a una escala entre −1 y +1:

- **NUPL = 0.5** → la mitad del valor de la red es ganancia no realizada.
- **NUPL = 0** → el mercado está exactamente en su costo base.
- **NUPL = −0.15** → la red entera está un 15% bajo el agua.

## Por qué funciona

Mide presión psicológica agregada. Cada punto de ganancia no realizada es un incentivo latente para vender; cada punto de pérdida es una razón para no hacerlo (nadie quiere materializar una pérdida).

Cuando el NUPL se vuelve negativo, ha ocurrido algo específico: **el tenedor promedio de bitcoin está perdiendo dinero**. Ese estado no es sostenible mucho tiempo. O los que quedan capitulan y venden, agotando la oferta, o aguantan y la oferta se congela. En ambos casos el resultado es el mismo: se acaban los vendedores.

### Cómo leerlo

Glassnode popularizó una división por zonas emocionales que vale la pena conocer porque la va a ver citada en todas partes:

| Zona | NUPL | Nombre habitual |
|---|---|---|
| Euforia | mayor a 0.75 | *Euphoria / Greed* |
| Codicia | 0.5 a 0.75 | *Belief / Denial* |
| Optimismo | 0.25 a 0.5 | *Optimism / Anxiety* |
| Esperanza | 0 a 0.25 | *Hope / Fear* |
| **Capitulación** | **menor a 0** | ***Capitulation*** |

Lecturas en los suelos: **−0.25** en enero de 2015, **−0.16** en diciembre de 2018, **−0.10** en marzo de 2020 y **−0.15** en noviembre de 2022.

Note que la magnitud del suelo se ha ido reduciendo con cada ciclo (−0.25 → −0.16 → −0.15). Tiene sentido: a medida que la base de tenedores madura y se institucionaliza, se necesita menos dolor para agotar a los vendedores. **No espere ver −0.25 otra vez**; si lo hace, probablemente se pierda el suelo.

### Dónde ha fallado

> **NUPL negativo no es un evento puntual, es un estado que dura meses.** En 2018 estuvo bajo cero desde noviembre hasta abril de 2019. Quien compró el primer día de señal se comió una caída adicional del 25%. Trátelo como una ventana de acumulación, no como un disparador de compra única.

> **La versión agregada esconde información.** El NUPL total puede ser positivo mientras los tenedores de corto plazo están masacrados. Por eso este panel también incluye las versiones por cohorte (STH-MVRV y LTH-MVRV): cuando las manos cortas ya capitularon pero las largas todavía no, el suelo suele estar más cerca de lo que sugiere el agregado.

### Cómo usarlo en la práctica

Su mayor virtud es que es **fácil de comunicar y difícil de manipular**. No depende de suposiciones de modelado ni de datos de exchanges: sale directo de la contabilidad de la cadena. Si sólo pudiera mirar dos indicadores para el suelo, este y el MVRV Z-Score serían una elección defendible.
