# Memoria del proyecto: decisiones, implementación y resultados

## 1. Objetivo y alcance

El observatorio integra eventos de terremotos del catálogo GeoJSON de USGS,
conserva sus versiones y los presenta en una SPA. El trabajo incluye dos
poblaciones separadas (`live` y `replay`): una consulta periódica del feed
actual y una carga histórica mundial de 2025 con `eventtype=earthquake` y
`minmagnitude=4`. El pipeline es USGS → productor → Kafka → consumidor →
PostgreSQL → API FastAPI → frontend Angular.

Esta memoria recoge resultados observados en el entorno local y distingue
datos reales, mediciones sintéticas y verificaciones no realizadas. El alumno
confirma que ha probado el despliegue con Netlify, Docker y ngrok; esta
confirmación se identifica como tal y no como una verificación independiente
realizada durante la elaboración de esta memoria. La prueba informal de una
persona tampoco se presenta como evaluación formal de usabilidad.

### 1.1. Arquitectura y componentes construidos

El proyecto implementa una cadena de ingesta, persistencia, consulta y
visualización. El alcance elegido es un feed reciente de USGS y un baseline
mundial de 2025 filtrado a terremotos de magnitud igual o superior a 4; el
catálogo geográfico es la copia de Natural Earth incluida en el repositorio.
Los componentes ejecutables son:

| Componente | Implementación y responsabilidad |
|---|---|
| Productor live | [`backend/src/observatorio/producer/live.py`](./backend/src/observatorio/producer/live.py) consulta el feed periódico y prepara las novedades. |
| Productor histórico | [`backend/src/observatorio/producer/replay.py`](./backend/src/observatorio/producer/replay.py) consulta intervalos históricos, archiva respuestas y puede reanudar la carga. |
| Publicación | [`backend/src/observatorio/producer/publisher.py`](./backend/src/observatorio/producer/publisher.py) publica eventos versionados en Kafka y conserva el estado de publicación. |
| Broker | Kafka separa productores y consumidor y permite reentrega de mensajes. |
| Consumidor | [`backend/src/observatorio/consumer/`](./backend/src/observatorio/consumer) valida y normaliza mensajes, integra países y persiste o pone en cuarentena. |
| Persistencia | PostgreSQL conserva versiones, estado actual, procedencia, ejecuciones, intervalos, payloads publicados y rechazos. |
| API | [`backend/src/observatorio/api/`](./backend/src/observatorio/api) expone consultas, estadísticas, comparación temporal y estado de ingesta. |
| Frontend | [`frontend/src/app/`](./frontend/src/app) presenta el mapa, filtros y análisis; la ruta `/reproduccion` consulta el modo histórico sin mezclarlo con live. |
| Despliegue | [`compose.yaml`](./compose.yaml) y [`backend/Dockerfile`](./backend/Dockerfile) definen los servicios del backend; la SPA se publica en Netlify y la API de demostración se expone mediante ngrok. |

El recorrido implementado es USGS → productor → Kafka → consumidor →
PostgreSQL → API → Angular. El backend se ejecuta en contenedores locales,
el esquema se aplica con migraciones Alembic y el catálogo de países se
prepara durante el arranque del API. El navegador no consulta USGS
directamente. Las instrucciones reproducibles están en el
[`README.md`](./README.md) y el procedimiento de operación detallado en
[`docs/GUIA-DESPLIEGUE.md`](./docs/GUIA-DESPLIEGUE.md).

### 1.2. Registro de decisiones de diseño

