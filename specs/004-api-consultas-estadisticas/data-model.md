# Data Model: Consulta API y estadísticas sísmicas

## Alcance

No se introducen entidades persistidas ni migraciones. La API lee los modelos SQLAlchemy/PostgreSQL creados por las fases R15–R17 y construye entidades de respuesta. Todas las horas internas se tratan como UTC; fechas JSON de contrato se expresan como epoch Unix en milisegundos.

## Entidades persistidas consultadas

### Evento sísmico actual

**Grano**: una fila por `(mode, event_id)` en `event_current`, asociada mediante `(mode, event_id, current_updated_at)` a una fila única de `event_version`.

| Campo lógico | Campo persistido | Regla de salida |
|---|---|---|
| modo de pipeline | `event_current.mode` | Los endpoints recientes leen `live`; la comparación lee `replay`. No mezclar modos. |
| identidad | `event_current.event_id` | Se devuelve como `Feature.id`; una versión actual por identidad y modo. |
| actualización actual | `event_current.current_updated_at` | Debe apuntar a la versión referenciada, no a `MAX(updated_at)` calculado independientemente. |
| ocurrencia | `event_version.event_time` | Filtros y buckets se basan en este valor UTC. |
| actualización | `event_version.updated_at` | Se serializa en `properties.updated` como epoch ms UTC. |
| magnitud/tipo | `magnitude`, `mag_type` | Magnitud desconocida se serializa `null`; tipo puede ser null. |
| lugar | `place` | Texto opcional; sin inferencia/sustitución. |
| coordenadas | `longitude`, `latitude`, `depth_km` | Geometry Point `[lon, lat, depth_km]` con profundidad conocida; si profundidad es null, GeoJSON Point bidimensional `[lon, lat]` y `properties.depth_km: null`. Profundidad en km. |
| país | `country_id` y `Country.country_name` | País y nombre null si no asignado; sin atribución por proximidad. |
| procedencia | `source`, `ingested_at`, `ingestion_run_id` | Se conserva en persistencia; solo la metadata pública necesaria se expone. |

### Ejecución de ingesta

`IngestionRun` registra `mode`, `source`, `started_at`, `request_end`, `outcome`, `http_status` y errores. La fecha pública de última ingesta se obtiene del `request_end` más reciente que corresponde a una consulta live de USGS terminada correctamente (`outcome=succeeded`, origen `usgs-live`). Si ninguna existe, es `null`. Un fallo no debe reemplazar la fecha de una ejecución correcta anterior.

## Entidades de respuesta

### Feature de evento

- `type`: constante `Feature`.
- `id`: identificador del evento.
- `geometry`: `Point`; arreglo de longitud, latitud y profundidad en km. Coordenadas horizontales siempre finitas y dentro de rango por validación persistida; profundidad puede ser null.
- Si la profundidad está disponible, `geometry.coordinates` es `[longitude, latitude, depth_km]`; si se desconoce, es `[longitude, latitude]`, que mantiene la geometría GeoJSON válida.
- `properties`: `mag`, `magType`, `place`, `time`, `updated`, `depth_km`, `country_id`, `country_name`.
- Nulos se serializan como JSON `null`; nunca NaN/Infinity.

### Colección de eventos

- `type`: constante `FeatureCollection`.
- `metadata`: `generated` (hora de generación), `last_ingestion`, `mode`, `count`, `truncated`.
- `features`: lista de Features actuales live tras aplicar filtros.
- Default: periodo UTC `[ahora - 24h, ahora)`. En entrega sin límite preventivo `truncated=false` y `count` es el tamaño completo. Si se introduce un máximo, `count` es el total antes de truncar y la continuación se documenta como parte del contrato.

### Resultado estadístico

