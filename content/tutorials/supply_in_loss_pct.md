## Qué mide

Qué **porcentaje de todas las monedas existentes** vale hoy menos de lo que costó.

Se calcula recorriendo el conjunto completo de UTXOs —las "monedas" individuales de la cadena—, comparando el precio del día en que se crearon con el precio actual, y contando cuántas están bajo el agua.

Es la medida más directa e intuitiva de dolor agregado que existe en on-chain. Sin fórmulas, sin normalizaciones: cuántos están perdiendo.

## Por qué funciona

Es el mismo argumento de agotamiento de vendedores, pero medido por conteo en vez de por valor.

Cuando más de la mitad de las monedas están en pérdida, ha ocurrido algo estructural: **la mayoría de participantes del mercado, sin importar cuándo entraron, están perdiendo dinero.** En ese punto, la gente que iba a vender por pánico ya vendió, y quien queda tiene una razón concreta para no hacerlo.

Tiene además una virtud metodológica: **no depende de promedios.** El MVRV y el NUPL trabajan con costos base promedio, que pueden estar sesgados por unos pocos actores muy grandes. Este indicador cuenta unidades, así que una ballena con posición enorme pesa distinto que en las métricas de valor. Ver los dos ángulos a la vez es más informativo que cualquiera de ellos solo.

### Cómo leerlo

| Zona | % en pérdida | Qué significa |
|---|---|---|
| Euforia | menor a 5% | Casi todo el mundo en ganancia. Techo de ciclo. |
| Alcista | 5% a 20% | Correcciones normales dentro de tendencia. |
| Corrección | 20% a 35% | Bear market temprano o corrección profunda. |
| **Estrés** | **35% a 50%** | **Bear market establecido.** |
| **Capitulación** | **mayor a 50%** | **Más de la mitad de la red bajo el agua. Zona de suelo.** |

Lecturas en suelos: **62%** en 2015, **55%** en diciembre de 2018, **52%** en marzo de 2020 y **51%** en noviembre de 2022.

Igual que con el NUPL, note la tendencia decreciente ciclo tras ciclo: 62% → 55% → 52% → 51%. **No espere volver a ver 60%.** El umbral efectivo se ha ido desplazando hacia abajo a medida que la base de tenedores madura.

### Dónde ha fallado

> **Las monedas perdidas nunca están en pérdida.** Los 3-4 millones de BTC con costo base cercano a cero que nadie puede mover están permanentemente contados como "en ganancia". Eso pone un techo estructural al indicador: matemáticamente nunca podrá acercarse al 100%, y cada año que pasa el sesgo crece porque se acumulan más monedas viejas con costo base bajo.

> **Cuenta UTXOs, no personas.** Un solo tenedor puede tener cien UTXOs y otro uno. La distribución de tamaños no es uniforme, así que "51% de la oferta" no significa "51% de los participantes".

> **Reacciona rápido y puede sobrepasar.** A diferencia del MVRV, este indicador salta con cada movimiento fuerte de precio. En caídas violentas puede tocar 50% durante unos días y retroceder sin que haya habido nada parecido a un suelo de ciclo. Mire la persistencia, no el pico.

### Cómo usarlo en la práctica

Su mejor uso es **comunicar magnitud**. Un MVRV Z-Score de −0.2 es abstracto; "más de la mitad de los bitcoins del mundo valen menos de lo que costaron" es concreto y difícil de malinterpretar.

Combínelo con el **% de LTH en pérdida** de este mismo panel. Que la oferta total esté en pérdida es común en bear markets; que las **manos largas** lo estén es lo raro, y es lo que distingue un bear market profundo de una corrección grande.
