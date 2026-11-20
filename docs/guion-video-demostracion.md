# Guion del vídeo de demostración del Observatorio sísmico

**Duración objetivo:** 7 minutos (aprox. 6:30–7:30).  
**Objetivo:** recorrer la aplicación y explicar, con evidencias, extracción,
calidad, modelado, análisis y reflexión. El guion sigue la rúbrica del
enunciado y distingue la actividad actual del histórico reproducido.

## Antes de grabar

- Deja Docker Compose, la API y el túnel levantados; abre la URL definitiva
  del panel y comprueba que la salud de la API y los eventos cargan.
- Usa una ventana amplia del navegador y cierra pestañas, notificaciones y
  datos personales. Ten a mano la memoria de evaluación para mostrarla solo
  cuando se indiquen sus cifras.
- En **Exploración**, prepara un periodo que tenga resultados, una magnitud
  mínima (por ejemplo, 4) y, si carga el catálogo, un país que tenga eventos.
  Pulsa **Aplicar filtros** y verifica que mapa, tabla y ficha tienen datos.
  Apunta el periodo, país y resultados que realmente aparecen. No leas una
  cifra de ejemplo como si fuera el resultado de esta consulta.
- En **Análisis**, usa un periodo con baseline disponible y filtros coherentes.
  Comprueba que se muestran periodo y filtros efectivos, y que la comparación
  histórica indica cobertura disponible.
- En **Reproducción**, prepara un intervalo de 2025 con resultados. Comprueba
  que se ve la etiqueta **REPRODUCCIÓN**.
- Ten preparada la cifra histórica de la memoria: la lectura del 18-11-2026
  comparó 29 eventos de las últimas 24 horas, con magnitud mínima 4, con una
  media de 50,1425 eventos/día del baseline 2025. Preséntala como medición
  fechada, no como dato live actual.

## Recorrido y texto para narrar

### 0:00–0:35 | Presentación y pregunta que responde

**En pantalla:** abre **Resumen**. Deja visibles el estado de API, la última
ingesta, la consulta actual y el mapa.

**Di:**

> Este es el Observatorio de actividad sísmica. La aplicación sirve para
> consultar dónde se registran terremotos y analizar sus características, y
> comparar un periodo reciente con un histórico equivalente. No predice
> terremotos ni evalúa el riesgo. En este recorrido mostraré la consulta
> actual, cómo se aplican los filtros y qué conclusiones se pueden extraer
> sin perder de vista el periodo y la procedencia de los datos.

### 0:35–1:20 | Estado y recorrido del dato

**En pantalla:** señala el estado de la API, la última ingesta correcta y la
hora de lectura. Mientras sigues en Resumen, recorre visualmente el mapa y la
tabla.

**Di:**

> El flujo de datos empieza en USGS. Un productor consulta periódicamente el
> feed reciente y publica los eventos en Kafka. Un consumidor los valida,
> integra la información geográfica de Natural Earth y guarda los resultados
> en PostgreSQL. FastAPI ofrece los datos ya procesados y esta interfaz Angular
> los consulta; el panel no consulta USGS directamente.
>
> Aquí puedo distinguir que la API responde, cuándo se hizo la última ingesta
> y cuándo se leyó la respuesta. Si una consulta falla, la aplicación informa
> del problema y permite identificar si muestra una lectura anterior; no
> debería interpretarse como dato actualizado.

### 1:20–2:40 | Exploración, filtros, mapa y ficha

**En pantalla:** entra en **Exploración**. Muestra los filtros de inicio y fin
UTC, magnitud mínima y país. Lee en voz alta los filtros que preparaste y
púlsalos para que se vea el resultado. Señala el contexto de la consulta y
después el mapa.

**Di:**

> En Exploración puedo limitar el periodo con fechas UTC, fijar una magnitud
> mínima y seleccionar un país; si no indico periodo, la consulta usa las
> últimas 24 horas. Las fechas se interpretan con inicio incluido y fin
> excluido. Voy a aplicar [di tus filtros reales: periodo, magnitud y país o
> todos los países].
>
> El contexto confirma el periodo y los parámetros enviados. Los marcadores
> codifican la magnitud mediante el tamaño y la profundidad mediante el color;
> la leyenda explica esa codificación. Al seleccionar un punto, la ficha
> presenta lugar, hora, magnitud y su escala, profundidad, coordenadas, país
> y trazabilidad de la versión e ingesta.
>
> Si un dato no existe, se conserva como desconocido en vez de inventarlo. Un
> evento que no se asigna a un país permanece identificable como no asignado;
> puede ser, por ejemplo, un evento marítimo o una limitación de la cobertura
> geográfica.

**Acción:** haz clic en un punto y espera un segundo para que se lea la ficha.
Si el mapa indica resultados truncados, dilo: la tabla permite paginar el
conjunto consultado y el mapa puede representar solo una parte.

**Di, señalando la tabla:**

> La tabla es una alternativa al mapa y al color: permite recorrer páginas y
> consultar lugar, fecha UTC, magnitud, profundidad y país. Al seleccionar una
> fila también puedo inspeccionar el evento. Así no dependo exclusivamente de
> una representación visual para leer los datos.

### 2:40–3:10 | Calidad y modelado

**En pantalla:** mantén una ficha abierta y muestra brevemente la sección de
trazabilidad. Si tienes una diapositiva del flujo/modelo, úsala; evita abrir
archivos de código largos.

**Di:**

