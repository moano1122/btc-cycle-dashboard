## Qué mide

Hash Ribbons, creado por Charles Edwards, detecta **capitulación minera** comparando dos medias móviles del hashrate de la red:

- Media de **30 días** (rápida).
- Media de **60 días** (lenta).

Este panel muestra el ratio entre ambas:

```
Hash Ribbons = MA30 del hashrate / MA60 del hashrate
```

- **Ratio mayor a 1** → el hashrate está creciendo. Los mineros expanden.
- **Ratio menor a 1** → el hashrate está cayendo. **Los mineros están apagando máquinas.**

## Por qué funciona

El hashrate es una medida de capital físico desplegado. Nadie apaga una granja de minería por sentimiento: se apaga cuando el precio de la electricidad supera el ingreso por bloque, es decir, cuando minar destruye dinero.

Que la media de 30 días caiga por debajo de la de 60 significa que se está desconectando capacidad de forma sostenida, no por un apagón puntual ni por una tormenta en Texas. Es la firma de una **capitulación minera real**.

Y la capitulación minera importa por lo que viene después:

1. Los mineros débiles se apagan y **liquidan sus reservas** para pagar deudas → última ola de presión vendedora.
2. La dificultad se ajusta a la baja → los supervivientes ganan más por unidad de hashrate.
3. La minería vuelve a ser rentable → deja de haber ventas forzadas.
4. El hashrate se recupera → la MA30 vuelve a cruzar por encima de la MA60.

**El paso 4 es la señal de compra clásica de Hash Ribbons**, no el paso 1. El cruce a la baja marca el principio del dolor; el cruce al alza marca su final.

### Cómo leerlo

| Zona | Ratio | Qué significa |
|---|---|---|
| Expansión | mayor a 1.08 | Fuerte crecimiento del hashrate. |
| Normal | 1.0 a 1.08 | Crecimiento sano. |
| **Capitulación** | **menor a 1.0** | **Se está desconectando capacidad.** |
| **Capitulación profunda** | **menor a 0.95** | **Apagado masivo.** |

Lecturas en suelos: **0.93** en diciembre de 2018, **0.92** en marzo de 2020 y **0.95** en julio de 2022.

### Dónde ha fallado

> **Da señales que no son suelos de ciclo.** Hash Ribbons se activó en la prohibición de la minería en China (mayo-julio de 2021), que fue un evento regulatorio, no económico. Fue una señal de compra que técnicamente funcionó, pero por razones que nada tenían que ver con la tesis del indicador. También se activa tras cada halving, cuando la recompensa cae y los mineros marginales se apagan sin que el precio haya bajado.

> **Confunde causa y consecuencia.** El indicador supone que la capitulación minera provoca el suelo. Es igual de plausible que ambos sean consecuencia del mismo precio bajo. Esa distinción importa: si es lo segundo, el indicador no aporta información que el precio no tuviera ya.

> **La minería moderna se cubre con derivados.** Los mineros públicos hoy venden producción a plazo, tienen contratos de energía flexibles y acceso a crédito. Pueden aguantar caídas mucho más largas sin apagar, lo que retrasa o suprime la señal.

### Cómo usarlo en la práctica

Su peso por defecto aquí es moderado porque su tasa de falsos positivos es alta. Úselo **en conjunción con el Puell Multiple**: cuando el Puell está bajo 0.5 (los mineros no ganan dinero) **y** Hash Ribbons está bajo 1 (los mineros están apagando), la capitulación minera es real y no un artefacto del halving.

Cuando solo uno de los dos se activa, sospeche.
