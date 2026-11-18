# Operación del pipeline sísmico H5

## Configuración

Copiar `.env.example` a `.env`, reemplazar `POSTGRES_PASSWORD` por un secreto
aleatorio local y ajustar únicamente los valores de entorno necesarios. Compose
falla al resolver la configuración si no se proporciona la contraseña. No
guardar `.env` ni secretos en Git. Las variables principales son:

| Variable | Predeterminado | Uso |
|---|---:|---|
| `POSTGRES_PASSWORD` | Obligatorio, sin valor predeterminado | Contraseña runtime de PostgreSQL, compartida con los servicios backend. |
| `USGS_URL` | Feed GeoJSON `all_day` | Fuente live; las credenciales de una URL se eliminan de la procedencia persistida. |
| `POLL_SECONDS` | `60` | Periodo live basado en reloj monotónico. |
| `POLL_TOLERANCE_SECONDS` | `5` | Retraso máximo aceptado antes de registrar un deadline perdido. |
| `USGS_TIMEOUT_SECONDS` | `8` | Timeout por solicitud live. |
| `SOURCE_ARCHIVE_DIR` | `/data/source-archives` | Directorio del volumen persistente compartido por live e histórico. |
| `REPLAY_INTERVAL_SECONDS` | `2` | Pausa opcional entre Features históricas; `0` desactiva la pausa. |
| Retención Kafka | `168` horas | Retención limitada del log; los datos procesados e históricos se conservan en PostgreSQL y en el archivo de origen. |

Compose monta el volumen nombrado `source_archives` en el productor. El modo
live y el comando de histórico usan el mismo servicio y, por tanto, el mismo
volumen. No usar `docker compose down -v` si se deben conservar archivos y
checkpoints.

## Productor live

```sh
docker compose up --build -d
docker compose logs --since 5m productor
```

El productor realiza una consulta inmediata y continúa con deadlines de 60
segundos. Si una consulta supera su deadline, no se solapa ni lanza una ráfaga
catch-up: registra los deadlines perdidos y continúa con el siguiente futuro.
Cada solicitud live vence a los 8 segundos. Red, HTTP 429/5xx y respuestas
GeoJSON no interpretables se reintentan hasta tres veces con pausas de 1, 2 y
4 segundos; otros HTTP 4xx fallan el ciclo sin reintento.

Cada respuesta completa se escribe primero en un archivo temporal y se mueve
atómicamente a su ruta SHA-256. El `IngestionRun` se vincula al archivo antes
de extraer Features. Respuestas idénticas reutilizan un archivo, pero cada
consulta conserva su run, tiempos, status HTTP, recuento y URL saneada.
Después, el productor publica la Feature GeoJSON íntegra en `quakes.live` y
guarda el ACK en PostgreSQL solo tras el ACK de Kafka.

## Carga histórica y recuperación de huecos

Carga predeterminada: 2025 UTC, ámbito mundial, `eventtype=earthquake`,
`minmagnitude=4`, orden temporal ascendente:

```sh
docker compose run --rm productor python -m observatorio.producer.replay \
  --year 2025 --min-magnitude 4 --event-type earthquake --interval-seconds 0
```

Para recuperar un hueco live superior a 24 horas, indicar el inicio UTC
inclusivo y el fin UTC exclusivo:

```sh
docker compose run --rm productor python -m observatorio.producer.replay \
  --start 2025-04-01T00:00:00Z --end 2025-04-03T00:00:00Z \
  --min-magnitude 4 --event-type earthquake --interval-seconds 0
```

Cada intervalo mensual o explícito mantiene filtros, intentos, status HTTP,
límites, recuentos, estado y archivo asociado. Si una respuesta alcanza 20.000
Features se archiva y el intervalo se subdivide recursivamente; una respuesta
que no pueda subdividirse con seguridad falla explícitamente. Las fronteras
inclusivas de USGS pueden repetir eventos; la identidad/hash de publicación y
el consumidor idempotente evitan duplicar versiones. Los mensajes históricos
van a `quakes.replay` con `mode=replay` y usan el mismo consumidor y validación
que live.

Si el proceso se interrumpe tras archivar una respuesta, repetir exactamente
los mismos filtros y límites reanuda el intervalo desde el archivo verificado.
Los intervalos completos no vuelven a consultarse. Un fallo de Kafka deja el
intervalo incompleto y el siguiente intento vuelve a publicar desde el archivo;
el ledger de ACK evita repetir una entrega ya confirmada. La ausencia de un
evento en el feed móvil live no elimina su versión histórica.

## Procedencia, deduplicación y compatibilidad

- `source_archive` guarda SHA-256, ruta, tamaño, fuente y fecha; `deleted_at`
  registra una limpieza auditable.
- `ingestion_run` conserva modo, URL saneada, filtros y resultado de la
  extracción. `ingestion_interval` mantiene checkpoints históricos.
- `event_version_source` guarda una Feature completa, su huella canónica y la
  ejecución actualmente aceptada para cada `(mode, event_id, updated_at)`.
- `published_payload` registra ACKs por hash. Solo se omite una publicación si
  su huella coincide con la última confirmada para esa identidad; si llega
  `A`, luego `B` y después `A`, la última `A` vuelve a publicarse.
- Las filas heredadas de `published_version` no reciben huellas inventadas.
  Las versiones antiguas sin Feature completa se completan con el primer
  payload íntegro recibido, sin calcular un hash sobre datos parciales.
- Los datos inválidos y las exclusiones no sísmicas se conservan en
  `quarantine` con posición Kafka y bytes originales. El offset solo se
  confirma después del commit PostgreSQL.

## Retención y limpieza

Los originales distintos se conservan mientras existan versiones o cuarentenas
procesadas dependientes. Las respuestas idénticas comparten archivo. La limpieza
conservadora disponible elimina solo archivos de consultas exitosas vacías,
sin dependencias procesadas:

```sh
docker compose run --rm productor python -m observatorio.producer.archive
```

Los archivos de respuestas con registros no se eliminan mediante esa limpieza
automática; permanecen disponibles para auditoría y recuperación. Si se aplica
una política de retención que retire datos procesados, verificar primero que
ninguna versión, cuarentena ni intervalo pendiente/fallido dependa del archivo;
registrar la fecha de eliminación en `source_archive.deleted_at`. No borrar
archivos manualmente mientras Kafka todavía pueda entregar mensajes pendientes.

## Migraciones y comprobaciones

Las migraciones aditivas mantienen las filas existentes y no calculan hashes
retroactivos. La revisión vigente añade el índice temporal
`ix_event_version_mode_event_time` a la tabla de versiones.
Después de levantar una instalación actualizada:

```sh
docker compose ps
docker compose logs --since 5m api productor consumidor
docker compose run --rm --no-deps --entrypoint python consumidor -m pytest -q tests
```

Kafka y PostgreSQL continúan internos a la red Compose; no se publican puertos
de esos servicios en el host.
