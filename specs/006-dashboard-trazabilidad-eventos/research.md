# Research: Dashboard de actividad y trazabilidad sísmica

## Alcance e insumos

Se revisaron la especificación aclarada, la constitución, `docs/CONTRATO-API.md`, `docs/README.md`, el sistema visual, los contratos de `005-panel-sismico` y la implementación actual del dashboard, mapa, ficha, consultas, gráficos y rutas de API.

## Decisiones

### Integración del dashboard

- **Decision**: Componer el mapa existente `EventMapComponent` y la ficha `EventDetailComponent` en el dashboard, y presentar ahí recuentos horarios UTC y distribuciones de magnitud/profundidad en un resumen con equivalentes tabulares accesibles. Aprovechar ECharts y patrones de `StatisticsViewComponent`; no recalcular agregados en el navegador.
- **Rationale**: El frontend ya mantiene una única consulta compartida de eventos y estadísticas, refresca cada 60 segundos y contiene el mapa, la ficha y cuatro gráficos en la vista analítica. La integración reutiliza la fuente y el contexto de filtros existentes.
- **Alternatives considered**: Añadir un endpoint o duplicar las consultas en el dashboard (innecesario y con riesgo de divergencia); redibujar el mapa o recalcular distribuciones del subconjunto de features (duplicaría lógica y podría usar datos truncados).

### Trazabilidad compacta en la API

- **Decision**: Añadir un objeto `properties.traceability` a cada feature de `GET /api/eventos`, con modo, fuente pública segura, fecha de ingesta e identificador de ejecución. La identidad existente `Feature.id` y la versión existente `properties.updated` completan el identificador/fecha de versión solicitados. La nueva interfaz tolera que el objeto falte en una API anterior y marca los campos como no disponibles.
- **Rationale**: `EventVersion` ya almacena `mode`, `event_id`, `updated_at`, `source`, `ingested_at` e `ingestion_run_id`. La consulta puede serializarlos desde la versión actual sin cambiar la base ni añadir un endpoint. La ampliación preserva los campos y semánticas actuales de GeoJSON.
- **Alternatives considered**: Un miembro GeoJSON `provenance` como hermano de `properties` es válido como extensión según RFC 7946 §6.1, pero se elige `properties.traceability` para agrupar la metadata de ficha con los atributos que el cliente ya presenta sin alterar la forma de feature vigente. Publicar el payload de origen o su hash es innecesario para la ficha y aumenta exposición; migrar base de datos no hace falta; crear otra ruta duplica la consulta; hacer obligatorios los campos nuevos en el validador del cliente frente a un backend anterior rompe compatibilidad durante despliegues escalonados.

### Exposición segura de la fuente

- **Decision**: Publicar solo un identificador de fuente revisado y estable (por ejemplo, `usgs-live` o `usgs-replay`) o un origen/ruta normalizados cuando se necesite; descartar query string, fragmento, credenciales, tokens y cualquier dato original. Si no puede construirse una fuente pública segura, exponer `null`.
- **Rationale**: Los productores actuales usan etiquetas estables para eventos (`usgs-live` y `usgs-replay`); URLs y metadatos de solicitud no son necesarios para identificar el tipo de ingesta en la ficha. Esto evita exponer parámetros que pudieran incluir secretos.
- **Alternatives considered**: Exponer la URL registrada completa o reutilizar directamente una cadena `source` no validada (puede contener valores sensibles); omitir toda procedencia (no satisface la historia de trazabilidad).

### Formato de fecha y run ID

- **Decision**: Mantener para `ingested_at` el entero en milisegundos Unix UTC y para `ingestion_run_id` el UUID existente serializado como string; tratarlo como identificador opaco en la interfaz.
- **Rationale**: RFC 3339 ofrece un formato legible e interoperable para instantes, pero cambiar a texto aquí divergiría de `properties.time`, `properties.updated` y `metadata.last_ingestion`, que ya usan milisegundos UTC y forman parte del contrato público. No se expone el registro de ejecución ni sus demás campos internos.
- **Alternatives considered**: RFC 3339 `Z` sería apropiado para un contrato nuevo sin formato histórico; convertir o duplicar el timestamp solo en este campo introduciría inconsistencia y requeriría mantener dos convenciones.

