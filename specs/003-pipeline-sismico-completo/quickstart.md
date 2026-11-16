# Quickstart: Validación del pipeline H5

## Prerrequisitos

- Docker Desktop con Compose v2 y espacio para PostgreSQL, Kafka y el archivo histórico.
- Acceso de red a USGS para validar ingesta real. Las pruebas unitarias no dependen de Internet.
- Configuración por entorno; no guardar secretos en Git ni en el frontend.

## 1. Construir y levantar los servicios

Desde la raíz del repositorio:

```powershell
Copy-Item .env.example .env
# Edita .env y sustituye POSTGRES_PASSWORD por un secreto aleatorio local.
docker compose up --build -d
docker compose ps
```

Esperado: PostgreSQL, Kafka, API/bootstrap, productor y consumidor están `running`; API/bootstrap aplica migraciones, carga el catálogo y permanece healthy. Una dependencia temporalmente no disponible se reintenta y no se marca sana prematuramente.

Ejecutar pruebas unitarias y de integración existentes:

```powershell
docker compose run --rm --no-deps --entrypoint python consumidor -m pytest -q tests
```

Esperado: las pruebas no dejan contenedores, servicios externos ni datos de prueba permanentes. Para validar cambios de esquema, arrancar el Compose y comprobar que la revisión Alembic esperada y sus tablas están aplicadas.

## 2. Verificar el productor live

Esperar una consulta live y revisar logs:

```powershell
docker compose logs --since 5m productor
```

Esperado: las consultas se programan con reloj monotónico cada 60 segundos, con hasta 5 segundos de tolerancia y sin solaparse. Cada intento vence a los 8 segundos; errores de red, HTTP 429/5xx y respuestas no interpretables permiten hasta 3 reintentos, espaciados 1, 2 y 4 segundos. HTTP 4xx distintos de 429 no se reintentan. Si se pierde un deadline, se registra y no se ejecutan consultas de recuperación en ráfaga; se retoma en el siguiente deadline futuro. El fallo de un ciclo queda registrado sin borrar el run válido anterior. Cada respuesta GeoJSON completa se archiva antes de extraer eventos; el run registra SHA-256 y referencia al archivo. Cada publicación lleva el envelope de [pipeline-message.md](./contracts/pipeline-message.md), clave de evento y Feature USGS completa.

Una consulta repetida no publica otra vez una versión idéntica. Si dos respuestas tienen bytes idénticos, verificar que comparten un archivo pero mantienen runs y metadatos separados. La ausencia de un evento en la ventana live posterior no elimina su versión persistida.

## 3. Ejecutar el caso de control de versiones

Usar una prueba unitaria de integración con base aislada para procesar, en orden:

1. E1 en `updated=10:05`.
2. Repetición idéntica de E1 en `10:05`.
3. Revisión de E1 en `10:09`.
4. Reenvío atrasado de E1 en `10:05`.
5. Evento E2 en `10:12`.

Esperado después de cada operación: estado final de **2 eventos actuales** y **3 versiones distintas**, E1 actual en `10:09`; el segundo mensaje y la versión atrasada repetida no duplican filas ni hacen retroceder el estado.

### Reemplazo de contenido same-version

Enviar en orden tres payloads para la misma identidad `(mode, event_id, updated_at)`: Feature A, una Feature B con contenido distinto y Feature A otra vez.

- Se mantiene una sola fila `EventVersion` y una sola `EventVersionSource` para esa identidad; cada hash distinto reemplaza en-place los datos, Feature, hash y procedencia por los del payload entrante.
- La tercera entrega de A se publica aunque A se hubiera publicado antes de B; al terminar, la fila contiene A.
- Un reenvío consecutivo idéntico al último payload no cambia datos ni duplica efectos.
- No se crea una cuarentena por cambios de contenido con la misma identidad. Una versión con otro `updated` sí permanece como fila de historial y solo se vuelve actual si su timestamp es el más reciente.

Para validar compatibilidad, crear una versión previa sin registro de Feature fuente completo y procesar su versión completa: el payload entrante actualiza los campos conocidos y se registra como primera fuente completa verificable. No se asigna al payload heredado una huella calculada desde datos incompletos.

## 4. Probar validación, exclusión y cuarentena

Enviar, en una prueba aislada, fixtures con: Feature válida y campos opcionales nulos; `properties.type` distinto de `earthquake`; geometry distinto de Point; coordenadas fuera de rango o no finitas; fecha ausente o inválida.

Esperado:

- La Feature válida conserva sus nulos y coordenadas sin inventar datos.
- El tipo excluido queda registrado con razón durable y no aparece en estado actual.
- Cada entrada no procesable mantiene bytes/mensaje original, motivo y posición Kafka.
- El offset solo avanza tras el commit de resultado o cuarentena.
- Si la base falla, no se confirma el offset; al reanudar, el mensaje se procesa sin efectos duplicados.

## 5. Verificar enriquecimiento geográfico

Ejecutar casos de prueba contra la copia de Natural Earth:

| Punto de control | Resultado |
|---|---|
| Dentro de España (`-3.7, 40.4`) | País asignado `ESP` |
| Océano (`-150, 0`) | `country_id = null`, «Sin país asignado» |
| Frontera o varias coincidencias | `country_id = null`, «Sin país asignado» |

Esperado: hash del GeoJSON coincide con su manifiesto; `ADM0_A3` es único; el original no se modifica y no hay asignación por cercanía o texto.

## 6. Cargar y reanudar histórico

Cuando la extracción histórica esté implementada, ejecutar el lote predeterminado:

```powershell
docker compose run --rm productor python -m observatorio.producer.replay --year 2025 --min-magnitude 4 --event-type earthquake --interval-seconds 0
```

La extracción y sus checkpoints se definen en [historical-extraction.md](./contracts/historical-extraction.md). Esperado:

- Año completo procesado con límites UTC y filtros anotados.
- Respuestas GeoJSON y checksums persistidos antes de publicar.
- Respuestas idénticas reutilizan un mismo archivo, sin fusionar runs; un archivo solo se elimina cuando ningún dato procesado dependa de él y la limpieza queda registrada.
- Intervalos que alcanzan 20.000 respuestas se subdividen; no se acepta truncamiento.
- El consumidor común procesa los mensajes en `quakes.replay` con modo aislado.
- Repetir el comando o reiniciar durante la carga no duplica eventos/versiones ni elimina intervalos completados.

Para simular recuperación, detener consumidor durante una carga de prueba controlada, reiniciarlo y comprobar que el intervalo solo se marca `complete` cuando todos sus registros se hayan confirmado o deduplicado.

## 7. Recuperar un hueco live superior a 24 horas

Ejecutar una carga de catálogo para el intervalo UTC faltante con filtros y origen registrados. Esperado: el backfill conserva las fechas originales y su modo/procedencia, los eventos ya observados se deduplican por versión, y ningún evento preexistente se borra por su ausencia del feed.

## Registro de validación ejecutado

Validación realizada en Linux con un entorno virtual Python y una pila Compose aislada para no interrumpir la pila de desarrollo que ya estaba activa:

```sh
cd backend
/tmp/actividad-sismica-venv/bin/python -m pytest -q tests
```

Resultado: `51 passed`. La misma suite ejecutada dentro de la imagen del consumidor también terminó con `51 passed`. Incluye los casos de versiones, validación/cuarentena, offsets, catálogo geográfico, archivos y checkpoints históricos.

La pila aislada se inició como `actividad-sismica-h5`, con nombres de contenedor únicos temporales para los cinco servicios:

```sh
docker compose -f compose.yaml -f compose.validation.yaml -p actividad-sismica-h5 up --build -d
docker compose -f compose.yaml -f compose.validation.yaml -p actividad-sismica-h5 ps
```

Los cinco servicios quedaron healthy y el bootstrap alcanzó Alembic `0006_ingestion_intervals`. El productor live archivó una respuesta de 195 Features; el consumidor procesó los mensajes y persistió versiones y estado actual en PostgreSQL.

Se ejecutó el lote anual configurado por defecto y, después, se repitió para comprobar que los checkpoints completos evitan una segunda publicación:

```sh
docker compose -f compose.yaml -f compose.validation.yaml -p actividad-sismica-h5 exec -T productor \
  python -m observatorio.producer.replay --year 2025 --min-magnitude 4 --event-type earthquake --interval-seconds 0
```

Resultado: 12 intervalos mensuales archivados y completados, 18.242 mensajes replay publicados; al repetir el comando, el productor informó que la consulta ya tenía checkpoints completos y publicó 0 mensajes. También se probó `--start 2025-01-01T00:00:00Z --end 2025-01-02T00:00:00Z`: archivó 60 Features y la repetición no publicó mensajes. El override temporal de Compose se retiró al terminar esta validación.

## Limpieza

Detener los servicios de validación:

```powershell
docker compose down
```

No usar `docker compose down -v` para conservar datos. Solo eliminar volúmenes o archivos de prueba creados expresamente para una ejecución desechable y después de verificar su ruta.
