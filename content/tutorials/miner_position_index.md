## Qué mide

El Miner Position Index (MPI) mide **cuánto BTC están enviando los mineros a los exchanges**, comparado con su propio promedio anual.

```
MPI = Salidas de mineros hacia exchanges / Media de 365 días de esas salidas
```

Es un Z-score, así que se lee en desviaciones respecto a la normalidad de los propios mineros:

- **MPI mayor a 2** → los mineros están vendiendo mucho más de lo habitual.
- **MPI cercano a 0** → ventas normales.
- **MPI menor a −1** → los mineros prácticamente dejaron de vender.

## Por qué funciona

Complementa al Puell Multiple desde el otro lado. El Puell mide **cuánto ganan** los mineros; el MPI mide **cuánto venden**. No es lo mismo, y la diferencia es informativa.

La secuencia típica de un final de bear market es:

1. El precio cae → el Puell se hunde (los mineros ganan poco).
2. Los mineros venden reservas para cubrir costos → **el MPI se dispara**.
3. Se agotan las reservas de los que iban a vender; los débiles quiebran o se apagan.
4. **El MPI cae a territorio negativo**: los que quedan ya no necesitan vender.

El paso 4 es la señal que interesa. Significa que **la presión vendedora estructural del mercado se agotó**. Los mineros son los únicos vendedores obligatorios; cuando ellos paran, desaparece una fuente permanente de oferta.

### Cómo leerlo

| Zona | MPI | Qué significa |
|---|---|---|
| Venta agresiva | mayor a 2 | Los mineros liquidan reservas. Presión vendedora. |
| Elevado | 0.5 a 2 | Ventas por encima de lo normal. |
| Normal | −0.5 a 0.5 | Operación rutinaria. |
| **Ventas agotadas** | **menor a −1** | **Los mineros dejaron de vender. Zona de suelo.** |

Lecturas en suelos: **−2.1** en diciembre de 2018, **−1.8** en marzo de 2020 y **−1.5** en noviembre de 2022.

### Dónde ha fallado

> **Depende de etiquetas de direcciones de mineros y de exchanges, dos capas de estimación encadenadas.** Los pools de minería cambian de direcciones, los mineros usan intermediarios OTC que no aparecen como exchanges, y los custodios institucionales complican aún más la atribución. La calidad del dato es de las peores del panel.

> **La venta OTC es invisible.** Los mineros grandes venden cada vez más por mesas de negociación extrabursátiles, que no dejan rastro de "salida hacia exchange". Un MPI bajo puede significar que dejaron de vender o simplemente que cambiaron de canal.

> **Los mineros públicos se cubren con derivados.** Muchos venden producción futura con contratos a plazo en vez de liquidar monedas. Eso desacopla completamente la presión vendedora real del flujo on-chain que el indicador observa.

### Cómo usarlo en la práctica

Es el indicador de menor peso del bloque de mineros, por la calidad del dato. Se refresca semanalmente para no gastar cupo de API.

Úselo únicamente como **tercera confirmación** dentro del bloque minero: Puell bajo 0.5 (no ganan) + Hash Ribbons bajo 1 (se apagan) + MPI negativo (no venden) describen una capitulación minera completa. Cualquiera de los tres por separado significa poco.
