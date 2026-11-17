# Research: Consulta API y estadísticas sísmicas

## Alcance e insumos

La investigación se limita a fuentes del repositorio: la especificación aclarada, `docs/CONTRATO-API.md`, secciones 8–9 de `docs/ENUNCIADO.md`, sección 3 de `docs/README.md`, R18–R20 de `ROADMAP.md`, la constitución, modelos/migraciones actuales y configuración Compose. No se consultaron servicios externos.

## Decisiones

### Servicio y persistencia de consulta

- **Decision**: Implementar la API HTTP dentro del servicio Compose `api`, usando FastAPI/Uvicorn y la sesión asíncrona SQLAlchemy existente. Consultar PostgreSQL directamente mediante las tablas/modelos ya existentes, sin añadir tablas ni servicio.
- **Rationale**: La constitución requiere FastAPI y cinco servicios separados; los modelos actuales ya persisten evento actual, versiones, países y ejecuciones de ingesta. El repositorio carece todavía de aplicación FastAPI y dependencias de servidor en `backend/requirements.txt`.
- **Alternatives considered**: Crear otro servicio de consulta o un almacén agregado separado; se rechazan porque duplican estado y contradicen la arquitectura del proyecto.
- **Runtime integration**: El Compose actual ejecuta `observatorio.api.bootstrap` como proceso del servicio `api`; ese módulo aplica migraciones y luego queda en un bucle de espera, no sirve HTTP. La aplicación debe ejecutar bootstrap/reintentos al arrancar y Uvicorn en el mismo proceso de servicio (o proceso supervisor dentro del mismo contenedor), conservando el healthcheck de DB/esquema y los cinco servicios.

### Selección de eventos y modos

- **Decision**: `GET /api/eventos` devuelve solo `mode=live`, siempre unido desde `event_current` a la versión que referencia. Las agregaciones recientes usan también eventos live actuales; el baseline histórico lee `mode=replay` actual.
- **Rationale**: La forma del contrato muestra `metadata.mode: "live"` y requiere una sola versión actual por evento. El modo es parte de las claves persistidas para aislar replay, por lo que mezclarlo duplicaría identidades del mismo evento y contaminación del feed actual.
- **Alternatives considered**: Mezclar ambos modos o permitir un selector público de modo; se rechazan para preservar aislamiento y no ampliar filtros que el contrato no pide.

### GeoJSON con profundidad desconocida

- **Decision**: Para profundidad conocida, emitir coordenadas `[longitude, latitude, depth_km]`; cuando es null, emitir posición GeoJSON válida bidimensional `[longitude, latitude]` y añadir `properties.depth_km: null`.
- **Rationale**: Mantiene una geometría válida y expresa el desconocido explícitamente como exige el contrato y la constitución; un `null` como tercera ordenada no sería una posición válida.
- **Alternatives considered**: `null` como tercera ordenada; rechazada por invalidez de la posición GeoJSON.

### Periodo y filtros

- **Decision**: Los endpoints de eventos y estadísticas admiten `start`, `end`, `min_mag` y `country_id`. Si no se indican límites, el intervalo de ocurrencia es `[ahora - 24 horas, ahora)` en UTC. `start` es inclusivo y `end` exclusivo. Estadísticas aplica conjuntamente los mismos predicados. Magnitud desconocida no satisface `min_mag`; una búsqueda por país solo coincide con el identificador de país indicado.
- **Rationale**: Esto reproduce exactamente el contrato y sus fronteras temporales, y hace posible reconciliar eventos con agregados.
- **Alternatives considered**: Filtros de consulta diferentes por endpoint o rangos inclusivos en ambos extremos; se rechazan por producir resultados no equivalentes o solapados en ventanas consecutivas.

### Estadísticas y distribución

- **Decision**: Agrupar horas en intervalos UTC fijos `[HH:00, HH+1:00)`, basados en `event_time`; devolver buckets del intervalo consultado, incluidos los vacíos. Contabilizar eventos sin país bajo `country_id: null`/etiqueta «Sin país asignado». Distribuir magnitudes en bins de anchura 0.5 y profundidades en bins de anchura 10 km, alineados a múltiplos de la anchura y semiabiertos `[min, max)`; los valores negativos válidos se conservan. Para cada distribución, `valid_count` cuenta los eventos con valor válido de esa variable dentro de la población a la que se aplican los filtros; el porcentaje de cada bin es `100 * count / valid_count`, o null si `valid_count` es cero. Los valores ausentes se excluyen del denominador y bins, y se informan en `missing_count` por separado. Los nulos de magnitud quedan excluidos del filtro `min_mag`, pero se contabilizan aparte en su `missing_count` en el ámbito temporal/geográfico antes de ese filtro.
- **Rationale**: Una regla de intervalo explícita y estable permite pruebas exactas, comparaciones y representación posterior sin ocultar nulos ni valores negativos.
- **Alternatives considered**: Bins automáticos dependientes de cada consulta; se rechazan porque las mismas magnitudes/profundidades cambiarían de grupo entre respuestas, perjudicando la comparación. Mostrar un bin por valor exacto tampoco proporciona una distribución legible para magnitudes continuas.

### Comparación histórica

