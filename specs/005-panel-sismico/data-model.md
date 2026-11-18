# Data Model: Panel web del observatorio sísmico

El panel no introduce persistencia ni entidades backend. Los siguientes tipos son proyecciones de respuestas API y estados efímeros de presentación.

## Entidades de consulta

### EventFilters

Representa los filtros que comparten `GET /api/eventos` y `GET /api/estadisticas`.

| Campo | Tipo | Regla |
|---|---|---|
| `start` | ISO 8601 UTC opcional | Inclusivo. Si se usa periodo personalizado debe ir junto a `end`. |
| `end` | ISO 8601 UTC opcional | Exclusivo. Debe ser posterior a `start`. |
| `min_mag` | número finito opcional | Inclusivo; los eventos con magnitud nula no satisfacen el filtro. |
| `country_id` | identificador de tres letras opcional | Coincidencia exacta con el catálogo API. Null/no asignado no se filtra como país. |

Si `start` y `end` están ausentes, se usa el intervalo API móvil de las últimas 24 horas. Los controles de hora muestran UTC; los valores personalizados se serializan con `Z`. El estado inicial no fija una ventana caducada al iniciar: cada refresco que omite ambos límites consulta de nuevo las últimas 24 horas.

El selector de país usa `ADM0_A3` y `NAME_ES` del catálogo local. El catálogo del consumidor backend utiliza `ADM0_A3` como `country_id`; los identificadores no se describen como códigos ISO universales.

### EventFeature y EventCollection

Proyección GeoJSON actual del evento live devuelto por la API.

| Campo de propiedad | Tipo | Presentación |
|---|---|---|
| `id` | string | Identidad estable de la fila/selección en la respuesta. |
| `geometry` | GeoJSON Point | Longitud, latitud; profundidad como tercera coordenada solo cuando existe. |
| `properties.mag` | número o null | Magnitud; null como desconocida, sin sustituir por cero. |
| `properties.magType` | string o null | Tipo de magnitud si está disponible. |
| `properties.place` | string o null | Descripción de ubicación entregada por API. |
| `properties.depth_km` | número o null | Profundidad en km. |
| `properties.time` | epoch ms UTC | Ocurrencia. |
| `properties.updated` | epoch ms UTC | Actualización del origen. |
| `properties.country_id` | string o null | Código de catálogo o país no asignado. |
| `properties.country_name` | string o null | Nombre entregado por API. |

`metadata` aporta `generated`, `last_ingestion`, `mode`, `count` y `truncated` según el contrato. El panel no usa un total de features truncadas como recuento global ni calcula estadísticas a partir de la lista; los agregados siempre provienen del endpoint de estadísticas.

### StatisticsResponse

Proyección del endpoint de estadísticas para el mismo `EventFilters`.

- `period`: límites efectivos de la respuesta.
- `filters`: filtros efectivos, incluidos `min_mag` y `country_id`.
- `hourly_counts`: buckets UTC con conteo y `missing_count`.
- `country_counts`: buckets con id, nombre y count; null aparece como «Sin país asignado».
- `distributions.magnitude` y `distributions.depth_km`: unidad, anchura fija de bin, recuento válido, ausentes y buckets semiabiertos; porcentajes usan `valid_count`.
- `historical_comparison`: periodo y disponibilidad del baseline 2025, tasas y campos de diferencia/ratio opcionales según reglas de contrato.

La UI conserva los datos y la metadata recibidos. No vuelve a calcular promedios, porcentajes ni tasas históricas en el navegador.

### HealthResponse

`GET /api/salud` devuelve `status` (`ok` o `unavailable`) y `last_ingestion` (epoch ms UTC o null). La edad de `last_ingestion` no determina por sí sola el estado saludable.

## Estado efímero de interfaz

### ResourceSnapshot<T>

| Campo | Descripción |
|---|---|
| `status` | `idle`, `loading`, `success` o `error`. |
| `data` | Última respuesta válida de este recurso, si existe. |
| `queryId` | Identifica filtros/ciclo de consulta que produjo `data`; permite descartar respuestas fuera de orden. |
| `filters` | Para eventos, filtros enviados en la solicitud; para estadísticas, filtros efectivos declarados por la API; para salud, null. |
| `period` | Para eventos, periodo personalizado enviado o null si se usa el periodo móvil (sus límites exactos no los declara el endpoint); para estadísticas, periodo efectivo declarado por la API; para salud, null. |
| `readAt` | Hora de lectura local. |
| `error` | Error HTTP accesible o error de transporte; ausente tras éxito. |
| `possiblyStale` | True si falla una actualización habiendo respuesta previa; no se infiere por antigüedad. |
| `request` | Contexto de la consulta más reciente, separado del periodo/filtros asociados a los datos retenidos. |

Eventos, estadísticas y salud mantienen estados separados. Un error de una consulta no borra el último éxito ni hace que datos anteriores se atribuyan a filtros nuevos. Cada vista que conserve una respuesta anterior muestra su periodo/filtros y estado de desactualización. Una consulta posterior correcta reemplaza la lectura y limpia el error de ese recurso.

### SeismicTheme

Preferencia efímera `dark | light`. Dark Mars Station es el default; el cambio persiste durante la navegación en la sesión, sin almacenar preferencia entre visitas.

### SeismicEventSelection

Identificador del evento seleccionado en mapa o tabla. La ficha muestra el mismo `EventFeature`; al desaparecer el evento de la respuesta correcta correspondiente, se limpia la selección.

## Límites

- No hay mutaciones, cuentas, permisos, comentarios, exportaciones, alertas ni datos analíticos locales.
- No se crea un estado de país inferido en frontend; si no existe `country_id`, el evento permanece sin país asignado.
- Los eventos de demo de otros materiales no se mezclan ni sustituyen respuestas reales.
- Los códigos `ADM0_A3` de Natural Earth no se presentan como ISO oficial.
