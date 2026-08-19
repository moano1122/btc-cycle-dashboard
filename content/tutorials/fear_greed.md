## Qué mide

El índice de Miedo y Codicia es un compuesto de sentimiento del mercado en escala 0-100, donde 0 es miedo extremo y 100 codicia extrema.

Combina varios ingredientes con pesos aproximados: volatilidad, momentum y volumen de mercado, actividad en redes sociales, dominancia de bitcoin y tendencias de búsqueda.

## De dónde sale el dato

De **alternative.me**, que es quien publica el índice, mediante su API abierta y
sin autenticación. La serie llega hasta el 1 de febrero de 2018, que es cuando
empezó a calcularse.

Antes este indicador se pedía al proveedor on-chain de pago, lo que tenía dos
inconvenientes: consumía uno de los 15 huecos diarios del cupo gratuito para un
dato que es público, y solo daba cuatro años de historia. Traerlo de la fuente
original libera ese hueco para una métrica irremplazable y permite calibrarlo
contra dos suelos de ciclo en vez de ninguno.

## Por qué está aquí

Por una única razón: **es el indicador que mejor comunica el ambiente del mercado a un ser humano.** Un MVRV Z-Score de −0.2 es abstracto; un "miedo extremo: 12" describe algo que usted puede contrastar con lo que ve en las redes y en las noticias.

Esa capacidad de contrastar tiene valor práctico. Si el panel dice zona de suelo pero el ambiente general es de optimismo, algo no encaja y merece una segunda mirada.

### Cómo leerlo

| Zona | Índice | Qué significa |
|---|---|---|
| Codicia extrema | 75 a 100 | Euforia. Históricamente mal momento para comprar. |
| Codicia | 55 a 75 | Optimismo. |
| Neutral | 40 a 55 | Sin sesgo. |
| Miedo | 15 a 40 | Pesimismo. |
| **Pánico** | **menor a 10** | **Es donde han estado los suelos de verdad.** |

Lecturas reales en los suelos, medidas sobre la serie completa desde 2018:

| Suelo | Mínimo del índice | Fecha |
|---|---|---|
| Bear 2018 | **9** | 25 nov 2018 |
| Covid 2020 | 8 | 14 mar 2020 |
| Bear 2022 | **6** | 18 jun 2022 |

Fíjese en la fecha del suelo de 2022: **18 de junio**, la capitulación de LUNA y
Three Arrows Capital. El mínimo del precio llegó cinco meses después, en
noviembre. El sentimiento tocó fondo mucho antes que el precio, lo cual es un
recordatorio útil de que estos indicadores no marcan el mismo día.

**Contexto de agosto de 2026:** el dato crudo de hoy es **46** y la media de 7
días —que es la que muestra la tarjeta, porque el valor diario salta demasiado—
está en **35**.

La etiqueta que pone alternative.me a esa lectura es *"Fear"*, y ahí está la
trampa: 46 cae en el **percentil 52** de toda la historia del índice. Es
sentimiento exactamente mediano. No hay nada parecido al pánico de 6-9 que
acompañó a los suelos reales.

### Dónde ha fallado

> **Es el indicador más débil del panel y su peso lo refleja.** El miedo extremo aparece en todos los suelos de ciclo, pero también aparece en cada corrección intermedia del 25%. Ha marcado "miedo extremo" decenas de veces; solo tres o cuatro fueron suelos de ciclo. Su tasa de falsos positivos es altísima.

> **Es reflexivo, no predictivo.** Mide cómo se siente el mercado *ahora*, y esa sensación es en buena medida consecuencia del precio reciente. Es casi un derivado del precio con pasos extra, no una fuente de información independiente.

> **Su metodología es opaca y ha cambiado.** Los pesos exactos de cada componente no están completamente documentados y se han ajustado con el tiempo. Las lecturas de 2018 y las de 2026 no son estrictamente comparables.

> **Las etiquetas de texto son más laxas que la historia.** El índice llama "Fear" a cualquier lectura por debajo de 45, pero los suelos de ciclo se formaron en 6-9. Guiarse por la palabra en vez de por el número lleva a creer que hay pánico cuando solo hay pesimismo corriente. Los umbrales de este panel usan la mediana de los mínimos reales de 2018 y 2022, no las etiquetas.

> **La componente de redes sociales se ha vuelto ruido.** El volumen de bots, contenido automatizado y engagement artificial en las plataformas donde se mide el sentimiento ha crecido mucho, degradando la señal.

### Cómo usarlo en la práctica

Como **verificación de coherencia**, nunca como señal. Su peso por defecto aquí es el más bajo de todo el catálogo.

La forma correcta de usarlo es al revés de como suele plantearse: no "hay miedo extremo, luego compro", sino **"el panel dice zona de suelo, ¿el ambiente del mercado es coherente con eso?"**. Si el score agregado está en 80 y el Fear & Greed en 65, desconfíe del score: los suelos de ciclo no se forman con la gente optimista.