- **Decision**: La comparación predeterminada es el periodo consultado actual frente al promedio diario del año UTC 2025 (`[2025-01-01, 2026-01-01)`) en modo replay. Solo se declara baseline disponible cuando los intervalos históricos completados acreditan cobertura de todo el año. Aplicar los mismos filtros de magnitud y país, incluir días sin eventos en los 365 días del denominador y devolver recuento actual, media diaria 2025, duración actual en días, tasa actual diaria y diferencia/ratio solo cuando el promedio histórico es mayor que cero. El periodo personalizado se compara como tasa por día, no como totales de duraciones distintas.
- **Rationale**: Se alinea con el ejemplo explícito del enunciado y con la asunción de la spec; los periodos desiguales se hacen comparables, no se divide por cero y la cobertura parcial no se presenta como promedio de año completo.
- **Alternatives considered**: Comparar solo totales de periodos distintos o descartar días sin eventos; se rechazan como sesgados y contrarios al requisito.

### Salud

- **Decision**: HTTP 200 solo cuando la aplicación responde y PostgreSQL/esquema requerido están disponibles; HTTP 503 si la base o el esquema fallan. `last_ingestion` es la última `request_end` de ejecución live USGS con outcome `succeeded`, o `null`; su antigüedad no cambia estado/código.
- **Rationale**: Incorpora las respuestas del usuario en la aclaración, aprovecha el readiness y la revisión Alembic existentes, y separa operatividad de frescura de datos.
- **Alternatives considered**: Marcar no saludable por ausencia de ingesta reciente o devolver siempre HTTP 200; se rechazan porque la spec fija que la frescura se presenta por separado y que las dependencias indisponibles dan 503.

### Fallos y límites de resultados

- **Decision**: Usar HTTP 400 para sintaxis de solicitud no parseable, HTTP 422 para parámetros desconocidos o semánticamente inválidos, 503 para dependencia de base/esquema indisponible y 500 para fallo inesperado. Los errores JSON de consulta comparten envelope `{error: {code, message, details?}}`; los detalles opcionales indican campo y motivo sin repetir valores sensibles. `/api/salud` conserva su cuerpo de estado contractual. Nunca sustituir un fallo por `features: []` o conteos cero. Devolver colección completa por defecto sin límite preventivo; no introducir paginación hasta tener límite de tamaño impuesto/documentado.
- **Rationale**: El volumen del enunciado no fija tope ni throughput; no hay evidencia para introducir paginación. El contrato permite colección pequeña completa y exige transparencia si se trunca.
- **Alternatives considered**: Un límite arbitrario y paginación desde el primer cambio; se rechaza por trabajo adicional y nuevo contrato innecesario.

### CORS y cliente

- **Decision**: Autorizar `http://localhost:4200` y una lista multi-origen de orígenes HTTPS de publicación configurada explícitamente; GET/OPTIONS y cabecera de solicitud `ngrok-skip-browser-warning`; sin credenciales, cookies ni comodín. Rechazar explícitamente configuración malformada/no permitida al iniciar, sin descartar entradas inválidas ni aplicar una lista parcial; una lista de producción vacía permite solo desarrollo. Un origen no autorizado no obtiene permiso de lectura CORS. El navegador no siempre puede distinguir CORS de una falla de red, por lo que el cliente clasifica ambas como fallo de transporte sin respuesta HTTP accesible, distinto de un status no exitoso recibido de la API. El snapshot no incluye app ni toolchain frontend, por lo que se añadirá un módulo pequeño de transporte de navegador basado en `fetch`/AbortController y tests con `node:test`, sin construir UI. También se añadirá `frontend/public/config.json`, que README documenta pero no está presente en el árbol actual. El cliente configura una URL base pública sin secretos, usa 15 segundos como timeout, distingue errores de transporte/HTTP de colección vacía y conserva la última lectura correcta. Una consulta posterior iniciada por el consumidor puede recuperar el módulo: al tener éxito reemplaza datos y metadatos y limpia error/desactualización; no hay reintentos automáticos ni refresco periódico.
- **Rationale**: Coincide con contrato, README y aclaraciones. Un módulo de transporte aislado satisface R20 sin empezar R21–R23. `ngrok-skip-browser-warning` es una cabecera de petición del navegador, no un secreto ni un mecanismo de autenticación.
- **Alternatives considered**: `no-cors`, origen comodín, credenciales o umbral de ingesta inventado; se rechazan por impedir lectura correcta, reducir seguridad o afirmar una frecuencia no garantizada.

## Consecuencias y cuestiones no asumidas

- No se promete latencia, tasa de concurrencia ni disponibilidad cuantitativa del servidor: no hay objetivos en los documentos de referencia. El timeout del cliente no es un SLA.
- La distribución por bins elegida es una decisión de diseño para satisfacer “distribuciones” de manera verificable; no altera ni redondea eventos ni los valores originales.
- La consulta histórica requiere que los intervalos completados acrediten cobertura replay del año 2025; si la cobertura es parcial o no existe, el endpoint devuelve un resultado explícito de baseline no disponible y no inventa promedio cero.
- No se añaden índices/migraciones sin medición que demuestre una necesidad; la implementación debe medir con muestra real antes de proponer optimizaciones.
