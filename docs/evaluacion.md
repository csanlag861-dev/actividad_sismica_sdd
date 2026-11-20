Evaluación como profesor
Nota global: 8,9 / 10 — Notable alto / sobresaliente limitado (provisional)
La nota se basa en los descriptores del apartado 13 y en las evidencias disponibles. El alumno confirma que Netlify, Docker y ngrok ya se han probado; se recoge esa validación como declaración del alumno, no como una comprobación independiente. Siguen sin ejecutarse SC-002 y la evaluación formal de diez participantes exigida por SC-003/SC-006.

Criterio	Nota	Nivel
Extracción	9,5	Sobresaliente
Calidad	9,0	Sobresaliente
Modelado	9,0	Sobresaliente
Análisis	8,5	Notable alto
Reflexión	8,5	Notable alto
Promedio	8,9	Notable alto
1. Extracción — 9,5 / 10
Por qué sobresaliente

Existen los cinco servicios obligatorios en compose.yaml.
Está implementado el flujo USGS → productor → Kafka → consumidor → PostgreSQL → API.
Se cargaron datos históricos reales de 2025: 18.302 eventos.
Se procesó una captura live real de 177 eventos.
Se conservan tipos, unidades, procedencia, frecuencia y archivos originales.
La carga histórica se divide en intervalos mensuales y se detectan inconsistencias mediante el ledger.
La reproducción está separada mediante el modo replay.
Las instrucciones de extracción y reproducción están disponibles en README.md.
Qué impide el 10

El despliegue se considera realizado según lo informado por el alumno. Cuando ngrok cae, la aplicación muestra un error de conexión con la API. No se documenta un reintento automático al recuperar el túnel, ni se repitió independientemente esta validación.
2. Calidad — 9,0 / 10
Por qué sobresaliente

La memoria evalúa explícitamente más de cuatro dimensiones:

Completitud.
Unicidad.
Validez.
Consistencia.
Países asignados.
Rangos de coordenadas y profundidad.
Ausencias y cuarentena.
Limitaciones de exactitud física.
Está bien documentada la diferencia entre resultados reales y sintéticos en
[memoria-proyecto.md](../memoria-proyecto.md). Además, las decisiones
son sensatas:

Mantener magnitudes nulas en lugar de sustituirlas por cero.
Mantener el estado «sin país asignado».
No corregir profundidades negativas sin una referencia independiente.
Conservar rechazos en cuarentena.
Qué falta

No aparece un antes/después de una limpieza real sobre problemas existentes, aunque esto es coherente porque el conjunto aceptado no contiene esos defectos.
La exactitud física no puede verificarse con una fuente independiente.
Varias pruebas controladas siguen sin registrarse con evidencias observadas, como coordenadas inválidas o revisiones antiguas.
La rúbrica no exige inventar incidencias, así que estas limitaciones no penalizan mucho, pero sí impiden afirmar un 10 absoluto.

3. Modelado — 9,0 / 10
Por qué sobresaliente

El esquema distingue correctamente:

event_current: estado actual.
event_version: historial de revisiones.
ingestion_run: ejecución y procedencia.
quarantine: rechazos.
country y calendar_date: dimensiones.
Separación live / replay.
La implementación incluye:

Claves compuestas.
Restricciones de rango.
Identidad de versión.
Claves foráneas.
Integración geográfica con Natural Earth.
Actualización solo si la revisión es posterior.
Escritura idempotente.
Confirmación posterior del offset.
Índice temporal específico en la migración 0007.
El modelo físico está plasmado en 0001_initial_schema.py.

Qué falta

La justificación del índice podría ser más completa si incluyese un EXPLAIN/ANALYZE comparativo con y sin índice sobre datos representativos.
Falta una evidencia visual inequívoca del modelo conceptual, aunque el esquema y sus relaciones están bien explicados textualmente.
4. Análisis — 9,0 / 10
Por qué sobresaliente

Hay resultados y filtros identificables:

