Evaluación como profesor
Nota global: 8,8 / 10 — Notable alto / sobresaliente limitado
La nota se basa exclusivamente en los descriptores del apartado 13 y en las evidencias comprobables del repositorio. No sería prudente conceder un 10 completo mientras algunas entregas críticas siguen pendientes de ejecución pública.

Criterio	Nota	Nivel
Extracción	9,5	Sobresaliente
Calidad	9,0	Sobresaliente
Modelado	9,0	Sobresaliente
Análisis	9,0	Sobresaliente
Reflexión	7,5	Notable
Promedio	8,8	Notable alto
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

No se ha publicado una URL real de Netlify ni abierto un túnel ngrok público.
La extracción live no tiene una demostración pública registrada en la memoria.
Falta una ejecución observable por un tercero de las pruebas de cierre y reapertura del túnel.
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
Está bien documentada la diferencia entre resultados reales y sintéticos en memoria-evaluacion.md. Además, las decisiones son sensatas:

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
5. Reflexión — 7,5 / 10
Por qué notable

La reflexión incluye:

Complejidad lineal frente a búsqueda por diccionario.
Tres tamaños de entrada.
Memoria, pico de memoria y mediana temporal.
Limitaciones de PostgreSQL, Kafka y 100 millones de registros.
Retención de datos.
Propuestas de particionado, índices y escalado.
Costes cualitativos de hardware, almacenamiento, mantenimiento y desarrollo.
Qué impide sobresaliente

No se mide la mayoría de los costes reales: electricidad, almacenamiento y desarrollo.
No hay una estimación con supuestos identificados de una infraestructura futura.
El benchmark es sintético y no mide consultas reales de PostgreSQL ni API.
No se razonan numéricamente las consecuencias de 100 millones de registros.
Los pendientes de despliegue, usabilidad y rendimiento se reconocen, pero no se han resuelto.
Esta parte se queda claramente en Notable, aunque casi alcanza Sobresaliente.

Falta principal antes de la defensa
Para asegurar la máxima calificación, conviene completar y registrar:

Despliegue público con Netlify y ngrok.
Evidencias reales de cerrar y volver a abrir el túnel.
Evidencias de duplicado, revisión posterior y versión antigua.
Evidencia de magnitud nula y coordenadas inválidas.
Capturas finales del panel con filtros y resultados.
Prueba de rendimiento con la fixture definida.
Evaluación de diez participantes, si es posible dentro del alcance.
Explicación individual oral del flujo y una decisión técnica propia.
Conclusión del profesor
Es un proyecto técnicamente sólido y muy bien documentado. Los datos reales, el pipeline, el versionado, el modelo, la calidad y las conclusiones justifican una calificación alta. La nota se reduce principalmente por las pruebas públicas y orales todavía pendientes, no por una ausencia grave en los criterios centrales.

La rúbrica se podría cambiar de 8,8/10 a 9,5–10/10 una vez completada la demostración pública y ejecutadas las pruebas de aceptación restantes.