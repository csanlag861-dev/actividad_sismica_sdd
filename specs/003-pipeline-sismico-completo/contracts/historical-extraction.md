# Contract: Extracción y carga histórica USGS

## Alcance predeterminado

- Servicio USGS FDSN Event Catalog, respuesta GeoJSON FeatureCollection.
- Un año UTC, predeterminado 2025, ámbito mundial, `eventtype=earthquake`, `minmagnitude=4`, orden `time-asc`.
- Consulta inicial por meses con inicio incluido y fin exclusivo en el intervalo lógico.
- Máximo tratado por respuesta: 20.000 Features. Si la respuesta alcanza ese límite, dividir el intervalo en subintervalos y consultar cada uno; no aceptar una respuesta potencialmente truncada como completa.
- Cada evento conserva su Feature original y se publica en el topic aislado `quakes.replay` con `mode=replay`, usando el mismo consumidor y reglas de persistencia que live.

## Registro de lote e intervalo

Cada carga histórica crea un `IngestionRun` y un `IngestionInterval` por consulta hoja. Live e histórico reutilizan el registro `SourceArchive`: respuestas con bytes idénticos comparten un archivo, pero cada extracción mantiene su propio run e intervalo. El registro incluye:

- URL/fuente y todos los filtros efectivos, sin credenciales.
- Límites UTC del intervalo solicitado; límites inclusivos de la fuente se ajustan al particionar y cualquier solapamiento residual se deduplica por identidad de evento/versión.
- Intentos, status HTTP, hora de solicitud y archivo, total recibido, versiones únicas y total publicado.
- Referencia a `SourceArchive`, que contiene la ruta de archivo GeoJSON original y SHA-256 verificada.
- Estado `pending` → `archived` → `publishing` → `complete`; cualquier fallo registra `failed` con error y conserva la última etapa durable.

Una subconsulta no se marca `complete` hasta que sus Features archivadas hayan sido publicadas o reconocidas como duplicados ya confirmados. Cualquier error de descarga, JSON, archive, Kafka o persistencia detiene el intervalo afectado con estado explícito; no se informa el lote como completo.

## Archivo fuente y reanudación

- Escribir cada respuesta original en volumen persistente antes de publicar; escribir de forma atómica (temporal seguido de rename) y registrar SHA-256 antes de marcar `archived`.
- Mantener metadatos/checkpoints por intervalo, no solo una lista de eventos en memoria. Tras reiniciar, verificar el checksum y continuar intervalos pendientes/fallidos sin volver a crear efectos persistidos.
- No borrar datos históricos porque desaparezcan del feed live. Los archivos originales distintos quedan disponibles mientras exista alguna versión o cuarentena procesada dependiente; deduplicar copias idénticas sin fusionar runs y documentar la limpieza de archivos sin dependencias.
- El archivo no debe incluir datos sintéticos ni cambiar los timestamps originales. La hora de extracción/ingesta se registra aparte.
- Si un intervalo aún devuelve el máximo tras subdividir hasta una unidad temporal que no pueda dividirse de forma segura, fallar explícitamente y conservar el archivo/diagnóstico; no truncar ni declarar cobertura completa.

## Fallos y deduplicación

| Situación | Resultado |
|---|---|
| Repetición de una consulta o intervalo ya completo | Mantener conteos; no republicar versiones con la misma identidad y huella. |
| Respuesta con límites solapados | Deduplicar por `(mode, event_id, updated_at, payload_sha256)`; las colisiones de igual identidad y distinto hash van a cuarentena. |
| Falla tras archivar y antes de publicar | Reanudar desde archivo verificado y publicar. |
| Falla tras ACK pero antes de guardar el ACK | El reenvío es posible; consumidor idempotente impide duplicar efectos. |
| Falla del consumidor | Kafka conserva mensajes dentro de su retención; el intervalo no se marca completo hasta poder verificar resultados. |
| Parada live mayor de 24 horas | Ejecutar extracción histórica para el periodo ausente con filtros documentados; no usar la ausencia del feed como borrado. |

Los conteos de extracción y de persistencia se informan por separado: una respuesta o solapamiento puede contener varias entregas de la misma versión.
