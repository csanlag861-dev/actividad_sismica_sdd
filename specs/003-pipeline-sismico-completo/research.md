# Research: Pipeline sísmico completo H5

## Contexto inspeccionado

- `ROADMAP.md`, R13–R17 y el criterio del Hito H5.
- `docs/ENUNCIADO.md`, secciones 4–7; `docs/FAQ-ALUMNADO.md`, preguntas 10–16 y 18–21; `docs/FUENTES-Y-LICENCIAS.md`.
- Implementación existente en `backend/src/observatorio/producer/`, `consumer/`, `models/`, `db/` y `migrations/`; pruebas en `backend/tests/`; `compose.yaml`.
- No se identificaron dudas de alcance pendientes de la especificación. La investigación se centra en adaptar el diseño a las decisiones ya fijadas y a los huecos detectables en el código existente.

## Decisiones

### D1. Mantener el pipeline actual y extenderlo

**Decision**: Reutilizar los cinco servicios Compose, módulos Python, modelos SQLAlchemy, migraciones Alembic y pruebas actuales. No añadir servicios ni cambiar el stack.

**Rationale**: El repositorio ya tiene extracción live con reintentos, publicación con confirmación, consumidor Kafka, persistencia transaccional, cuarentena por posición, catálogo Natural Earth, tablas de versiones y estado actual, y aislamiento `live`/`replay`. El trabajo H5 debe cerrar brechas y cubrir casos de aceptación, no rehacer la infraestructura.

**Alternatives considered**:
- Crear un servicio independiente de backfill: rechazado porque el productor ya ofrece un modo histórico y el enunciado requiere los mismos cinco servicios, no una arquitectura adicional.
- Sustituir Kafka/PostgreSQL o introducir un motor de procesamiento: rechazado por las restricciones del proyecto y la falta de necesidad para el volumen del ejercicio.

### D2. Preservar respuesta y Feature GeoJSON originales

**Decision**: Antes de extraer o transformar Features, el productor archiva la respuesta GeoJSON completa de USGS con SHA-256 y una referencia durable desde cada `IngestionRun`. El mensaje Kafka transporta además la Feature original completa, sin reconstruirla a partir de `id`, `properties` y `geometry`. Runs distintos conservan metadatos independientes aunque sus respuestas compartan archivo por contenido idéntico.

**Rationale**: `live.py` y `replay.py` actualmente reconstruyen una parte de la Feature, lo que puede perder campos originales como el tipo GeoJSON, `bbox` u otros atributos. La procedencia exige que se pueda explicar el dato fuente y sus transformaciones.

**Alternatives considered**:
- Guardar únicamente los campos usados por el consumidor: rechazado porque no conserva el original suficiente para auditoría y transformación futura.
- Guardar solo la respuesta agregada sin una referencia por run y Feature: rechazado porque no permite seguir cada versión procesada hasta su extracción.

**Retention alignment**: Esta ampliación sigue FR-003 y la decisión aceptada de conservar cada original distinto mientras exista el dato procesado correspondiente. Las respuestas idénticas deduplican por hash, pero nunca se colapsan ejecuciones; la limpieza se permite únicamente cuando ningún run del archivo conserva versiones procesadas o cuarentenas dependientes y queda registrada. No implica retención ilimitada de copias idénticas.

### D3. Identidad de versión y reemplazo de contenido same-version

**Decision**: Mantener `(mode, event_id, updated_at)` como identidad única de versión procesada y un único `EventCurrent` por evento/modo, que siempre apunta al timestamp más reciente. Calcular el hash determinista del Feature completo y guardarlo únicamente en `EventVersionSource`, cuya clave es la identidad de versión sin hash y cuya cardinalidad es cero o una fila por versión. Si llega el mismo `event_id` y `updated_at` con otro hash, reemplazar atómicamente los campos de esa versión y su único Feature/hash/procedencia por el payload entrante; no crear una segunda versión ni una cuarentena por conflicto. La magnitud puede subir o bajar porque prevalece el payload recibido más recientemente. Timestamps distintos siguen siendo versiones de historial y no eventos distintos. Para filas heredadas sin fuente completa, no calcular hash sobre payload parcial; aceptar el entrante como fuente completa y actualizar los campos conocidos.