| Decisión | Motivo y efecto |
|---|---|
| Separar los modos `live` y `replay` en claves y consultas | Evita que la demostración histórica altere o contamine los datos recientes; el API permite consultar cada modo de forma aislada. |
| Identificar una versión por `(mode, event_id, updated_at)` y mantener un puntero actual | Conserva revisiones de USGS y permite responder con la versión vigente sin eliminar el historial. |
| Tolerar reentregas de Kafka mediante claves, hashes, restricciones y escritura idempotente | Kafka puede reenviar mensajes ante interrupciones. La deduplicación evita duplicar una versión ya procesada o una publicación confirmada. |
| Conservar escalas de magnitud, valores originales y ausencias | Evita comparar magnitudes de escalas distintas o inventar valores. Los datos no asignados geográficamente permanecen sin país. |
| Asignar país mediante geometría de Natural Earth, no mediante texto del lugar | La geografía se determina con coordenadas; si no hay exactamente una coincidencia, se almacena `country_id` nulo en vez de adivinar. |
| Descargar el histórico por intervalos y guardar respuestas y checkpoints | Hace posible reanudar una ejecución, rastrear la consulta de origen y resolver de forma segura límites que puedan solaparse. |
| Mantener la SPA fuera de Docker y no publicar Kafka/PostgreSQL | Netlify aloja el frontend; ngrok da acceso HTTPS a la API durante la demostración, sin exponer el broker ni la base de datos. |
| Aplicar el esquema en el arranque del API y conservar datos en volúmenes | Facilita el arranque desde un clon limpio y mantiene PostgreSQL, Kafka y archivos originales al detener los contenedores. |
| Indexar por modo y tiempo de evento | Las consultas del API filtran por modo y ventana temporal y ordenan por fecha; la medición local de la sección 5.4 documenta el plan y sus límites. |

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

### 2.1. Modelo conceptual, lógico y físico

En el nivel **conceptual**, un evento puede tener varias versiones; una de
ellas es la actual. Cada versión se asocia a una fecha UTC, puede asociarse a
un país y procede de una ejecución. Las ejecuciones e intervalos describen
cómo se obtuvo el dato; las publicaciones y la cuarentena registran el
procesamiento de Kafka.

En el nivel **lógico y físico**, las entidades principales se implementan
como estas tablas. Las migraciones de creación y evolución están en
[`backend/migrations/versions/`](./backend/migrations/versions/), y los
modelos ORM en [`backend/src/observatorio/models/`](./backend/src/observatorio/models/).

| Tabla | Qué representa una fila | Clave o restricción relevante |
|---|---|---|
| `event_version` | Una revisión normalizada de un evento en un modo | PK `(mode, event_id, updated_at)`; referencia a `country`, `calendar_date` y `ingestion_run`; comprobaciones de modo y rango de coordenadas. |
| `event_current` | La versión vigente de un evento para un modo | PK `(mode, event_id)` y FK compuesta a la versión vigente. |
| `event_version_source` | El payload fuente y su hash para una versión | PK/FK `(mode, event_id, updated_at)`; SHA-256 para comparar el contenido recibido. |
| `country` | Un país del catálogo Natural Earth | PK `country_id`; se conserva el identificador de catálogo `ADM0_A3`. |
| `calendar_date` | Una fecha UTC usada por las versiones | PK `date_utc`. |
| `ingestion_run` | Una ejecución de extracción o replay | PK UUID `run_id`; estado, fuente, intervalo consultado, contadores y error. |
| `source_archive` | Un archivo original identificado por contenido | PK SHA-256; ruta, tamaño, fuente y fechas de archivo/borrado. |
| `ingestion_interval` | Un intervalo de una ejecución histórica | PK `interval_id`; unicidad de ejecución e intervalo y estado/checks de contadores. |
| `published_version` | La confirmación de publicación de una versión en Kafka | PK `(mode, event_id, updated_at)`; topic, partición, offset y hora. |
| `published_payload` | Un payload confirmado para una versión y hash | PK `(mode, event_id, updated_at, payload_sha256)`. |
| `quarantine` | Un mensaje rechazado con motivo y posición Kafka | PK UUID `quarantine_id`; unicidad de `(kafka_topic, kafka_partition, kafka_offset)`. |

PostgreSQL usa tipos como UUID, `TIMESTAMPTZ`, `DATE`, `NUMERIC`, texto,
binario y JSONB para conservar los payloads y metadatos estructurados. Las
claves compuestas y restricciones protegen la identidad de versión, la
referencia de `event_current` y la idempotencia. La migración
[`0007_event_time_query_index.py`](./backend/migrations/versions/0007_event_time_query_index.py)
añade el índice temporal utilizado por las consultas paginadas del API. El
detalle ejecutable del esquema se mantiene en las migraciones, no duplicado
en esta memoria. `country_id` utiliza el atributo `ADM0_A3` del catálogo:
se comprobó su unicidad en la copia entregada, pero no se presupone que sea
un código ISO oficial.

