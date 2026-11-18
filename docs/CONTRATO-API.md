# Contrato mínimo de la API

## GET /api/eventos

Devuelve HTTP 200, `Content-Type: application/json` y un GeoJSON `FeatureCollection`. Sin eventos: `features: []`, no un error. Cada evento aparece una sola vez, con su versión actual. Por defecto devuelve terremotos ocurridos en las últimas 24 horas.

```json
{
  "type": "FeatureCollection",
  "metadata": {
    "generated": 1793113200000,
    "last_ingestion": 1793113140000,
    "mode": "live",
    "count": 1,
    "truncated": false
  },
  "features": [{
    "type": "Feature",
    "id": "ejemplo-ficticio",
    "geometry": {"type": "Point", "coordinates": [-3.7, 40.4, 12]},
    "properties": {
      "mag": 3.2,
      "magType": "ml",
      "place": "Ejemplo ficticio",
      "depth_km": 12,
      "time": 1793109600000,
      "updated": 1793110000000,
      "country_id": "ESP",
      "country_name": "España",
      "traceability": {
        "mode": "live",
        "source": "usgs-live",
        "ingested_at": 1793113140000,
        "ingestion_run_id": "02dfad0c-2c13-431c-95fb-4bdb4d253e23"
      }
    }
  }]
}
```

`generated`: generación de esta respuesta; no implica que la ingesta siga activa. `last_ingestion`: última consulta correcta a USGS. Fechas en milisegundos Unix UTC. Coordenadas en orden longitud, latitud, profundidad (km). Usa `null`, nunca NaN/Infinity, para magnitud, profundidad o país desconocidos. Geometría válida obligatoria en este endpoint.

`properties.traceability` añade la procedencia compacta de la versión actual. `mode` es `live` o `replay`; `source` solo se publica como `usgs-live` o `usgs-replay`, y cualquier otro valor se representa como `null`; `ingested_at` es la fecha de ingesta de esa versión en milisegundos Unix UTC; `ingestion_run_id` es el UUID de la ejecución. Los valores ausentes se representan como `null`. `Feature.id` sigue siendo el identificador del evento y `properties.updated` su fecha de versión. Las respuestas anteriores pueden carecer del objeto; los clientes deben tolerarlo. No se exponen payloads originales, hashes, credenciales, secretos, parámetros de consulta ni fragmentos de URL. Esta ampliación no modifica los campos existentes ni la semántica de `GET /api/estadisticas`.

Filtros a implementar: `start` (ISO8601, inclusive), `end` (ISO8601, exclusive), `min_mag` y `country_id`. El mapa inicial aún no envía filtros; corresponde al alumnado añadirlos. La magnitud nula no cumple un filtro `min_mag` y debe contabilizarse por separado.

Para limitar el tamaño, la API puede aplicar un máximo documentado de puntos. Si trunca, debe indicar `truncated: true`, el total completo y un mecanismo de paginación. El panel final deberá mostrarlo y no calcular estadísticas globales sobre una muestra truncada. El componente inicial espera una colección pequeña y completa.

Las solicitudes cuya sintaxis no se pueda interpretar deben responder HTTP 400. Los parámetros desconocidos o con valores inválidos deben responder HTTP 422. Los errores de consulta usan el envelope JSON común definido abajo; no deben convertirse en una colección vacía.

## Otros endpoints a implementar

| Ruta | Resultado |
|---|---|
| GET /api/salud | Estado API y fecha de última ingesta; no credenciales |
| GET /api/estadisticas | Conteos por hora UTC/país, distribuciones y comparación histórica |

Los filtros de estadísticas deben equivaler a los del mapa. Cada resultado debe indicar periodo, filtros, unidad y registros sin valor. Si la base falla, devuelve un error explícito; no cero eventos como si fuera un resultado válido.

Cada distribución informa `valid_count` y `missing_count`. Los bins semiabiertos se alinean a múltiplos enteros de su anchura: `[k*w, (k+1)*w)`, con `w=0.5` para magnitud y `w=10 km` para profundidad. Los porcentajes se calculan como `100 * bin_count / valid_count`; los valores ausentes no forman parte del denominador ni de los bins y se informan por separado. Si `valid_count` es cero, los porcentajes son `null`. Los conteos de bins suman `valid_count`. El `missing_count` de magnitud se calcula en el ámbito temporal/geográfico antes de `min_mag`, mientras `valid_count` y los bins usan los eventos que quedan tras todos los filtros; con `min_mag`, ambos campos pueden describir poblaciones distintas.

### Errores de consulta

Las estadísticas históricas comparan tasas diarias, no totales de periodos de distinta duración. Si existe cobertura completa de 2025 y el promedio histórico es mayor que cero, se incluyen `daily_rate_difference` (tasa actual menos tasa histórica) y `daily_rate_ratio` (tasa actual dividida por tasa histórica). Con baseline no disponible o promedio histórico cero, estos campos se omiten.

Las respuestas de error de eventos y estadísticas usan un envelope JSON común con códigos y mensajes estables:

```json
{
  "error": {
    "code": "invalid_request",
    "message": "Request parameters are invalid",
    "details": [
      {"parameter": "start", "reason": "must include a timezone offset"}
    ]
  }
}
```

`details` es opcional y solo contiene nombres de parámetros y motivos seguros; no debe repetir valores sensibles ni incluir SQL, trazas o excepciones internas. Los parámetros inválidos/desconocidos usan HTTP 422; la sintaxis de solicitud no parseable usa HTTP 400. Los fallos internos usan HTTP 500 y la indisponibilidad de base/esquema HTTP 503, manteniendo el mismo envelope en consultas. `GET /api/salud` conserva su cuerpo específico `{"status":"unavailable","last_ingestion":null}` en HTTP 503. Una respuesta vacía o con ceros solo representa una consulta exitosa.