**Rationale**: La clave natural ya distingue revisiones y el estado actual debe ser monotónico. La nueva regla del producto evita multiplicar versiones para contenido distinto con el mismo timestamp y garantiza que el hash y Feature aceptados describan el mismo payload. El ledger de publicación registra ACKs por hash, pero solo su último hash determina si se omite una entrega; así un hash antiguo que reaparece después de otro contenido se reenvía para respetar el orden de observación. El ledger no define identidad de terremoto.

**Alternatives considered**:
- Crear una segunda fila `EventVersion` o `EventVersionSource` para el mismo timestamp: rechazado porque convierte distintas observaciones del mismo terremoto en varias versiones/eventos.
- Añadir el hash a la clave primaria de `EventVersionSource`: rechazado porque permitiría varias fuentes aceptadas para una misma identidad de versión.
- Calcular huellas desde payloads heredados parciales: rechazado porque presentaría evidencia incompleta como exacta.

### D4. Validación y exclusiones antes del estado actual

**Decision**: El consumidor valida que el mensaje tenga una Feature GeoJSON de tipo Point, identidad y timestamps interpretables, y coordenadas finitas y dentro de rango. `properties.type` distinto de `earthquake` se conserva como exclusión durable con razón explícita; otras entradas no procesables se guardan en cuarentena con bytes del mensaje y posición Kafka. Los valores opcionales nulos y valores válidos aunque inusuales se conservan.

**Rationale**: El consumidor ya valida rangos y fechas, pero no comprueba el tipo GeoJSON/Point ni filtra de forma explícita tipos de evento. La política evita puntos inventados y mantiene el resultado auditable sin convertir nulos o magnitudes inusuales en errores.

**Alternatives considered**:
- Descartar en el productor todo evento no sísmico: rechazado como único control porque el consumidor debe ser el límite de calidad y dejar evidencia durable.
- Rellenar campos faltantes o descartar valores inusuales: rechazado por la constitución y las reglas de calidad del enunciado.

### D5. Asignación por catálogo sin ambigüedad

**Decision**: Mantener Natural Earth como catálogo, validar su hash y unicidad de `ADM0_A3`, cargar sus atributos de identificación, y asignar país solo cuando haya exactamente una coincidencia espacial. Sin coincidencia, frontera o varias coincidencias no inequívocas, el país es desconocido («Sin país asignado»).

**Rationale**: El cargador y la función geográfica ya comprueban hash, códigos únicos y `covers`; la función retorna `None` ante cero o múltiples resultados, que implementa la decisión aclarada. El modelo de país actual solo conserva el nombre y debe ampliarse con los atributos requeridos para el enriquecimiento.

**Alternatives considered**:
- Elegir la primera entidad coincidente: rechazado porque depende del orden del archivo y atribuye una ubicación ambigua arbitrariamente.
- Asignar por `place` o país más cercano: rechazado expresamente por enunciado y constitución.

### D6. Histórico por intervalos, con staging durable y reanudación

**Decision**: Extraer el año configurado por intervalos mensuales en UTC; si un resultado alcanza el límite de 20.000, subdividir el intervalo y repetir hasta que cada respuesta quede bajo el límite. Guardar cada respuesta original en el almacenamiento persistente compartido con live antes de publicarla, junto a parámetros, límites, fecha, huella y conteos; marcar cada intervalo pendiente, completo o fallido y reanudar sin duplicar efectos. La publicación reutiliza el envelope y consumidor común bajo modo/topic `replay`.

**Rationale**: La extracción actual pagina con `offset` y retiene todos los eventos en memoria, pero no deja checkpoints por intervalo ni archivos originales recuperables. El enunciado pide subdividir en caso de límite y reutilizar el histórico; el roadmap pide recuperar huecos live superiores a 24 horas. El staging persistente evita perder la extracción si falla el envío a Kafka o el consumidor.

**Alternatives considered**:
- Paginar siempre una respuesta grande con `offset`: no elegido como estrategia primaria porque el requisito exige subdividir los intervalos cuando se alcanza el máximo; la deduplicación por identidad se mantiene como protección adicional ante límites inclusivos.
- Mantener todo el año en memoria y publicar al final: rechazado por la recuperación, el crecimiento de memoria y la pérdida de avance ante fallos.
- Convertir la ausencia del feed live en borrado: rechazado; la ventana móvil no es una fuente de eliminaciones.

