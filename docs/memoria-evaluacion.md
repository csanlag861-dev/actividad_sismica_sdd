# Memoria de evaluación y resultados

## 1. Objetivo y alcance

El observatorio integra eventos de terremotos del catálogo GeoJSON de USGS,
conserva sus versiones y los presenta en una SPA. El trabajo incluye dos
poblaciones separadas (`live` y `replay`): una consulta periódica del feed
actual y una carga histórica mundial de 2025 con `eventtype=earthquake` y
`minmagnitude=4`. El pipeline es USGS → productor → Kafka → consumidor →
PostgreSQL → API FastAPI → frontend Angular.

Esta memoria recoge resultados que se observaron en el entorno local y
distingue datos reales, mediciones sintéticas y verificaciones no realizadas.
No se atribuyen al proyecto despliegues públicos ni evaluaciones humanas que no
se hayan efectuado.

## 2. Diccionario y modelo de datos

| Campo | Significado | Tipo/unidad | Ausencia y tratamiento |
|---|---|---|---|
| `event_id` | Identificador del evento asignado por USGS | Texto | Obligatorio |
| `mode` | Población del evento | `live` o `replay` | Obligatorio; aísla las dos fuentes |
| `updated_at` | Revisión publicada por USGS | Fecha/hora UTC | Parte de la identidad de versión |
| `event_time` | Momento en que ocurrió el sismo | Fecha/hora UTC | Obligatorio; timestamps externos se convierten desde milisegundos Unix |
| `magnitude` | Magnitud informada | Decimal, escala indicada en `mag_type` | Se conserva nula; no se mezcla entre escalas |
| `mag_type` | Tipo/escala de magnitud (p. ej. `ml`, `md`, `mb`, `mww`) | Texto | Se conserva nulo |
| `place` | Descripción de USGS | Texto | Se conserva nula |
| `longitude`, `latitude` | Posición geográfica | Grados decimales WGS84 | Obligatorios y validados en rango |
| `depth_km` | Profundidad | Kilómetros | Se conserva nula o negativa; no se corrige sin evidencia |
| `country_id` | País asignado por unión espacial a Natural Earth | Código de catálogo | Nulo si no se asigna un país |
| `source`, `ingested_at`, `ingestion_run_id` | Procedencia y ejecución que aceptó la versión | Texto, UTC, UUID | Obligatorios para trazar el dato |

El grano de `event_version` es una versión identificada por
`(mode, event_id, updated_at)`. `event_current` apunta a la revisión vigente
para `(mode, event_id)`; por tanto, un evento puede evolucionar sin perder su
historial ni cruzarse entre modos. `country` y `calendar_date` actúan como
referencias. La API devuelve el evento actual del modo solicitado, ordenado
por tiempo de ocurrencia, e incluye trazabilidad compacta.

La integración geográfica se realiza en el consumidor, no mediante una
etiqueta manual del mapa. Los payloads originales y sus hashes se mantienen
en las tablas de procedencia, pero no se exponen desde el endpoint público.
La identidad de versión, el ledger de publicaciones y el procesamiento
transaccional permiten reintentar sin duplicar indebidamente datos. Para
acelerar ventanas temporales se añadió el índice
`(mode, event_time DESC, event_id)` en la migración `0007`; se comprobó su
presencia en PostgreSQL.

## 3. Procedencia y extracción

| Conjunto | Fuente y periodo | Filtros | Evidencia |
|---|---|---|---|
| Captura del feed | USGS `all_day`, observada el 18-11-2026 a las 22:06:18 UTC | Respuesta completa del feed | 177 eventos; SHA-256 `daf5878259a555284f6254c8874568860104a116bbf6288f9692b076a66a9a0e` |
| Histórico anual | Catálogo USGS, 2025-01-01 inclusive a 2026-01-01 exclusive | Mundial, `earthquake`, magnitud mínima 4 | La consulta API replay devolvió 18.302 eventos y la comparación indicó cobertura completa |
| Consulta de comparación | API local, últimas 24 horas hasta 18-11-2026 22:21 UTC | Magnitud mínima 4 | 29 eventos actuales; baseline anual disponible |

