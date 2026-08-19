## Qué mide

El MVRV en crudo, sin normalizar: **capitalización de mercado dividida por capitalización realizada.**

```
MVRV = Valor de mercado / Valor realizado
```

Es el mismo insumo del MVRV Z-Score, pero sin dividir por la desviación estándar. Eso lo hace más fácil de interpretar y menos comparable entre épocas.

## Cómo leerlo

La virtud de esta versión es que el número tiene un significado directo:

- **MVRV = 2.0** → el mercado vale el doble de lo que costó. El tenedor promedio duplicó su dinero.
- **MVRV = 1.0** → el mercado vale exactamente lo que costó. El tenedor promedio está en cero.
- **MVRV = 0.75** → el tenedor promedio pierde un 25%.

**El nivel 1.0 es la frontera importante**, y no hace falta ninguna estadística para entender por qué: por debajo de 1, el participante promedio de bitcoin está perdiendo dinero.

| Zona | MVRV | Qué significa |
|---|---|---|
| Techo | mayor a 3.5 | Solo visto en cimas de ciclo. |
| Caro | 2 a 3.5 | Bull avanzado. |
| Neutral | 1.2 a 2 | Tendencia normal. |
| **Bajo el costo** | **menor a 1** | **El mercado cotiza bajo su costo base.** |
| **Capitulación** | **menor a 0.8** | **Zona de suelo de ciclo.** |

Lecturas en suelos: **0.55** en 2015, **0.70** en diciembre de 2018, **0.83** en marzo de 2020 y **0.75** en noviembre de 2022.

## Por qué está aquí si ya tenemos el Z-Score

Por dos razones concretas:

**1. Es interpretable sin contexto.** Un Z-Score de −0.28 no le dice nada a nadie que no maneje estadística. "El bitcoinero promedio está perdiendo un 25%" se entiende de inmediato y se puede verificar contra la propia intuición.

**2. El Z-Score tiene un problema que este no tiene.** La desviación estándar del denominador se calcula sobre toda la historia disponible, y va cambiando a medida que pasa el tiempo. Eso significa que **el MVRV Z-Score de una fecha pasada puede cambiar de valor cuando se recalcula hoy**. El MVRV crudo no sufre de eso: el valor de noviembre de 2022 es el mismo hoy que entonces.

Cuando compare gráficos de MVRV Z-Score de distintas fuentes o de distintos años y no cuadren, esta es normalmente la razón.

### Dónde ha fallado

> **Está afectado por el mismo sesgo de monedas perdidas que el Z-Score.** El valor realizado incluye los 3-4 millones de BTC muertos con costo base cercano a cero, lo que infla el ratio de forma creciente con el tiempo. Los suelos han ido subiendo (0.55 → 0.70 → 0.75) en parte por esta razón, no solo por maduración del mercado.

> **Sin normalizar, los umbrales envejecen.** Un MVRV de 3.5 era territorio de techo en 2017; en ciclos más recientes el mercado ha hecho techo con lecturas bastante más bajas.

### Cómo usarlo en la práctica

Como **verificación de cordura del Z-Score**. Si el Z-Score dice suelo pero el MVRV crudo está en 1.4, algo no cuadra y conviene entender qué antes de actuar.

Su peso por defecto en este panel es bajo precisamente porque duplica información del Z-Score. Está aquí por su claridad interpretativa, no por su poder de señal.