### Compatibilidad y alcance de cambios

- **Decision**: La API nueva devuelve el objeto de trazabilidad con campos ausentes como `null`; consumidores anteriores ignoran propiedades adicionales. El cliente nuevo acepta respuestas antiguas sin el objeto y presenta sus datos como no disponibles. Actualizar conjuntamente el contrato público y las pruebas de contrato.
- **Rationale**: La adición es compatible con los consumidores existentes y no oculta ni transforma fallos de lectura. La validación no debe invalidar la colección entera si el backend se despliega después que el frontend.
- **Alternatives considered**: Cambiar el envelope/forma GeoJSON, exigir migración coordinada y simultánea o tratar la ausencia del nuevo objeto como error global; ninguno aporta valor al contrato aditivo solicitado.

### Recursos visuales

- **Decision**: Reutilizar `frontend/public/icon.png` como favicon y como marca global en el encabezado/sidebar donde ayude a reconocer la aplicación. Mantener proporción, texto alternativo cuando sea imagen de contenido y no duplicarlo en cada vista.
- **Rationale**: El recurso está presente y ya fue seleccionado por el usuario como marca aprobada.
- **Alternatives considered**: Crear otro logo, incluirlo como decoración en cada página o generar variantes no solicitadas.

## Evidencia local

- [`frontend/src/app/features/dashboard/dashboard-page.component.ts`](../../../frontend/src/app/features/dashboard/dashboard-page.component.ts) y su plantilla implementan el resumen actual.
- [`frontend/src/app/shared/map/event-map.component.ts`](../../../frontend/src/app/shared/map/event-map.component.ts) contiene el mapa reutilizable; [`frontend/src/app/features/events/event-detail.component.ts`](../../../frontend/src/app/features/events/event-detail.component.ts) contiene la ficha actual.
- [`frontend/src/app/features/analytics/statistics-view.component.ts`](../../../frontend/src/app/features/analytics/statistics-view.component.ts) y su plantilla ya representan las series/bins de la API con tablas alternativas.
- [`frontend/src/app/core/state/query-state.service.ts`](../../../frontend/src/app/core/state/query-state.service.ts) administra respuestas independientes y actualiza datos periódicamente.
- [`backend/src/observatorio/api/queries.py`](../../../backend/src/observatorio/api/queries.py), [`backend/src/observatorio/api/routes.py`](../../../backend/src/observatorio/api/routes.py) y [`backend/src/observatorio/models/events.py`](../../../backend/src/observatorio/models/events.py) confirman que los valores de procedencia están asociados a la versión persistida.
- [`backend/tests/contract/test_api_contract.py`](../../../backend/tests/contract/test_api_contract.py) es el lugar existente para verificar la respuesta pública.

## Fuentes externas

No se requiere dependencia ni protocolo externo nuevo. Referencias consultadas:

- [RFC 7946 §6.1: GeoJSON foreign members](https://www.rfc-editor.org/rfc/rfc7946.html#section-6.1) permite miembros de extensión; se documenta como alternativa compatible, aunque este diseño agrupa trazabilidad dentro de `properties`.
- [RFC 3339 §5.6](https://www.rfc-editor.org/rfc/rfc3339.html#section-5.6) define timestamps con offset explícito/UTC; se conserva el formato epoch existente del contrato del proyecto para evitar incompatibilidad.
- [RFC 3986](https://www.rfc-editor.org/rfc/rfc3986) informa la normalización de URI; el contrato elegido expone etiquetas estables y evita publicar URI de consulta o credenciales.
- [OWASP SSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html) respalda no hacer dereferencia del origen público desde la ficha ni aceptar URLs arbitrarias como destinos de red.

La compatibilidad aditiva y la protección de datos se concretan en los contratos del proyecto y se validan con pruebas de contrato.
