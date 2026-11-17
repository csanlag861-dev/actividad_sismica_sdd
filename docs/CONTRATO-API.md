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
      "country_name": "España"
    }
  }]
}
```

`generated`: generación de esta respuesta; no implica que la ingesta siga activa. `last_ingestion`: última consulta correcta a USGS. Fechas en milisegundos Unix UTC. Coordenadas en orden longitud, latitud, profundidad (km). Usa `null`, nunca NaN/Infinity, para magnitud, profundidad o país desconocidos. Geometría válida obligatoria en este endpoint.

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

## Acceso desde Netlify

Configura CORS en FastAPI para la lista de orígenes HTTPS exactos de publicación y `http://localhost:4200` durante desarrollo; métodos GET y OPTIONS, y cabecera `ngrok-skip-browser-warning`. No uses comodines ni credenciales. Una lista de producción ausente o vacía solo autoriza el origen de desarrollo. Un origen malformado, comodín, no HTTPS o con ruta/query/fragmento invalida la configuración: el servicio debe reportar el error explícitamente y no iniciar con una lista parcial. Un origen no autorizado no recibe permiso CORS para que el navegador lea la respuesta.

El encabezado de ngrok evita su página intermedia cuando es aplicable; no autentica al usuario. No incluir secretos en config.json. Añade timeout y manejo de errores en el frontend.

El transporte del navegador aplica un timeout de 15 segundos y distingue errores HTTP accesibles de fallos de transporte sin respuesta accesible. Un rechazo de transporte puede deberse a red o CORS; el navegador puede no permitir distinguir su causa. Tras un fallo, una nueva consulta iniciada por el consumidor puede ejecutarse; si tiene éxito, sustituye la lectura conservada y limpia el error y el estado de posible desactualización. No se realizan reintentos automáticos ni refresco periódico.

## Transporte y contenedores

La API es un servicio Docker, igual que productor, consumidor, Kafka y PostgreSQL. Uvicorn escucha en `0.0.0.0:8000`. ngrok termina el HTTPS público y gestiona el certificado; la API recibe HTTP local. El frontend utiliza la URL HTTPS del túnel. Desde otro contenedor de la misma red, el agente se conecta a `http://api:8000`; desde el host, al puerto publicado.