El histórico se obtuvo por intervalos mediante el productor, se archivó y
circuló por Kafka antes de quedar disponible como `replay`. El API permite
seleccionar el modo explícitamente; la nueva ruta `/reproduccion` consulta
`mode=replay`, permite acotar intervalo y magnitud, y advierte que el mapa
puede mostrar solo los primeros 100 registros. El 18-11-2026 se comprobó en
navegador la ruta con el primer día de 2025: la tabla y el mapa recibieron 60
eventos de 60, separados del modo live.

La diferencia de 60 quedó conciliada consultando el ledger y las ejecuciones.
Una ejecución previa el 16-11-2026 cargó y confirmó por Kafka los 60 eventos
del 1 de enero de 2025. En la ejecución anual del 18-11-2026
(`483e89b7-8b16-4da9-b34e-ccdc763264b3`), 12/12 intervalos mensuales finalizaron
correctamente: `records_received=18.302`, `unique_versions=18.302` y
`processed_count=18.302`. El campo `published_messages=18.242` cuenta las
publicaciones nuevas enviadas por esa ejecución, no los eventos procesados.
El ledger confirma 60 payloads idénticos ya confirmados antes de comenzar y
18.242 ACKs durante la ejecución. Por ello, 60 + 18.242 = 18.302: no hay
evidencia de pérdida; es el comportamiento esperado de la deduplicación
idempotente. PostgreSQL contiene 18.302 eventos actuales del periodo, sin
duplicados por identidad `event_id + updated_at`.

## 4. Calidad de datos

### 4.1 Captura real del feed

Sobre los 177 Features del snapshot USGS indicado arriba:

| Dimensión | Resultado observado | Decisión |
|---|---|---|
| Completitud de campos principales | 177/177 con magnitud, tipo de magnitud, lugar, tiempos y geometría/coordenadas completas | Se conservan los valores originales; no se imputan valores artificiales |
| Validez estructural | 0 errores de normalización observados | El GeoJSON aceptado mantiene su geometría y unidades |
| Unicidad | 177 identidades `id + updated` distintas | Se conservan revisiones mediante la identidad de versión |
| Consistencia de tipo | Los 177 registros eran `earthquake` | No se mezclan otros tipos sísmicos en esta medición |
| Asignación geográfica | 147 con país; 30 sin país (16,95 %) | Los no asignados permanecen explícitos como desconocidos; no se fuerza el país más cercano |
| Tipo de magnitud | `ml`: 99; `md`: 53; `mb`: 17; `mww`: 7; `mw`: 1 | Se preserva la escala para evitar comparar magnitudes como si fueran una única escala |
| Profundidad | 165/177 menores de 70 km; mediana 7,53 km; se observaron -0,21 km y -0,5 km | Los dos valores negativos se señalan, pero no se corrigen ni descartan sin revisar la referencia de profundidad |
| Intensidad | 26 eventos con magnitud ≥ 4 | Se informa con el umbral explícito, no como característica de todo evento del feed |

Los 30 eventos sin país no implican ausencia de coordenadas: el dato espacial
está completo, pero la unión con el catálogo no produjo una asignación. La
validez no equivale a exactitud física: no se contrastaron coordenadas ni
magnitudes con una fuente independiente. Tampoco se utiliza el valor de
cuarentena `14` como resultado de esta captura: pertenecía a estado compartido
de exclusiones live y no se pudo atribuir a este snapshot o a la carga anual.

En esta muestra no hubo errores de normalización que justificaran modificar
valores antes/después. Por eso el resultado posterior documentado es el de
validación y preservación, no una tasa de “reparación” inventada. En
producción, los inválidos y exclusiones se registran en cuarentena; los nulos
siguen siendo nulos y se separan de los denominadores estadísticos que
requieren magnitud o profundidad.

### 4.2 Perfil del histórico anual completo

El perfil se calculó el 18-11-2026 sobre los eventos actuales `mode=replay`
con `event_time` en `[2025-01-01, 2026-01-01)` y magnitud ≥ 4, el mismo
conjunto del baseline. La tabla almacena versiones aceptadas; esta consulta
describe el conjunto final y no sustituye un perfil de las respuestas crudas
de USGS.

Consulta principal ejecutada en PostgreSQL:

