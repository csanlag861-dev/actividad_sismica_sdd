# Contrato: trazabilidad de eventos

## Ruta

La ampliación corresponde a la ruta ya existente `GET /api/eventos`. No añade ruta, parámetro, autenticación ni permiso. El contrato completo de filtros, errores, geometría y metadatos sigue en [`docs/CONTRATO-API.md`](../../../docs/CONTRATO-API.md).

## Propiedades nuevas

Cada feature de la respuesta actualizada añade `properties.traceability`:

```json
{
  "type": "Feature",
  "id": "event-id",
  "geometry": {
    "type": "Point",
    "coordinates": [-3.7, 40.4, 12]
  },
  "properties": {
    "updated": 1793110000000,
    "traceability": {
      "mode": "live",
      "source": "usgs-live",
      "ingested_at": 1793113140000,
      "ingestion_run_id": "UUID"
    }
  }
}
```

El ejemplo es ilustrativo; los datos reales provienen de la versión de evento actual. Los campos vigentes `Feature.id` y `properties.updated` proporcionan la identidad y fecha de versión respectivamente; no se duplican en el objeto nuevo.

| Campo | Tipo | Semántica |
|---|---|---|
| `mode` | `"live"` o `"replay"` | Modo de procedencia de la versión. |
| `source` | `"usgs-live"`, `"usgs-replay"` o `null` | Etiqueta estable y segura de fuente. Solo se publican estos valores permitidos; cualquier otro valor persistido se representa como `null`. No contiene query string, fragmento, credenciales o secretos. |
| `ingested_at` | entero en milisegundos Unix UTC o `null` | Instante de ingesta de esta versión. |
| `ingestion_run_id` | UUID string o `null` | Ejecución de ingesta que produjo la versión. |

`mode` y `ingestion_run_id` proceden de la versión actual persistida; no se infieren de la fuente. `ingested_at` no se confunde con `properties.updated` ni con la última ingesta global.

## Compatibilidad y privacidad

- La respuesta conserva el tipo `FeatureCollection`, identificadores, propiedades, geometría, metadata y filtros actuales.
- Los consumidores antiguos pueden ignorar `properties.traceability`.
- El cliente nuevo admite que el objeto falte al consultar una API anterior y presenta todos sus datos como no disponibles; no rechaza por ello el evento.
- Si el objeto está presente, debe contener `mode`, `source`, `ingested_at` e `ingestion_run_id` con los tipos y valores permitidos indicados arriba. No se aceptan formas malformadas como si fueran trazabilidad válida.
- El payload original, el hash, la ruta de archivo, credenciales, tokens, secretos, parámetros de solicitud y fragmentos nunca se exponen.
- No se modifica la respuesta de `GET /api/estadisticas` ni su cálculo de horarios y distribuciones.

## Verificación de contrato

Una prueba de contrato debe verificar para un evento de muestra que:

1. `Feature.id` y `properties.updated` conservan sus significados existentes.
2. `properties.traceability` refleja los valores asociados con esa versión actual.
3. Las fechas son UTC en milisegundos, `ingestion_run_id` tiene formato UUID, una fuente no permitida se serializa como `null` y los datos ausentes se expresan como `null`.
4. No aparecen `original_payload`, hash ni datos internos/sensibles.
5. Una colección vacía y el envelope de error existente no cambian.
