# Research: Roadmap integral del Observatorio sísmico

## Alcance y fuentes

Esta investigación establece qué información debe ordenar el roadmap y cuál
es la autoridad de cada fuente. No requiere investigación tecnológica externa:
la arquitectura y las tecnologías obligatorias ya están prescritas por el
proyecto, y la feature consiste en producir un documento de planificación.

## Jerarquía documental

**Decision**: Usar la constitución del proyecto como gobierno; el enunciado
como fuente primaria de requisitos, arquitectura, aceptación, rúbrica y
entregables; `CONTRATO-API.md` como contrato del servicio de consulta; y
`FAQ-ALUMNADO.md` y `README.md` como aclaraciones operativas y ejemplos. El FAQ
no crea requisitos adicionales.

**Rationale**: Esta precedencia está establecida en la constitución y evita que
un ejemplo didáctico o una ampliación se conviertan en obligación.

**Alternatives considered**:

- Tratar los tres documentos de referencia con igual autoridad: descartado,
  porque el enunciado declara que el FAQ aclara, pero no sustituye, requisitos
  y rúbrica.
- Basar el roadmap solo en el FAQ: descartado, porque no contiene el conjunto
  autoritativo completo de requisitos.

## Secuencia de trabajo y dependencias

**Decision**: Organizar el roadmap por etapas con hitos de salida: lectura y
planificación; entorno y mapa de apoyo; análisis de fuentes y modelo;
infraestructura y persistencia mínima; procesamiento robusto; consulta;
panel y análisis; pruebas, replay y mediciones; publicación; documentación,
entrega y defensa. Permitir trabajo paralelo solo cuando las dependencias
reales lo permitan, como parte del frontend que no dependa de la API.

**Rationale**: El FAQ recomienda construir primero un recorrido vertical
pequeño y luego incorporar revisiones, catálogo, histórico y análisis. El
enunciado exige componentes Docker independientes, persistencia y un panel
que consume datos preparados.

**Alternatives considered**:

- Ordenar únicamente por componentes (todo el productor, luego todo el
  frontend): descartado, porque retrasa la verificación de integración y
  dificulta descubrir errores de contrato.
- Enumerar requisitos sin prerrequisitos: descartado, porque el usuario
  necesita saber qué hacer primero y cómo validar cada avance.

## Cobertura de requisitos

**Decision**: Mantener trazabilidad desde requisitos funcionales y pruebas de
aceptación hasta fases, tareas y evidencias del roadmap. Incluir explícitamente
los cinco servicios obligatorios, fuentes recientes e históricas, catálogo
geográfico, calidad, datos actuales/versionados, contrato, panel, seguridad
operativa, despliegue, costes, mediciones, documentación y defensa.

**Rationale**: La rúbrica evalúa extracción, calidad, modelado, análisis y
reflexión. La sección de aceptación también define resultados concretos para
reintentos, revisiones, nulos, coordenadas, túnel y replay.

**Alternatives considered**:

- Cubrir solo hitos de programación: descartado, porque dejaría fuera el
  análisis, las pruebas, el despliegue y los entregables evaluables.
- Copiar todo el texto de los documentos fuente dentro del roadmap:
  descartado, porque duplicaría requisitos y podría desincronizarse; se
  enlazarán las fuentes y se resumirán tareas accionables.

## Límites entre obligatorio y opcional

**Decision**: Señalar con claridad las obligaciones explícitas, las decisiones
que se deben justificar y las ampliaciones opcionales. No requerir Spark,
Flink, Kubernetes, cloud permanente, automatización de informes de calidad ni
panel de calidad.

**Rationale**: El enunciado y el FAQ excluyen expresamente varias herramientas
y aclaran que el generador automático de informes y el panel de calidad son
opcionales.

**Alternatives considered**:

- Añadir ampliaciones como tareas obligatorias para que el roadmap parezca más
  exhaustivo: descartado, porque altera el alcance y la rúbrica.
- Omitir todas las ampliaciones del documento: descartado, porque distinguirlas
  ayuda a no confundirlas con requisitos.

## Decisiones técnicas conocidas

**Decision**: Documentar las tecnologías del sistema como restricciones ya
definidas por el enunciado, no como elecciones de esta feature: Python y
aiokafka para productor/consumidor, Kafka, PostgreSQL, FastAPI, Docker Compose,
Angular/Leaflet, Netlify y ngrok según la arquitectura prescrita.

**Rationale**: El roadmap debe ser fiel al sistema que el estudiante debe
construir y no proponer una arquitectura alternativa.

**Alternatives considered**:

- Seleccionar un stack diferente: descartado por contradecir la arquitectura
  obligatoria.
- Realizar benchmarking o investigación externa del stack en esta fase:
  descartado porque no hay decisión técnica pendiente y excede la creación de
  una hoja de ruta fiel a los documentos entregados.

## Incertidumbres

No quedan `NEEDS CLARIFICATION`. La fecha de entrega, modalidad de trabajo y
distribución en la evaluación se comunicarán en clase según el enunciado; por
eso el roadmap no impondrá fechas ni duraciones.