```sql
SELECT
    count(*) AS total,
    count(DISTINCT (e.event_id, e.updated_at)) AS unique_versions,
    count(DISTINCT e.event_id) AS unique_events,
    count(*) FILTER (WHERE e.mag_type IS NULL) AS missing_mag_type,
    count(*) FILTER (WHERE e.place IS NULL OR btrim(e.place) = '') AS missing_place,
    count(*) FILTER (WHERE e.depth_km IS NULL) AS missing_depth,
    count(*) FILTER (WHERE e.longitude IS NULL OR e.latitude IS NULL)
        AS missing_coordinates,
    count(*) FILTER (WHERE e.country_id IS NULL) AS unassigned_country,
    count(*) FILTER (
        WHERE e.longitude NOT BETWEEN -180 AND 180
           OR e.latitude NOT BETWEEN -90 AND 90
    ) AS invalid_coordinates,
    count(*) FILTER (WHERE e.depth_km < 0) AS negative_depth,
    min(e.magnitude) AS min_magnitude,
    max(e.magnitude) AS max_magnitude,
    min(e.depth_km) AS min_depth_km,
    max(e.depth_km) AS max_depth_km,
    count(DISTINCT e.country_id) FILTER (WHERE e.country_id IS NOT NULL)
        AS assigned_countries
FROM event_version AS e
JOIN event_current AS c
  ON c.mode = e.mode
 AND c.event_id = e.event_id
 AND c.current_updated_at = e.updated_at
WHERE e.mode = 'replay'
  AND e.event_time >= TIMESTAMPTZ '2025-01-01 00:00:00+00'
  AND e.event_time < TIMESTAMPTZ '2026-01-01 00:00:00+00'
  AND e.magnitude >= 4;
```

Resultados sobre **18.302** eventos actuales:

| Dimensión | Resultado | Interpretación/acción |
|---|---:|---|
| Unicidad | 18.302 versiones únicas y 18.302 identificadores únicos; 0 filas duplicadas por identidad | Cada evento aparece una sola vez en el conjunto filtrado |
| Magnitud | Rango observado 4–8,8 en 18.302 registros | El filtro de origen/API ≥ 4 no permite estimar aquí cuántos eventos sin magnitud o por debajo de 4 fueron excluidos |
| Tipo de magnitud | `mb` 16.332 (89,24 %), `mww` 1.476 (8,06 %), `mwr` 354 (1,93 %), `ml` 76 (0,42 %), `mw` 29 (0,16 %), `md` 29 (0,16 %), `mwb` 6 (0,03 %) | Se preserva el tipo; la composición de escalas limita cualquier comparación directa de magnitudes |
| Lugar | 0 nulos o cadenas vacías | Los 18.302 registros tienen descripción |
| Profundidad | 0 nulas; rango 0,5–669,556 km; mediana 20,9395 km y percentil 95 de 414,2888 km | No se observan negativos en este baseline; se conserva el rango profundo, sin recortarlo |
| Tramos de profundidad | Menos de 70 km: 13.689 (74,80 %); de 70 a menos de 300 km: 3.511 (19,18 %); 300 km o más: 1.102 (6,02 %) | Tramos descriptivos; no se usan como umbrales de validez |
| Asignación por país | 3.952 asignados (21,59 %) a 87 países; 14.350 sin asignar (78,41 %) | No equivale a coordenadas ausentes: el campo país no es obligatorio y se deja nulo si la unión espacial no asigna |
| Coordenadas | 0 nulas y 0 fuera de longitud [-180,180] o latitud [-90,90] | Los campos son obligatorios y tienen restricciones de rango en PostgreSQL |
| Cuarentena replay | 0 filas con `mode=replay` al momento de la consulta | No se observaron rechazos replay en la tabla de cuarentena; no demuestra la exactitud física del catálogo |

La cantidad alta de eventos sin país es una limitación de la integración con el
catálogo geográfico, no prueba de que falten coordenadas. La decisión actual
es conservarlos como «sin país asignado» y no inferir por proximidad una
etiqueta que el proceso no confirmó. Se preservan las magnitudes por escala y
las profundidades originales. No se aplicaron correcciones al conjunto:
ningún valor de coordenadas o profundidad de los registros aceptados incumplió
los controles consultados, así que no existe un “antes/después” de limpieza
que se pueda afirmar honestamente. El pipeline sí distingue rechazos en
cuarentena, pero el perfil describe datos persistidos, no un registro crudo
completo de descartes del origen.

### 4.3 Límites de la medición