> En calidad se revisan completitud, unicidad, validez estructural y rangos,
> consistencia de tipos, ausencias y asignación geográfica. Las decisiones
> importantes son conservar magnitudes nulas y profundidades originales en
> lugar de sustituirlas por valores ficticios, y mantener los rechazos con su
> motivo en cuarentena.
>
> El modelo separa el estado actual del historial de versiones. La identidad
> de un evento y la fecha de revisión permiten guardar cambios sin que una
> versión antigua reemplace a una posterior. La escritura idempotente evita
> que un reintento duplique los efectos. También se conserva la procedencia
> para poder explicar de dónde sale cada registro.

### 3:10–4:35 | Análisis y conclusiones con contexto

**En pantalla:** abre **Análisis**. Deja visibles primero los filtros efectivos
y el periodo. Señala el recuento por hora UTC, el recuento por país, las
distribuciones de magnitud y profundidad y el bloque de comparación histórica.
Si hay tiempo, muestra la opción de consultar los valores de los gráficos en
tablas.

**Di:**

> La página de Análisis reutiliza los filtros y muestra el periodo y los
> filtros efectivos para que los gráficos se puedan interpretar. Aquí se
> resumen los eventos por hora UTC y por país, y se muestran distribuciones
> de magnitud y profundidad. Los valores ausentes se cuentan aparte: no se
> convierten en cero.
>
> La comparación histórica solo es válida si la cobertura del baseline está
> disponible y se mantienen filtros equivalentes. Como ejemplo documentado,
> no como lectura actual, el 18 de noviembre de 2026 se observaron 29 eventos
> en una ventana de 24 horas con magnitud mínima 4. El baseline de 2025 tenía
> 18.302 eventos en 365 días, es decir, una media de 50,1425 al día. Una sola
> ventana es variable y puede estar afectada por retrasos de publicación; esa
> diferencia describe esos periodos, pero no demuestra una tendencia ni
> permite predecir terremotos.
>
> Otra conclusión del perfil anual 2025 es que el 74,80 % de los eventos
> tenía profundidad inferior a 70 kilómetros. En una captura distinta del
> feed de un día, fue el 93,22 %. No son poblaciones equivalentes: comparar
> periodos distintos sin decirlo llevaría a una conclusión engañosa. Además,
> el conjunto anual no tuvo asignación de país para el 78,41 % de los eventos;
> por eso el sistema no oculta ni reasigna automáticamente esa categoría.

### 4:35–5:10 | Reproducción histórica aislada

**En pantalla:** entra en **Reproducción**. Señala la etiqueta, cambia o
confirma fechas y magnitud, pulsa **Consultar replay**, y muestra mapa, ficha o
tabla con un resultado.

**Di:**

> Además de la actividad actual, la aplicación ofrece una ruta de reproducción
> histórica. Aquí está marcada explícitamente como REPRODUCCIÓN: puedo
> consultar un periodo de 2025 y aplicar fechas y magnitud mínima, sin mezclar
> estos eventos con el modo live. Esta separación permite explorar el
> histórico de forma controlada y deja claro qué población estoy viendo.

### 5:10–6:20 | Reflexión: complejidad, rendimiento y límites

**En pantalla:** muestra brevemente la memoria de evaluación con las tablas de
mediciones; no leas toda la tabla. Si usas una diapositiva, resume los tres
datos destacados.

**Di:**

> Para reflexionar sobre rendimiento, se comparó una búsqueda lineal con una
> búsqueda en diccionario: la primera crece linealmente con el número de
> identificadores, mientras que el acceso promedio al diccionario es
> aproximadamente constante a cambio de memoria proporcional al tamaño.
> Para las consultas temporales de PostgreSQL se añadió un índice y se usa
> paginación.
>
> En una medición local sobre 18.302 eventos, la primera página de 100
> resultados tuvo una mediana de 104 milisegundos y un p95 de 143
> milisegundos; una página profunda fue más lenta, con una mediana de 198
> milisegundos, en parte por el coste de OFFSET. Son medidas secuenciales en
> un entorno local, no una prueba de concurrencia ni una garantía de
> rendimiento en producción.
>
> Para escalar, habría que probar con cargas mayores, agregar en base de
> datos, evitar conteos completos por página y evaluar paginación por cursor.
> La integración espacial y el cálculo de estadísticas también tendrían que
> optimizarse. Las cifras para 100 millones de registros de la memoria son
> proyecciones con supuestos, no un ensayo real a esa escala. Los costes de
> electricidad, desarrollo y nube también se presentan como estimaciones,
> porque no se midieron con vatímetro ni corresponden a facturas del proyecto.

### 6:20–6:50 | Cierre y mejoras pendientes

**En pantalla:** vuelve a Resumen. Termina con el estado del servicio y el
mapa.

**Di:**

> En resumen, el Observatorio conecta extracción, procesamiento, persistencia,
> consulta y análisis en una aplicación con filtros, mapa, tabla, trazabilidad
> y modo histórico separado. La memoria deja claras las conclusiones y sus
> límites. Como trabajo pendiente, falta completar la prueba de rendimiento
> de aceptación y la evaluación formal con diez participantes; no las presento
> como superadas. Gracias.

## Comprobación final

- El vídeo dura entre 5 y 8 minutos y se leen los filtros concretos que se
  aplicaron.
- Se ve al menos una ficha seleccionada, la leyenda del mapa, la tabla y la
  paginación.
- Se ven periodo y filtros efectivos en Análisis y la cobertura del baseline.
- Las cifras históricas se identifican como resultados fechados de la memoria,
  no como lectura en directo.
- Se explican las cinco dimensiones de la rúbrica y no se afirma que pruebas
  pendientes se hayan completado.