- Contexto común por bloque: `period` con inicio inclusive/fin exclusivo ISO UTC, filtros normalizados, unidad y `missing_count`.
- Buckets por hora: inicio de bucket UTC y `count`; incluir buckets vacíos del intervalo consultado para mantener continuidad.
- Buckets por país: `country_id`, nombre y `count`; null representa «Sin país asignado». `missing_count` es el subconjunto no asignado, también incluido en el bucket null.
- Distribuciones: bins semiabiertos (`min_inclusive`, `max_exclusive`, `count`, `percentage`) alineados a múltiplos enteros de la anchura `[k*w, (k+1)*w)`, `valid_count` y `missing_count` separados; anchura fija magnitud 0.5 y profundidad 10 km. `valid_count` es el denominador de cada porcentaje y cuenta solo eventos con un valor válido para esa variable dentro de la población filtrada. Los nulos no entran en porcentaje ni bins y se contabilizan aparte; si `valid_count` es cero, `percentage` es null. Los conteos de bins suman `valid_count`. En profundidad, `valid_count + missing_count` reconcilia la población filtrada; para magnitud, `missing_count` se calcula antes de aplicar `min_mag`, mientras `valid_count` y los bins corresponden a los eventos filtrados, por lo que ambos solo se reconcilian directamente cuando no se ha aplicado `min_mag`.
- Comparación: recuento del periodo live, duración en días, recuento diario promedio del replay del 2025 (denominador 365 días incluyendo ceros), tasa diaria del periodo, y `daily_rate_difference`/`daily_rate_ratio` solo si el baseline está disponible y es mayor que cero. La diferencia es tasa actual menos histórica y el ratio es tasa actual dividida por histórica. La cobertura de intervalos históricos completados debe cubrir todo 2025 para marcar baseline disponible; la cobertura parcial se representa como no disponible, no como promedio anual ni cero.

### Estado del servicio

- `status`: `ok` cuando API, PostgreSQL y esquema requerido están disponibles; `unavailable` en caso contrario.
- `last_ingestion`: epoch ms UTC o null.
- HTTP 200 para `ok`; HTTP 503 para `unavailable`.
- Nunca incluir DSN, credenciales, secretos, tokens ni mensaje interno de excepción.

### Estado de lectura del cliente

- `last_success`: resultado/metadata de la última lectura correcta conservada.
- `last_attempt`: éxito o fallo de la consulta más reciente; fallos incluyen tipo de error legible (timeout, red, HTTP) y tiempo de intento.
- Ante fallo tras éxito, no sustituir la última respuesta por vacío; señalar que puede estar desactualizada y mostrar `last_ingestion` si está disponible.

## Reglas comunes de validación

1. Interpretar límites ISO 8601 con offset; normalizarlos a UTC. Rechazar fecha inválida, `start >= end`, magnitud no finita, país con forma inválida y parámetros desconocidos mediante error de validación, no corregir ni ignorar silenciosamente.
2. Intervalos temporales son semiabiertos `[start, end)`. Una hora pertenece al bucket UTC que comienza en la hora exacta anterior.
3. `min_mag` excluye registros con magnitud null de los resultados filtrados; el `missing_count` de magnitud los cuenta en el periodo y ámbito geográfico elegidos antes de aplicar ese filtro. Los porcentajes de bins usan como denominador `valid_count` del ámbito filtrado para esa distribución; ausentes se excluyen del porcentaje. El `missing_count` de magnitud es una métrica diagnóstica pre-filtro y puede no compartir población con `valid_count` cuando existe `min_mag`.
4. Estadísticas calculan sobre el conjunto persistido de eventos actuales, nunca sobre las Features devueltas por una consulta truncada.
5. País null se cuenta en un grupo explícito; no se elimina como join inner.
6. Revisiones antiguas y versiones históricas no referenciadas por `event_current` no afectan ni consulta ni agregación.
7. Errores HTTP de solicitudes inválidas o fallidas usan un envelope JSON común con código y mensaje público; detalles opcionales solo identifican parámetro y motivo, sin incluir el valor recibido ni información interna. Salud conserva su cuerpo contractual específico.