### D7. Orden transaccional del consumidor

**Decision**: Persistir versión, evento actual o rechazo/exclusión en una transacción PostgreSQL; confirmar el offset Kafka solo después del commit. Repeticiones posteriores se resuelven por clave única y huella.

**Rationale**: Ya existe `handle_message` con persistencia antes de `commit`, y el FAQ especifica entrega al menos una vez con escrituras idempotentes, no una transacción distribuida Kafka–PostgreSQL.

**Alternatives considered**:
- Confirmar offset antes de escribir en PostgreSQL: rechazado porque puede perder mensajes al fallar la base.
- Añadir transacción distribuida Kafka/PostgreSQL: rechazado explícitamente por el enunciado y desproporcionado para esta práctica.

### D8. Verificación y límites

**Decision**: Probar algoritmos y transacciones en SQLite para rapidez, y validar comportamiento real de offsets, migraciones, volumen persistente, reinicio y flujo con Kafka/PostgreSQL mediante Compose. No definir SLA de disponibilidad o latencia de procesamiento que los documentos de referencia no exigen.

**Rationale**: El Hito H5 fija frecuencia de sondeo y resultados de corrección, no un objetivo de throughput de servicio. Pruebas unitarias no demuestran durabilidad de los servicios reales.

**Alternatives considered**:
- Exigir disponibilidad 24/7 o una latencia p95 fija: rechazado porque la defensa usa recursos locales y el enunciado no impone esos objetivos.
- Validar todo solo con SQLite: rechazado porque no comprueba reanudación y commits Kafka con servicios reales.

### D9. Cadencia live y reintentos

**Decision**: Programar sondeos con reloj monotónico cada 60 segundos y tolerancia de 5 segundos, sin solicitudes solapadas. Cada intento HTTP vence a los 8 segundos; se permiten hasta 3 reintentos con esperas de 1, 2 y 4 segundos para errores de red, HTTP 429/5xx y respuestas no interpretables. Otros HTTP 4xx terminan el ciclo sin reintentar. Si un ciclo supera su siguiente deadline, registrar el intervalo perdido, no hacer catch-up en ráfaga y retomar en el próximo deadline futuro. El run fallido queda explícito y no reemplaza el último exitoso.

**Rationale**: El timeout y los reintentos acotados terminan antes del siguiente intervalo nominal, permiten recuperación de fallos transitorios sin tormentas de solicitudes y dejan errores persistentes visibles.

## Decisiones derivadas para el plan de implementación

1. Añadir ledger de publicación por hash y un registro único de Feature fuente por identidad de versión; reemplazar en-place same-version y tratar filas heredadas incompletas como huella desconocida sin fabricar fingerprints.
2. Archivar cada respuesta GeoJSON completa antes de extraerla, conservar la Feature completa en la envoltura y reforzar la validación del envelope/Feature/Point/tipo de evento.
3. Ampliar el catálogo `country` con los atributos Natural Earth que se usarán en análisis; nunca modificar el GeoJSON fuente.
4. Añadir estado y metadatos por intervalo histórico y reutilizar el almacenamiento persistente de respuestas originales live; publicar de manera incremental y recuperable.
5. Añadir pruebas exactas para secuencia de control H5, reemplazo same-version, exclusión de tipos, fronteras ambiguas, fallo entre envío/confirmación y reanudación de intervalos.

## Referencias

- `ROADMAP.md`, tareas R13–R17.
- `docs/ENUNCIADO.md`, secciones 4.1–4.3, 5–7.
- `docs/FAQ-ALUMNADO.md`, preguntas 10–16 y 18–21.
- `docs/FUENTES-Y-LICENCIAS.md`, catálogo Natural Earth y fuentes USGS.
- Código examinado: `backend/src/observatorio/producer/{live,publisher,replay,replay_source,source}.py`, `backend/src/observatorio/consumer/{processor,validation,geography,main}.py`, modelos, migraciones y pruebas unit/integration.