La medición se limita al endpoint histórico consultado con `eventtype=earthquake`
y `minmagnitude=4`, y a las versiones actuales aceptadas. El filtro hace
imposible medir aquí la proporción de eventos USGS sin magnitud o por debajo
de 4; tampoco se contrastaron magnitudes ni posiciones con una fuente
independiente. El 0 de coordenadas inválidas se mide en la base y está
respaldado por restricciones de rango, pero no es una validación de exactitud
geográfica. La captura independiente de 177 eventos `all_day` sigue siendo
una muestra distinta, con sus propios resultados.

## 5. Análisis y resultados

### 5.1 Ventanas y comparación histórica

El baseline de 2025 contiene 18.302 eventos según la consulta API con los
filtros especificados y 365 días de cobertura. Su promedio es:

`18.302 / 365 = 50,1425 eventos/día`.

En la lectura del 18-11-2026 a las 22:21 UTC, el periodo móvil de 24 horas con
magnitud mínima 4 devolvió 29 eventos, frente al promedio anual de 50,1425.
La comparación es equivalente en el umbral de magnitud, pero una sola ventana
diaria no permite inferir una tendencia sísmica ni explica estacionalidad,
cambios de catálogo o variabilidad aleatoria. La API también devolvió 7.685
eventos para la primera mitad de 2025 con cobertura de 181 días; es otra
ventana de análisis, no una prueba de uniformidad temporal.

### 5.2 Distribución histórica completa y captura del feed

En el baseline anual filtrado, el 74,80 % de los eventos tiene profundidad
menor de 70 km; la mediana es 20,9395 km. La distribución por tipo de magnitud
está dominada por `mb` (89,24 %) y `mww` (8,06 %), bajo el mismo filtro anual.
En cambio, la captura independiente de 177 eventos `all_day` tenía 165/177
(93,22 %) bajo 70 km, mediana 7,53 km y predominio de `ml` (99) y `md` (53).
La diferencia entre las dos distribuciones muestra por qué se deben conservar
periodo, filtro y procedencia: la captura de un día no representa el año.

### 5.3 Complejidad y microbenchmark

Se comparó una búsqueda lineal con una búsqueda en diccionario usando claves
sintéticas, no eventos ni consultas a PostgreSQL. Entorno: Python 3.12.3,
Linux Mint 22.3, Intel Core Ultra 7 255U, 14 CPU lógicas y aproximadamente
32 GB de RAM reportados.

| Identificadores | Búsqueda lineal, mediana/op | Diccionario, mediana/op | Memoria del diccionario |
|---:|---:|---:|---:|
| 1.000 | 25,2 µs | 0,104 µs | 46.772 bytes |
| 10.000 | 134,228 µs | 0,053 µs | 480.356 bytes |
| 100.000 | 1.683,923 µs | 0,045 µs | 6.637.604 bytes; pico observado 8.206.836 bytes |

La búsqueda lineal es O(N) por consulta y el acceso a un diccionario es O(1)
promedio, con coste de memoria O(N) para construirlo. Este microbenchmark solo
justifica la estructura para búsquedas repetidas en memoria; no demuestra la
latencia del API, PostgreSQL, Kafka ni una carga real de 100.000 eventos.

### 5.4 Conclusiones

1. El baseline anual tiene cobertura completa y su diferencia de 60 se explica
   por deduplicación: esos payloads ya estaban confirmados desde una ejecución
   previa de un día; no faltan en los 18.302 eventos finales.
2. La calidad del conjunto aceptado es alta en completitud de lugar y
   profundidad y en rangos estructurales; la principal limitación es que
   78,41 % no recibe país. Mantener el estado explícito evita inventar
   geografía.
3. Las escalas del catálogo anual están dominadas por `mb`, frente al
   predominio `ml`/`md` del snapshot `all_day`; los subconjuntos no se deben
   comparar sin filtros y periodos equivalentes.
4. El diccionario reduce la latencia de búsqueda del microbenchmark a cambio
   de memoria; para ventanas persistentes son pertinentes el índice SQL y la
   paginación.

## 6. Operación, memoria y costes

- La consulta live está configurada cada 60 segundos: como máximo nominal son
  1.440 ciclos diarios, sin que eso garantice 1.440 respuestas correctas.
  Cada consulta tiene timeout y reintentos documentados en
  [`PIPELINE-OPERACION.md`](./PIPELINE-OPERACION.md).