## 3. Procedencia y extracción

| Conjunto | Fuente y periodo | Filtros | Evidencia |
|---|---|---|---|
| Captura del feed | USGS `all_day`, observada el 18-11-2026 a las 22:06:18 UTC | Respuesta completa del feed | 177 eventos; SHA-256 `daf5878259a555284f6254c8874568860104a116bbf6288f9692b076a66a9a0e` |
| Histórico anual | Catálogo USGS, 2025-01-01 inclusive a 2026-01-01 exclusive | Mundial, `earthquake`, magnitud mínima 4 | La consulta API replay devolvió 18.302 eventos y la comparación indicó cobertura completa |
| Consulta de comparación | API local, últimas 24 horas hasta 18-11-2026 22:21 UTC | Magnitud mínima 4 | 29 eventos actuales; baseline anual disponible |

Las consultas se reproducen con los endpoints y parámetros siguientes:

- Feed reciente: [`all_day.geojson`](https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson),
  ventana móvil de las últimas 24 horas, consultada nominalmente cada 60
  segundos.
- Histórico: servicio FDSN
  [`/fdsnws/event/1/query`](https://earthquake.usgs.gov/fdsnws/event/1/query)
  con `format=geojson`, `eventtype=earthquake`, `minmagnitude=4` y
  `orderby=time-asc`; el año se dividió en 12 intervalos mensuales entre el
  1-1-2025 (inclusive) y el 1-1-2026 (exclusive). El comando de carga y sus
  opciones están en el [`README.md`](./README.md).
- Geografía: archivo
  [`backend/data/ne_110m_admin_0_countries.geojson`](./backend/data/ne_110m_admin_0_countries.geojson),
  con su procedencia y licencia recogidas en
  [`docs/FUENTES-Y-LICENCIAS.md`](./docs/FUENTES-Y-LICENCIAS.md).

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

La cantidad alta de eventos sin país no significa que falten coordenadas. La
explicación esperada es que muchos sismos ocurren en el mar, como señala el
alumno; todavía no se ha contrastado individualmente todo el conjunto con una
referencia independiente ni se ha identificado un caso terrestre concreto que
debería tener país y no lo tenga. Por ello, el resultado se denomina «sin país
asignado», sin afirmar que el 78,41 % sea íntegramente marino ni inferir por
proximidad una etiqueta que el proceso no confirmó. Se preservan las
magnitudes por escala y las profundidades originales. No se aplicaron correcciones al conjunto:
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
promedio, con coste de memoria O(N) para construirlo. Este microbenchmark
aislado no representa una estructura concreta del pipeline de PostgreSQL y no
demuestra la latencia del API, Kafka ni una carga sísmica real. Para completar
esa limitación, se midieron también la consulta real de PostgreSQL y el API
local, cuyos resultados se presentan a continuación.

#### Complejidad de otras operaciones implementadas

- **Integración geográfica:** el consumidor compara cada punto con las
  geometrías de los países de Natural Earth mediante `covers`. Las geometrías
  se cargan y cachean en el proceso, pero la búsqueda actual recorre el
  catálogo para cada evento: se evalúan O(C) geometrías por evento y O(E × C)
  para E eventos y C geometrías; el coste de cada predicado depende también
  de la complejidad de sus polígonos. Solo se asigna país si existe
  exactamente una coincidencia. El catálogo es pequeño para el alcance
  actual; para volúmenes mayores convendría evaluar un índice espacial (por
  ejemplo, STRtree) y medirlo antes de adoptarlo.
- **Agregación por hora y país:** las estadísticas del API recorren las filas
  seleccionadas y usan contadores/diccionarios (`Counter`), con coste esperado
  O(E) y memoria adicional O(B), donde B es el número de intervalos o
  categorías, además de las filas que ya materializa la consulta. La
  comparación histórica también carga las filas del periodo en memoria; con
  conjuntos mucho mayores, trasladar agregaciones a SQL o procesarlas por
  bloques reduciría memoria de aplicación.
- **Consulta paginada:** PostgreSQL localiza las versiones mediante claves e
  índice temporal y devuelve una página acotada; el conteo total se calcula
  aparte y `OFFSET` tiene un coste que aumenta con la página solicitada. La
  medición de la sección 5.4 cuantifica esta diferencia para el baseline, no
  permite extrapolar el resultado a otros tamaños.

### 5.4 PostgreSQL y API: medición sobre datos del proyecto

Medición realizada el 19-11-2026 sobre los 18.302 eventos del histórico
replay, sin carga concurrente deliberada. Entorno local: Linux Mint 22.3,
Intel Core Ultra 7 255U, 14 CPU lógicas, aproximadamente 32 GB RAM reportados;
PostgreSQL y API en Docker Compose. Las peticiones se hicieron secuencialmente
desde el mismo equipo por HTTP local. Para cada caso se hicieron cinco
peticiones de calentamiento y se midieron 40 respuestas completas. El p95 es
el elemento 38 de las 40 duraciones ordenadas.

| Consulta API `GET /api/eventos` | Mediana | p95 | Mín.–máx. | Filas por respuesta |
|---|---:|---:|---:|---:|
| Replay anual, primera página (`offset=0`, `limit=100`) | 104,31 ms | 142,74 ms | 40,71–180,20 ms | 100 de 18.302 |
| Mismos filtros, página final (`offset=18.000`, `limit=100`) | 197,53 ms | 246,88 ms | 161,50–267,70 ms | 100 de 18.302 |

La latencia incluye API, serialización JSON y transporte local, pero no el
render del navegador. La página final es más lenta, coherente con el coste de
recorrer filas omitidas por `OFFSET`; no debe extrapolarse linealmente a
100 millones.

Un `EXPLAIN (ANALYZE, BUFFERS)` de la consulta de página encontró el índice
`ix_event_version_mode_event_time`: devolución de 100 filas en 8,736 ms en el
motor SQL. Como contraste diagnóstico, dentro de una transacción de solo
lectura se deshabilitaron localmente los index scans para observar un plan de
secuencial scan más ordenación top-N; tardó 46,549 ms para la misma página.
La relación de tiempos de esa ejecución es 5,3×, pero **no es una comparación
controlada de dos bases idénticas con y sin índice**: el plan forzado también
deshabilita otros index scans y los tiempos son una sola ejecución caliente.
El resultado evidencia que el plan indexado es útil para esta ventana, no
prueba universal de aceleración ni sustituye una prueba con más tamaños.

El conteo exacto antes de paginar ejecutó un scan y un hash join de unas
18.302 filas en 33,431 ms. Es una sola ejecución `EXPLAIN ANALYZE`, en caché;
su extrapolación lineal aproximada a 100 millones sería 183 segundos. Ese
número es un **escenario aritmético, no una predicción**: el plan, caché,
particiones, distribución, hardware y concurrencia cambiarían. Sí advierte
que contar todos los resultados en cada página puede convertirse en un cuello
de botella incluso si la página de 100 filas usa índice.

Estas pruebas no son el criterio SC-002: no usaron la fixture reproducible de
1.000 eventos, no midieron ambas tablas ni 100 navegaciones por tamaño, y no
midieron el tiempo hasta el render del DOM. El navegador, llamadas
concurrentes, caché fría y carga sostenida quedan pendientes.

### 5.5 Conclusiones

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
  [`docs/PIPELINE-OPERACION.md`](./docs/PIPELINE-OPERACION.md).
- Kafka conserva el log durante 168 horas; las versiones aceptadas quedan en
  PostgreSQL y el histórico original en el volumen de archivos. La retención
  limitada evita tratar Kafka como archivo permanente.

### 6.1 Costes locales: magnitudes observadas y estimadas

No se instaló un medidor de consumo ni hay factura separada del proyecto; por
tanto, la electricidad y el coste de oportunidad del equipo no son costes
medidos. Sí se midió el almacenamiento persistente:

| Recurso medido | Resultado | Alcance |
|---|---:|---|
| Base PostgreSQL completa | 69 MB | Base local con las tablas del pipeline y datos de ambos modos |
| Cinco tablas principales de eventos, incluyendo índices | 61.693.952 bytes (58,84 MiB) | `event_version`, `event_version_source`, `event_current`, `published_payload`, `published_version`; incluye filas adicionales no pertenecientes al baseline anual |
| Archivos fuente de la ejecución anual 2025 | 13.011.875 bytes (12,41 MiB) | 12 respuestas archivadas para la ejecución anual, enlazadas desde sus intervalos |
| Volumen completo `source_archives` en la fecha de medida | 280.476.853 bytes (267,5 MiB) | Contiene archivos de otras ejecuciones también; no se atribuye todo al baseline |

Para estimar la electricidad del entorno local, supongo un consumo **adicional**
de 30–80 W mientras corre el stack y 730 horas mensuales. A una tarifa
hipotética de 0,15–0,30 €/kWh:

`0,03–0,08 kW × 730 h = 21,9–58,4 kWh/mes`

`21,9–58,4 kWh × 0,15–0,30 €/kWh ≈ 3,29–17,52 €/mes`.

Es un rango para presupuestar, no una medición del equipo. No incluye pantalla,
router ni consumo base del ordenador; para sustituirlo por dato real hay que
medir con vatímetro el equipo en reposo y con Compose, restar ambos valores y
multiplicar la diferencia por horas y tarifa efectiva. Si el ordenador se
compra específicamente para el proyecto, su amortización debe añadirse aparte.
No se compró hardware dedicado: el equipo de desarrollo es compartido y no se
registró su precio ni la fracción de uso atribuible al observatorio, por lo que
no le asigno un coste histórico inventado. En el escenario cloud de abajo el
cómputo alquilado sí es la partida que representa el hardware.

Las horas de desarrollo reales no se registraron y no son reconstruibles con
precisión desde los commits. Para visibilizar el coste de oportunidad, una
planificación hipotética de 80–160 horas a 20–35 €/h equivale a **1.600–5.600
€ de coste único**. No es una afirmación de las horas trabajadas ni una factura;
debe reemplazarse por un registro de horas y una tarifa acordada. El
mantenimiento futuro también se debe contabilizar: con 2–4 horas al mes bajo
la misma tarifa, serían 40–140 €/mes.

### 6.2 Escenario de infraestructura para 100 millones de registros

Para que la escala sea cuantificable, defino 100 millones como registros de
eventos/versiones retenidos simultáneamente, con **una versión media por
evento**, manteniendo el esquema actual y sin considerar compresión adicional.
En este escenario:

- 100.000.000 / 18.302 = **5.463,9 veces** el baseline anual observado.
- Si fueran 100 millones de altas cada año, el promedio sería 273.973 eventos
  al día, o 3,17 por segundo. Es un promedio; los picos pueden ser superiores.
- Las cinco tablas principales ocuparon 61.693.952 bytes para una base de
  18.302 eventos anuales más algunas filas ajenas a ese baseline. Dividir por
  18.302 y multiplicar por 100 millones da aproximadamente **337,1 GB
  (313,9 GiB)** de tablas e índices. Es una aproximación de orden de magnitud,
  no una medición de una base de 100 millones.
- Las 12 respuestas originales del baseline promediaron unos 711 bytes por
  evento según el tamaño de archivo registrado. Manteniendo esa razón,
  100 millones requerirían unos **71,1 GB (66,2 GiB)** de respuestas fuente.
  Los filtros, el formato de respuesta y la compresión pueden cambiarla.
- Tabla e índices más una copia de fuentes sumarían aproximadamente **408 GB**
  antes de WAL, bloat, backups, réplicas, espacio libre y datos operativos.
  Una previsión prudente sería probar con 1 TB de SSD para PostgreSQL y 200 GB
  para archivos originales; las copias de seguridad necesitan capacidad
  adicional. Si el promedio fuera dos versiones por evento, las tablas
  versionadas crecerían sustancialmente y habría que dimensionar de nuevo.

No bastaría con ampliar el disco. `country_for_coordinates` comprueba en el
código actual cada punto frente a las 177 geometrías del catálogo: para 100
millones de eventos representa hasta **17.700 millones de predicados
poligonales** si se conserva el algoritmo. Un `STRtree` espacial para reducir
los polígonos candidatos sería una mejora a probar y medir.

Las estadísticas actuales materializan los eventos consultados en memoria y
recorren las filas con contadores Python: coste O(N) de CPU y O(N) de memoria
para la lista de filas, más los buckets. En 100 millones, esa estrategia no
es apropiada sin particionar/batchear; convendría agregar en PostgreSQL por
ventanas y países, paginar/streaming para los resultados detallados y evitar
calcular un `COUNT(*)` global en cada navegación. La paginación por offset
también debería evaluarse frente a cursores/keyset en páginas muy profundas.
Particionar por tiempo, mantener índices con una carga representativa y
revisar archivado/retención son decisiones que dependen del patrón de consulta.

### 6.3 Presupuesto ilustrativo de despliegue

El siguiente cálculo usa **precios unitarios hipotéticos**, solo para mostrar
el método; no es una cotización de AWS, Azure, GCP ni de un proveedor concreto
y no incluye IVA. Supone 730 h/mes, disponibilidad básica sin alta
disponibilidad, 1 TB SSD, 200 GB de objetos originales, una copia de backup de
400 GB y 100 GB/mes de salida:

| Partida | Supuesto | Cálculo | €/mes aproximados |
|---|---|---:|---:|
| Cómputo PostgreSQL administrado | 4 vCPU y 16 GiB; 0,04 €/vCPU-h y 0,005 €/GiB-h | (4×0,04 + 16×0,005)×730 | 175,20 |
| API, Kafka, productor y consumidor | Total 4 vCPU y 8 GiB con las mismas tarifas | (4×0,04 + 8×0,005)×730 | 146,00 |
| SSD PostgreSQL | 1.000 GB a 0,10 €/GB-mes | 1.000×0,10 | 100,00 |
| Backup de base de datos | 400 GB a 0,02 €/GB-mes | 400×0,02 | 8,00 |
| Archivos fuente | 200 GB de almacenamiento de objetos a 0,02 €/GB-mes | 200×0,02 | 4,00 |
| Transferencia saliente | 100 GB a 0,05 €/GB | 100×0,05 | 5,00 |
| **Subtotal cloud ilustrativo** | Sin redundancia/HA, impuestos ni soporte | Suma de partidas | **438,20** |
| Operación humana | 2–4 h/mes a 20–35 €/h | Rango | **40–140** |
| **Total mensual ilustrativo** | Cloud más operación | Rango | **478–578** |

Con los mismos supuestos, el coste único de desarrollo de 1.600–5.600 € no
está incluido en el mensual. La electricidad doméstica tampoco se añade a la
factura cloud: el consumo del centro de datos está incorporado en el precio
del servicio. Una arquitectura con réplica disponible, más IOPS, backups
diarios completos, mayor tráfico o soporte puede superar ampliamente este
escenario; la decisión final requiere cotizar las tarifas vigentes con la
retención, SLA y región elegidas. Una cuota gratuita reduce el desembolso, no
el tiempo de operación ni el coste del hardware local.

### 6.4 Límites y decisión de escalado

Las cifras de 100 millones multiplican tamaños y una consulta observados sobre
18.302 registros. No son un benchmark de escala: pueden cambiar el tamaño de
los payloads, la proporción de revisiones, la distribución de eventos, el
índice seleccionado, la memoria de trabajo, el caché, la concurrencia y la
fragmentación. El cálculo lineal de 183 segundos para el conteo tampoco debe
usarse como SLO. Antes de contratar capacidad, se debe generar una fixture
sintética etiquetada, probar al menos 1M y 10M registros y medir disco, RAM,
latencia p95/p99 y throughput, así como validar planes `EXPLAIN (ANALYZE,
BUFFERS)` con y sin índice sobre copias desechables.

Las métricas actuales reducen parte de la incertidumbre: se observó en la base
real el coste de la consulta y se midió el tamaño persistente. No resuelven
todavía los criterios de rendimiento del navegador ni la evaluación formal de
participantes; estos pendientes siguen explícitos en la sección siguiente.

## 7. Pruebas y estado operativo

Comprobaciones ejecutadas entre el 18 y el 19-11-2026:

- Backend: 124 pruebas unitarias/de contrato superadas.
- Integración: 17 pruebas superadas y 1 prueba PostgreSQL aislada superada.
- Cliente de API Node: 13 pruebas superadas.
- `npm run build`: build Angular correcto; quedan avisos de dependencias
  CommonJS/AMD de Cesium y deck.gl, no bloqueantes.
- Smoke test en navegador en `http://localhost:4200/reproduccion`: ruta,
  filtro del primer día de 2025, etiqueta inequívoca y consulta de 60 eventos
  cargados desde replay. No se hizo evaluación sistemática de interacción.
- El alumno confirma haber probado el flujo de publicación Netlify + API
  local en Docker expuesta por ngrok. Cuando el túnel no está disponible, el
  frontend muestra un error de conexión con la API. No se verificaron aquí los
  dominios públicos ni se conservan capturas de esa ejecución; tampoco se
  documenta un reintento automático tras recuperar el túnel.
- Una persona probó informalmente la aplicación y la describió como intuitiva,
  según el alumno. No se siguió el protocolo SC-003/SC-006, no se midieron
  tiempos o tareas y una persona no satisface el requisito formal de diez.
- En la respuesta local de estadísticas consultada el 19-11-2026, la API
  devolvió la categoría `USA` («Estados Unidos») con 169 eventos. El gráfico
  de países tenía altura fija para un número variable de categorías; ahora
  ordena por recuento descendente, ajusta la altura y permite desplazarse para
  recorrerlas. Se verificó visualmente que Estados Unidos queda visible al
  inicio y que las listas extensas se pueden recorrer.
- `docker compose config --quiet`: correcto; los cinco servicios terminaron
  saludables. La API reporta `0007_event_time_query_index`, el índice temporal
  existe en PostgreSQL y Kafka arrancó con `KAFKA_LOG_RETENTION_HOURS=168`.
- La suite Karma/Angular no se validó porque no hay Chrome/Chromium disponible
  para `ChromeHeadless`.

El despliegue Netlify/ngrok se considera probado por el alumno, pero no fue
verificado independientemente en esta revisión. No se ha ejecutado el
protocolo de diez participantes. El guion y el formulario agregado están
preparados en
[`docs/evaluacion-usabilidad-007.md`](./docs/evaluacion-usabilidad-007.md);
la prueba informal de una persona no permite declarar SC-003 ni SC-006
superados. Tampoco se han medido los umbrales de rendimiento SC-002. Esas
pruebas requieren fixture y/o participantes, y no se sustituyen por la
compilación o la inspección de una página local.

### 7.1. Reproducción histórica: procedimiento y resultado

Con los cinco servicios saludables, la carga se inicia con el comando
documentado en el [`README.md`](./README.md): se solicita el año 2025,
`eventtype=earthquake`, magnitud mínima 4 e intervalo de envío cero. El
productor descarga y archiva los intervalos, registra checkpoints y publica
en el modo `replay`; si se interrumpe, se puede volver a ejecutar para
reanudar. Los registros mantienen su fecha original y no se insertan en la
población `live`.

El resultado anual observado fue 18.302 versiones procesadas en 12 de 12
intervalos mensuales; 60 eventos del primer día ya estaban confirmados por
una ejecución anterior, lo que explica que la ejecución anual publicara
18.242 mensajes nuevos. En el smoke test del 18-11-2026 se abrió
`/reproduccion`, se filtró el 1 de enero de 2025 y se mostraron 60 de 60
eventos del modo histórico en tabla y mapa. La ruta permite ajustar el
intervalo y la magnitud; el mapa puede limitarse a los primeros 100 registros.
La cobertura y el comportamiento de deduplicación se detallan en la sección
3. La reproducción está implementada, aunque no se conserva una captura
independiente del despliegue público.