Baseline anual de 18.302 eventos.
Comparación con una ventana móvil de 24 horas.
Distribución por profundidad.
Distribución por tipo de magnitud.
Porcentaje de asignación geográfica.
Comparación entre el histórico anual y el feed live.
Cuatro conclusiones fundamentadas.
Las conclusiones indican correctamente el periodo, la población y las limitaciones. También evitan interpretar la ventana de un día como una tendencia futura.

Qué falta

Las tres conclusiones mínimas están ampliamente cubiertas, pero faltan algunos resultados visuales finales con capturas de los filtros aplicados.
La comparación de 29 frente a 50,1425 eventos/día es útil, aunque no debe utilizarse sin advertir la variabilidad de una sola ventana.
No se ha ejecutado una prueba visual completa de todos los gráficos en otro navegador o dispositivo.

Como corrección puntual, se confirmó que la API sí incluía Estados Unidos y que el límite estaba en la presentación del gráfico de países. Ahora se ordena por recuento, se dimensiona según el número de categorías y ofrece desplazamiento; una comprobación visual con datos de muestra mostró Estados Unidos al inicio. Esto corrige el defecto reportado, aunque no sustituye una validación con el conjunto completo de la instancia publicada.
5. Reflexión — 8,5 / 10
Por qué notable alto, acercándose a sobresaliente

La reflexión incluye:

Complejidad lineal frente a búsqueda por diccionario.
Tres tamaños de entrada.
Memoria, pico de memoria y mediana temporal.
Complejidad de búsqueda, integración geográfica y agregación.
Retención de datos.
Medición de página PostgreSQL y latencias p50/p95 del API con el conjunto real de 18.302 eventos.
Comparación diagnóstica de planes indexado/secuencial y límites de dicha medición.
Proyección de almacenamiento y throughput para 100 millones, con riesgos de memoria, agregación, índice y geoprocesamiento.
Estimaciones de electricidad, esfuerzo de desarrollo, mantenimiento y una infraestructura futura, separando supuestos de datos medidos.

Qué sigue impidiendo el sobresaliente completo

No hay medición directa con vatímetro, factura de proveedor ni registro de las horas históricas de desarrollo; los costes monetarios son escenarios hipotéticos transparentes, no gastos comprobados.
La proyección a 100 millones es una extrapolación dimensional desde 18.302 registros, no una prueba real de carga.
La medición de API es local, secuencial y no incluye renderizado ni concurrencia; SC-002 y la evaluación humana formal no están ejecutados. El alumno informa de una prueba informal con una persona, que encontró intuitiva la aplicación, pero no es evidencia suficiente para SC-003/SC-006.

La reflexión mejora materialmente y deja de depender solo de un microbenchmark sintético: aporta medidas de la base/API, números de escalado y supuestos de coste. Se mantiene provisional mientras no se ejecuten las pruebas de rendimiento y aceptación pendientes.

Falta principal antes de la defensa
Para asegurar la máxima calificación, conviene completar y registrar:

Evidencias de duplicado, revisión posterior y versión antigua.
Evidencia de magnitud nula y coordenadas inválidas.
Capturas finales del panel con filtros y resultados.
Prueba de rendimiento con la fixture definida.
Evaluación formal de diez participantes, si se pretende declarar superados SC-003/SC-006. La prueba informal de una persona puede citarse como impresión exploratoria, pero no sustituye este requisito.
Explicación individual oral del flujo y una decisión técnica propia.
Conclusión del profesor
Es un proyecto técnicamente sólido y muy bien documentado. Los datos reales, el pipeline, el versionado, el modelo, la calidad y las conclusiones justifican una calificación alta. La nota se reduce principalmente por la ausencia de pruebas de rendimiento y aceptación formal, y por no disponer de mediciones de costes reales, no por una ausencia grave en los criterios centrales. El despliegue se considera probado según la información del alumno.

La nota se mantiene en 8,9/10. Podría mejorar tras completar las pruebas de rendimiento y aceptación restantes, pero no se anticipa una nota de 9,5–10 sin esas evidencias.