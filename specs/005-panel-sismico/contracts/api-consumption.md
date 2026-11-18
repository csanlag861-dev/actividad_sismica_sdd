# Contrato de consumo de API del panel

Este contrato enlaza la UI con las operaciones existentes; no añade ni modifica rutas, parámetros o esquemas. La fuente normativa es [`docs/CONTRATO-API.md`](../../../docs/CONTRATO-API.md) y el contrato detallado de R18–R20 es [`specs/004-api-consultas-estadisticas/contracts/query-api.md`](../../004-api-consultas-estadisticas/contracts/query-api.md).

## Configuración

- Cargar `public/config.json`, que contiene solo `apiBaseUrl`.
- El cliente adjunta `/api/...` al URL base conforme al cliente existente.
- Publicado: URL HTTPS. Desarrollo: `http://localhost:4200` permitido por CORS del backend. No cookies, tokens ni secretos.
- Mantener timeout de transporte de 15 segundos para cada solicitud y separar error HTTP accesible de fallo de transporte sin respuesta accesible.

## Solicitudes

| Endpoint | Momento | Parámetros |
|---|---|---|
| `GET /api/eventos` | Al abrir, al cambiar filtros, cada 60 s y al reintentar explícitamente | `start`, `end`, `min_mag`, `country_id` según filtros activos. No mandar `start`/`end` para el periodo móvil default de últimas 24 h. |
| `GET /api/estadisticas` | En el mismo ciclo de eventos | Los mismos filtros y semánticas que la consulta de eventos. |
| `GET /api/salud` | Al abrir, cada 60 s y al reintentar explícitamente | Ninguno. |

Para un periodo personalizado, enviar inicio inclusive y fin exclusive como ISO 8601 con offset UTC `Z`, con `start < end`. País se envía como identificador de catálogo exacto; no se mandan valores desconocidos, filtros regionales ni filtros de tipo.

## Respuestas y presentación

- **Eventos**: validar `FeatureCollection`; usar `features`, metadata, geometría, propiedades y nulos como están definidos. Sustituir la capa ante cada éxito. `metadata.generated` es generación, no salud; `last_ingestion` es la última ingesta correcta. Un array vacío es éxito.
- **Estadísticas**: usar periodo y filtros declarados por la respuesta; graficar buckets, distribuciones y comparación directamente con unidades y valores ausentes. No recalcular estadísticas en el cliente.
- **Salud**: HTTP 200 con estado `ok` y `last_ingestion`, o HTTP 503 con estado `unavailable`. Una fecha de ingesta antigua no cambia el status.
- **Truncamiento**: respetar `metadata.truncated` y los metadatos de total/continuación solo si la API los declara; la UI informa limitación y no calcula totales de universo sobre la muestra. El servicio desplegado actualmente no aplica límite ni paginación. Si una versión futura trunca resultados, el contrato de API exige declarar el total y un mecanismo de paginación; hasta que se documenten sus parámetros, la UI no inventa controles ni solicitudes de continuación.
- **Errores**: respetar los status HTTP y envelope común para eventos/estadísticas; la ruta de salud conserva su cuerpo específico. No convertir errores en colección vacía, cero, baseline no disponible o promedio cero.

## Coordinación

Cada refresh envía eventos, estadísticas y salud como solicitudes independientes. Aplicar una misma huella de filtros a eventos y estadísticas. Si una respuesta llega tras haber cambiado el filtro, descartarla. Un éxito nuevo reemplaza únicamente la instantánea del recurso correspondiente; un fallo conserva la última instantánea de ese recurso con señal de posible desactualización. No se promete atomicidad entre endpoints; mostrar los periodos efectivos que cada uno devuelve.

El cliente no ejecuta retry automático ni programa el intervalo de actualización. El consumidor Angular mantiene el ciclo acordado de 60 segundos y ofrece acción explícita de reintento.