| HTTP | `error.code` | `error.message` |
|---|---|---|
| 400 | `malformed_request` | `Request syntax is malformed` |
| 422 | `invalid_request` | `Request parameters are invalid` |
| 500 | `internal_error` | `The request could not be completed` |
| 503 en consultas | `dependency_unavailable` | `A required service is unavailable` |

### GET /api/salud

Con la API, la base de datos y la revisión de esquema disponibles, responde HTTP 200:

```json
{
  "status": "ok",
  "last_ingestion": 1793113140000
}
```

`last_ingestion` es la fecha de la última ingesta live correcta en milisegundos Unix UTC, o `null` si todavía no existe. La antigüedad de esa fecha no cambia el estado de salud. Si la base de datos o el esquema requerido no están disponibles, responde HTTP 503 con este cuerpo específico:

```json
{
  "status": "unavailable",
  "last_ingestion": null
}
```

La respuesta de salud no contiene credenciales ni detalles internos.

### GET /api/estadisticas

Una respuesta HTTP 200 incluye el periodo y filtros aplicados, las series por hora UTC, los recuentos por país, las distribuciones y la comparación con el baseline. Cada distribución expresa su unidad, anchura de bin, recuento válido usado como denominador, ausentes y bins semiabiertos:

```json
{
  "period": {
    "start": "2026-11-17T11:00:00Z",
    "end": "2026-11-17T13:00:00Z"
  },
  "filters": {
    "min_mag": 4.0,
    "country_id": null
  },
  "hourly_counts": {
    "unit": "events/hour (UTC)",
    "missing_count": 0,
    "buckets": [
      {"start": "2026-11-17T11:00:00Z", "count": 2},
      {"start": "2026-11-17T12:00:00Z", "count": 1}
    ]
  },
  "country_counts": {
    "unit": "events",
    "missing_count": 1,
    "buckets": [
      {"country_id": null, "country_name": "Sin país asignado", "count": 1},
      {"country_id": "ESP", "country_name": "España", "count": 2}
    ]
  },
  "distributions": {
    "magnitude": {
      "unit": "magnitude",
      "bin_width": 0.5,
      "valid_count": 3,
      "missing_count": 0,
      "buckets": [
        {
          "min_inclusive": 4.0,
          "max_exclusive": 4.5,
          "count": 2,
          "percentage": 66.6666666667
        },
        {
          "min_inclusive": 4.5,
          "max_exclusive": 5.0,
          "count": 1,
          "percentage": 33.3333333333
        }
      ]
    },
    "depth_km": {
      "unit": "km",
      "bin_width": 10,
      "valid_count": 2,
      "missing_count": 1,
      "buckets": [
        {
          "min_inclusive": 0,
          "max_exclusive": 10,
          "count": 1,
          "percentage": 50.0
        },
        {
          "min_inclusive": 10,
          "max_exclusive": 20,
          "count": 1,
          "percentage": 50.0
        }
      ]
    }
  },
  "historical_comparison": {
    "baseline_period": {
      "start": "2025-01-01T00:00:00Z",
      "end": "2026-01-01T00:00:00Z"
    },
    "baseline_days": 365,
    "baseline_available": true,
    "current_count": 3,
    "current_period_days": 0.0833333333,
    "current_daily_average": 36.0,
    "historical_daily_average": 2.0,
    "unit": "events/day",
    "daily_rate_difference": 34.0,
    "daily_rate_ratio": 18.0
  }
}
```

Si no hay cobertura histórica completa para el año y la población de magnitud solicitada, `baseline_available` es `false` y `historical_daily_average` es `null`; las diferencias y el ratio diario se omiten. Una distribución con `valid_count` igual a cero devuelve `buckets: []`; cualquier porcentaje calculable con denominador cero es `null` (no se emiten bins sin eventos). Cuando existe baseline pero su promedio es cero, también se omiten la diferencia y el ratio. Los fallos de consulta conservan el envelope de error común descrito arriba, no una agregación con ceros.

## Acceso desde Netlify

Configura CORS en FastAPI para la lista de orígenes HTTPS exactos de publicación y `http://localhost:4200` durante desarrollo; métodos GET y OPTIONS, y cabecera `ngrok-skip-browser-warning`. No uses comodines ni credenciales. Una lista de producción ausente o vacía solo autoriza el origen de desarrollo. Un origen malformado, comodín, no HTTPS o con ruta/query/fragmento invalida la configuración: el servicio debe reportar el error explícitamente y no iniciar con una lista parcial. Un origen no autorizado no recibe permiso CORS para que el navegador lea la respuesta.

El encabezado de ngrok evita su página intermedia cuando es aplicable; no autentica al usuario. No incluir secretos en config.json. Añade timeout y manejo de errores en el frontend.

El transporte del navegador aplica un timeout de 15 segundos y distingue errores HTTP accesibles de fallos de transporte sin respuesta accesible. Un rechazo de transporte puede deberse a red o CORS; el navegador puede no permitir distinguir su causa. Tras un fallo, una nueva consulta iniciada por el consumidor puede ejecutarse; si tiene éxito, sustituye la lectura conservada y limpia el error y el estado de posible desactualización. No se realizan reintentos automáticos ni refresco periódico.

## Transporte y contenedores

La API es un servicio Docker, igual que productor, consumidor, Kafka y PostgreSQL. Uvicorn escucha en `0.0.0.0:8000`. ngrok termina el HTTPS público y gestiona el certificado; la API recibe HTTP local. El frontend utiliza la URL HTTPS del túnel. Desde otro contenedor de la misma red, el agente se conecta a `http://api:8000`; desde el host, al puerto publicado.