- Kafka conserva el log durante 168 horas; las versiones aceptadas quedan en
  PostgreSQL y el histórico original en el volumen de archivos. La retención
  limitada evita tratar Kafka como archivo permanente.
- No se obtuvo una factura ni se midió consumo eléctrico. No se asigna un
  coste monetario ficticio. Para una estimación de despliegue habría que
  multiplicar horas de cómputo, GB-mes de base/archivos y tráfico saliente por
  las tarifas reales del proveedor; también incluir almacenamiento y backup.
- La memoria medida solo cubre la tabla hash sintética. El límite real debe
  calcularse con el tamaño de lote, payload original, índices, réplicas y
  retención de PostgreSQL/Kafka.
- Si el volumen crece, las propuestas son medir EXPLAIN/latencia con datos
  representativos, vigilar tamaño e índices, particionar o archivar según
  retención acordada y cuantificar coste con tarifas reales antes de escalar.

## 7. Pruebas y estado operativo

Comprobaciones ejecutadas el 18-11-2026:

- Backend: 124 pruebas unitarias/de contrato superadas.
- Integración: 17 pruebas superadas y 1 prueba PostgreSQL aislada superada.
- Cliente de API Node: 13 pruebas superadas.
- `npm run build`: build Angular correcto; quedan avisos de dependencias
  CommonJS/AMD de Cesium y deck.gl, no bloqueantes.
- Smoke test en navegador en `http://localhost:4200/reproduccion`: ruta,
  filtro del primer día de 2025, etiqueta inequívoca y consulta de 60 eventos
  cargados desde replay. No se hizo evaluación sistemática de interacción.
- `docker compose config --quiet`: correcto; los cinco servicios terminaron
  saludables. La API reporta `0007_event_time_query_index`, el índice temporal
  existe en PostgreSQL y Kafka arrancó con `KAFKA_LOG_RETENTION_HOURS=168`.
- La suite Karma/Angular no se validó porque no hay Chrome/Chromium disponible
  para `ChromeHeadless`.

No se ha publicado en Netlify, abierto un túnel ngrok público ni realizado el
protocolo de diez participantes. El guion y el formulario agregado están
preparados en [`evaluacion-usabilidad-007.md`](./evaluacion-usabilidad-007.md),
pero no se han medido SC-003 ni SC-006. Tampoco se han medido los umbrales de
rendimiento SC-002. Esas pruebas requieren fixture y/o participantes, y no se
sustituyen por la compilación o la inspección de una página local.

## 8. Reevaluación orientativa con la rúbrica del apartado 13

El enunciado no asigna ponderaciones numéricas por criterio. Para hacer
transparente esta estimación, se usa promedio simple; la nota oficial puede
variar según el docente y la defensa.

| Criterio | Nota estimada | Nivel de rúbrica | Justificación y mejora pendiente |
|---|---:|---|---|
| Extracción | 9,5/10 | Sobresaliente | Feed, histórico y procedencia medidos; 12/12 intervalos completos y discrepancia de los 60 ACKs explicada con el ledger |
| Calidad | 9,0/10 | Sobresaliente | Perfil de 18.302 eventos con completitud, unicidad, coordenadas, distribución, país, rango y cuarentena; no se inventa una reparación antes/después sin valores que corregir |
| Modelado | 9,0/10 | Sobresaliente | Grano/versionado, separación live/replay, idempotencia, integración geográfica, migración e índice aplicado comprobados |
| Análisis | 8,5/10 | Sobresaliente | Comparación de ventanas, baseline anual completo, distribuciones y conclusiones; no se infiere tendencia ni exactitud externa |
| Reflexión | 7,5/10 | Notable | Complejidad, memoria, límites, costes y protocolo humano documentados; siguen pendientes evaluación real, medición SC-002 y despliegue público |
| **Promedio simple** | **8,7/10** | **Notable alto, provisional** | La evidencia de datos y extracción mejoró; la máxima nota sigue dependiendo de pruebas públicas y participantes |

La mejora prioritaria para acercarse al 10 es publicar el despliegue y ejecutar
SC-002 y el protocolo sin ayuda de diez participantes para SC-003/SC-006,
guardando solo las evidencias agregadas y el contexto de ejecución. La nota de
esta memoria es una valoración razonada, no una calificación oficial.
