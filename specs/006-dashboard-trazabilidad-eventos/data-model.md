# Data Model: Dashboard de actividad y trazabilidad sísmica

## Evento actual de la API

Representación GeoJSON ya existente y devuelta por `GET /api/eventos`.

| Campo | Tipo | Regla |
|---|---|---|
| `Feature.id` | string | Identificador estable del evento; ya existente y no duplicado dentro de `traceability`. |
| `geometry` | Point | Coordenadas longitud/latitud válidas; profundidad opcional en kilómetros según el contrato vigente. |
| `properties.time` | entero | Tiempo de ocurrencia en milisegundos Unix UTC. |
| `properties.updated` | entero | Tiempo de la versión actual en milisegundos Unix UTC; identifica la fecha de versión en la ficha. |
| `properties.traceability` | objeto, opcional para clientes que aceptan APIs anteriores | Nuevo grupo de procedencia descrito abajo. La API actualizada lo devuelve en cada feature. |

### Trazabilidad

| Campo | Tipo público | Origen / validación |
|---|---|---|
| `mode` | `"live" \| "replay"` | Modo de la versión persistida; no se infiere a partir de la fecha o la fuente. |
| `source` | string o `null` | Identificador de fuente revisado para exposición pública. No incluir URL original, query string, fragmento ni secretos. Valor desconocido/no seguro se serializa como `null`. |
| `ingested_at` | entero en milisegundos Unix UTC o `null` | Fecha de ingesta de esa versión; no confundir con `properties.updated` ni con la última ingesta global. |
| `ingestion_run_id` | UUID como string o `null` | Identificador de ejecución asociado a esa versión; nunca exponer otra información de la ejecución. |

No se devuelven `original_payload`, `original_feature`, `payload_sha256`, archivos de archivo ni valores internos de error. Los campos actuales de `EventVersion` satisfacen el modelo; no se necesita migración.

## Resultado estadístico

Se consume sin cambios ni recálculo a partir de `StatisticsResponse`:

- `period` y `filters` describen el resultado estadístico efectivo.
- `hourly_counts.buckets` contiene inicio UTC y conteo por hora.
- `distributions.magnitude` y `distributions.depth_km` conservan unidad, ancho, bins, `valid_count`, `missing_count` y porcentajes.
- Un porcentaje nulo no se convierte en cero. Los conteos de cero siguen siendo resultados válidos.

El resumen del dashboard refleja estos valores; no establece una relación uno-a-uno con la colección de eventos si sus periodos o filtros efectivos difieren.

## Estado de interfaz

Se reutilizan los snapshots del estado compartido:

- Eventos y estadísticas tienen estado de carga, error y última respuesta válida, con filtros, periodo, hora de lectura y posible desactualización.
- La selección del mapa identifica un evento por `Feature.id`; la ficha muestra atributos y trazabilidad de esa misma feature.
- Respuesta anterior sin `properties.traceability`: mostrar la información de trazabilidad como no disponible sin invalidar los demás atributos o la colección.
- Distribuciones y serie vacías son estados de éxito sin datos; no crear buckets para completar el gráfico ni valores ficticios.

## Marca visual

`frontend/public/icon.png` es un recurso estático compartido para favicon e identidad global. No forma parte de los datos del evento ni de las respuestas de API.
