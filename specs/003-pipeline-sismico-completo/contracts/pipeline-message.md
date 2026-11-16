# Contract: Mensaje interno del pipeline

## Alcance

Contrato entre productor, Kafka y consumidor para el modo `live` y la carga histórica `replay`. No constituye un endpoint público ni cambia `docs/CONTRATO-API.md`; el servicio de consulta queda fuera de H5.

## Transporte

| Propiedad | Regla |
|---|---|
| Codificación | JSON UTF-8. |
| Topics | `quakes.live` para el feed reciente; `quakes.replay` para histórico/reproducción aislados. |
| Key Kafka | ID de evento UTF-8 para conservar orden por evento en una partición. |
| ACK | El productor espera ACK Kafka antes de guardar el registro de publicación. |
| Offset | El consumidor confirma `offset + 1` después del commit PostgreSQL del resultado o cuarentena durable. |

## Envelope

```json
{
  "id": "usgs-event-id",
  "mode": "live",
  "source": "usgs-live",
  "ingestion_run_id": "uuid",
  "ingested_at": "2026-11-16T11:00:00+00:00",
  "published_at": "2026-11-16T11:00:01+00:00",
  "payload": {
    "type": "Feature",
    "id": "usgs-event-id",
    "properties": {
      "type": "earthquake",
      "time": 1794826800000,
      "updated": 1794826860000,
      "mag": null,
      "magType": null,
      "place": null
    },
    "geometry": {
      "type": "Point",
      "coordinates": [-3.7, 40.4, 12.0]
    }
  }
}
```

El ejemplo es ilustrativo; el productor DEBE incluir en `payload` la Feature original completa, incluidos sus miembros desconocidos, sin transformarla ni reconstruirla. En una consulta live, los timestamps fuente habituales son epoch milliseconds; el consumidor puede aceptar valores documentados en otras representaciones solo si la conversión a UTC es inequívoca. `published_at` sirve para diagnosticar publicación, no sustituye `updated` ni `ingested_at`.

Antes de extraer las Features, el productor archiva la respuesta GeoJSON completa en almacenamiento persistente. El `ingestion_run_id` del envelope identifica el run que referencia el archivo por SHA-256; ejecuciones distintas con bytes idénticos comparten el archivo, no sus metadatos de run. El consumidor conserva el run al persistir la versión o una cuarentena.

## Invariantes de datos

- `id` del envelope coincide con `payload.id`; ambos son cadenas no vacías.
- `mode` es `live` o `replay`; debe corresponder al topic de destino.
- `source`, `ingestion_run_id` y `ingested_at` identifican procedencia y ejecución. El ID de run debe poder parsearse como UUID.
- `payload` es una Feature GeoJSON con `geometry.type == "Point"` y `properties` objeto.
- Solo `properties.type == "earthquake"` se convierte en evento sísmico; otra categoría se registra como exclusión durable.
- `properties.time` y `properties.updated` deben ser interpretables; se normalizan a UTC conservando el payload original y la unidad.
- Coordenadas en orden longitud, latitud, profundidad en km. Longitud/latitud son obligatorias, finitas y dentro de rango. Profundidad, magnitud, tipo de magnitud y lugar pueden ser nulos.
- La identidad de la versión procesada es `(mode, payload.id, properties.updated)`. El hash determinista de la Feature completa excluye metadata del envelope.
- Identidad y hash iguales: duplicado sin efectos nuevos. Identidad igual y hash distinto: reemplaza en-place los campos procesados, el Feature aceptado y su hash/procedencia por los del payload entrante; no crea otra versión ni una cuarentena por conflicto. La magnitud puede aumentar o disminuir, porque se adopta el último payload recibido.
- Si una versión heredada aún no tiene un Feature completo asociado, el payload entrante reemplaza los campos conocidos y se registra como primera fuente verificable. Nunca se calcula una huella completa a partir del payload heredado parcial.
- Una versión atrasada distinta se conserva en historial, pero nunca sustituye a `EventCurrent`.

El estado actual mantiene una fila por `(mode, event_id)` y apunta a la versión con `updated_at` más reciente. Las revisiones con timestamps distintos permanecen en historial; la identidad/hash de publicación es un ledger de entregas y no una identidad adicional de terremoto.

## Condiciones de error y confirmación

| Resultado | Acción durable | Confirmar offset |
|---|---|---|
| Evento válido nuevo o revisión | Commit de `EventVersion` y estado actual según orden temporal | Sí, tras el commit |
| Duplicado idéntico | Sin nueva fila ni efectos repetidos | Sí |
| Dato inválido o tipo excluido | Commit de cuarentena con posición Kafka, bytes originales y motivo | Sí, tras el commit |
| Mismo event_id/updated con hash distinto | Reemplazar en-place la versión y su fuente aceptada dentro de la transacción | Sí, tras el commit |
| Fallo de PostgreSQL o transacción | Ningún éxito simulado ni offset adelantado | No |
| Fallo antes del ACK de Kafka | No registrar publicación como confirmada | El productor reintenta |

Los logs no deben imprimir secretos ni registrar el payload completo. Los datos fuente se conservan en almacenamiento durable con acceso de servicio, no en logs. Un archivo respuesta se retiene mientras exista una versión o cuarentena procesada asociada a alguno de sus runs; respuestas idénticas comparten archivo y la limpieza de archivos sin dependencias queda registrada.
