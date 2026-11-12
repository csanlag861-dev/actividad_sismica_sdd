# Research: Arranque y procesamiento del stack Compose

## Alcance

El repositorio contiene la documentación del proyecto y el frontend de apoyo, pero todavía no tiene backend Python ni configuración Compose. El diseño debe respetar el requisito de cinco servicios separados y la decisión del usuario de usar SQLAlchemy para el mapeo y Alembic para la evolución del esquema. Esta entrega implementa el pipeline live/replay y el almacenamiento, pero excluye deliberadamente todos los endpoints HTTP.

## Decisión: runtime y acceso a PostgreSQL

**Decision**: Adoptar Python 3.12 como baseline práctico; utilizar SQLAlchemy 2.x con `AsyncEngine`/`AsyncSession` y `asyncpg` desde el backend de esquema, el productor y el consumidor basado en aiokafka. Crear una sesión por unidad de trabajo; no compartir una `AsyncSession` entre tareas concurrentes. FastAPI/Uvicorn se incorporarán cuando se implementen los endpoints en una entrega posterior.

**Rationale**: El productor y el consumidor realizan trabajo asíncrono. El driver asíncrono evita bloquear sus bucles de eventos durante operaciones de base de datos. Python 3.12 es una base conservadora para el proyecto; no se anuncia como mínimo de compatibilidad y las versiones exactas deberán fijarse al crear `requirements.txt`.

**Alternatives considered**:

- SQLAlchemy síncrono y un driver síncrono: válido para aplicaciones síncronas, pero puede bloquear el bucle de eventos del consumidor y requiere separar con cuidado las llamadas de base de datos.
- Mezclar sesiones síncronas y asíncronas: descartado por aumentar configuraciones y patrones sin necesidad en un stack asíncrono.

**Sources**:

- [SQLAlchemy asyncio](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [SQLAlchemy asyncpg dialect](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#asyncpg)
- [asyncpg](https://magicstack.github.io/asyncpg/current/)

## Decisión: Alembic y propiedad de inicialización

**Decision**: SQLAlchemy define las clases mapeadas. Alembic es el único camino normal para crear o cambiar el esquema: las revisiones candidatas se generan con autogenerate, se revisan y se guardan en control de versiones; al arrancar, el proceso backend del servicio Compose `api` ejecuta `alembic upgrade head`, comprueba el esquema y permanece activo para poder informar readiness. No inicia Uvicorn ni sirve HTTP.

**Rationale**: El usuario asignó al backend la responsabilidad del esquema y el proyecto exige exactamente cinco servicios, mientras que los endpoints se difieren. Ejecutar la cadena de migraciones desde el contenedor `api` respeta ambos límites y evita un sexto servicio. El proceso se mantiene activo para que Compose pueda supervisar PostgreSQL y el estado de migración; ante un error no se declara saludable y deja evidencia en logs.

**Alternatives considered**:

- Un sexto servicio Compose de migraciones que se ejecuta una vez: patrón habitual para despliegues con varias réplicas, pero incompatible con los cinco servicios exactos y con la propiedad de inicialización asignada por el usuario al backend.
- `Base.metadata.create_all()` como inicialización normal: descartado porque no conserva un historial versionado ni reemplaza las migraciones de Alembic.
- Ejecutar autogenerate automáticamente en producción: descartado; Alembic advierte que los scripts autogenerados son candidatos, pueden omitir o interpretar mal cambios y requieren revisión.

**Sources**:

- [Alembic tutorial y plantilla asyncio](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Alembic cookbook: integración asyncio](https://alembic.sqlalchemy.org/en/latest/cookbook.html)
- [Alembic autogenerate: límites y revisión](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)

## Decisión: disponibilidad de dependencias y Kafka

**Decision**: Usar la red de servicio de Compose y DNS, un broker Kafka oficial Apache en modo KRaft de un nodo y direcciones internas estables `kafka:9092` y `postgres:5432`. El listener anunciado a clientes será `kafka:9092`; el listener de control KRaft no se publica al host. Fijar versiones de imagen y configurar factores de replicación de un nodo a `1`.

**Rationale**: Los clientes deben poder resolver las direcciones que Kafka les devuelve después del bootstrap. Los nombres de servicio sobreviven a la recreación de contenedores, al contrario que las IP. El modo combinado de un nodo es suficiente para desarrollo local y no necesita ZooKeeper. El servicio `api` publica su puerto solo en loopback del host; Kafka y PostgreSQL no tienen mapeos `ports`.

**Alternatives considered**:

- `localhost` o IP de contenedor para conexiones internas: descartado; no identifica de forma estable al otro servicio.
- Broker con ZooKeeper o clúster de varios nodos: descartado para esta práctica local; añadiría infraestructura no requerida.
- Imágenes flotantes `latest`: descartadas porque reducen la reproducibilidad.

**Sources**:

- [Docker Compose networking](https://docs.docker.com/compose/how-tos/networking/)
- [Docker Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/)
- [Compose service reference: depends_on](https://docs.docker.com/reference/compose-file/services/#depends_on)
- [Apache Kafka Docker image](https://hub.docker.com/r/apache/kafka)
- [Apache Kafka Docker examples](https://github.com/apache/kafka/blob/trunk/docker/examples/README.md)
- [Kafka quickstart](https://kafka.apache.org/quickstart)
- [PostgreSQL container healthcheck guidance](https://docs.docker.com/compose/how-tos/startup-order/)

## Decisión: healthchecks y recuperación

**Decision**: Usar `pg_isready` para PostgreSQL, una comprobación de protocolo de cliente para Kafka y comprobaciones de aplicación para productor, consumidor y el proceso backend `api`. Compose usa `depends_on: condition: service_healthy` para el orden de arranque inicial. Además, los clientes reintentan/reconectan con espera progresiva y logs sin secretos durante interrupciones posteriores. `api` solo está saludable tras aplicar/verificar las migraciones y conectar a PostgreSQL; no se utiliza una ruta `/api/salud`.

**Rationale**: Compose espera por la disponibilidad inicial, pero el orden de arranque no protege contra una caída posterior ni reconecta por sí mismo a los clientes. El productor también necesita PostgreSQL para recuperar y persistir el estado de versiones confirmadas por Kafka. Productor y consumidor esperan además a que `api` haya terminado las migraciones.

**Alternatives considered**:

- Comprobar solo que el proceso del contenedor existe: descartado porque no confirma que el broker o la base acepten conexiones.
- Confiar solo en `depends_on` en forma corta: descartado porque indica orden, no disponibilidad.
- Añadir una red Docker interna aislada para todos los servicios: no se requiere para cumplir el alcance y puede complicar la salida del productor hacia USGS; basta no publicar puertos de infraestructura.

**Sources**:

- [Docker Compose startup order and healthchecks](https://docs.docker.com/compose/how-tos/startup-order/)
- [Docker Compose networking and service DNS](https://docs.docker.com/compose/how-tos/networking/)
- [Docker port publishing](https://docs.docker.com/engine/network/port-publishing/)
- [Docker Compose internal networks](https://docs.docker.com/compose/how-tos/networking/#internal-networks)

## Decisión: procesamiento live, geográfico e idempotente

**Decision**: El productor consulta `all_day.geojson` aproximadamente cada 60 segundos, registra cada `ingestion_run`, compara `id`/`updated` con `published_version`, publica eventos con `event_id` como clave y espera el ACK antes de actualizar la publicación persistida. El consumidor valida el original, integra puntos con el catálogo Natural Earth mediante `ADM0_A3`, conserva revisiones y actualiza `event_current` solo al recibir una versión más reciente. Los eventos sin una única coincidencia geográfica quedan con país nulo; no se asigna por proximidad. La cuarentena guarda el mensaje y el motivo antes de confirmar el offset.

**Rationale**: Sigue las secciones de extracción, calidad, integración geográfica, modelado y pruebas de aceptación del enunciado. El procesamiento al menos una vez, junto con claves únicas y escritura transaccional, permite reenvíos sin duplicar efectos.

**Alternatives considered**:

- Confirmar offsets antes de escribir en PostgreSQL: descartado porque puede perder mensajes tras un fallo.
- Rechazar eventos marítimos o imputarles el país más cercano: descartado por las reglas de procedencia y calidad del proyecto.
- Guardar solo la última fila sin historial ni original: descartado porque impide auditar revisiones y transformaciones.

**Sources**:

- [Enunciado: extracción, calidad, integración, modelado y aceptación](../../docs/ENUNCIADO.md)
- [Guía de entregables: catálogo Natural Earth y procesamiento transaccional](../../docs/Guia-entregables-observatorio-sismico.md)
- [README: frecuencia del feed reciente](../../README.md)

## Decisión: reproducción histórica

**Decision**: El productor replay obtiene una selección del catálogo USGS (por defecto, año 2025, global, magnitud ≥4, tipo earthquake), la ordena por tiempo de ocurrencia y la publica en un topic distinto con `mode=replay`. Reutiliza el consumidor normal. Se conserva `event_time`; `ingested_at` registra el tiempo de reproducción.

**Rationale**: La guía exige una reproducción acelerada por Kafka, con fechas originales, identificación de replay y aislamiento de live, incluyendo duplicados y revisiones controladas.

**Alternatives considered**:

- Inyectar datos directamente en PostgreSQL: descartado porque no demuestra el pipeline Kafka.
- Cambiar la fecha original para que aparezca como actual: descartado porque falsifica la procedencia temporal.

**Sources**:

- [Enunciado: reproducción histórica y pruebas de aceptación](../../docs/ENUNCIADO.md)
- [FAQ: reproducción acelerada y aislamiento](../../docs/FAQ-ALUMNADO.md)
- [Guía de entregables: flujo de reproducción](../../docs/Guia-entregables-observatorio-sismico.md)

## Decisiones aún para la implementación

No hace falta que el usuario especifique otra tecnología para producir el plan. Se fijarán versiones exactas de dependencias e imágenes al crear los archivos reproducibles. El parche concreto de Kafka se elegirá de una versión mantenida compatible con aiokafka; PostgreSQL se fijará en una serie mantenida. Las tareas deberán verificar las versiones exactas juntas antes de congelarlas y comprobar si `frontend/public/datos/paises.geojson` está presente; si no está, se restaurará la copia Natural Earth prevista por el enunciado y se registrará su procedencia.
