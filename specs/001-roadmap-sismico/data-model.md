# Data Model: Roadmap integral del Observatorio sísmico

Este modelo define la información que debe contener el documento de roadmap,
no las tablas de la aplicación sísmica.

## Entities

### Fase

Agrupa una parte coherente y ordenada del trabajo.

| Field | Description | Validation |
|---|---|---|
| `id` | Identificador estable y orden de la fase | Único; orden consistente con sus dependencias |
| `title` | Resultado que busca la fase | Concreto y orientado a una entrega |
| `goal` | Valor o capacidad que se obtiene | Comprensible para el estudiante |
| `prerequisites` | Hitos previos necesarios | Enlaza fases existentes; vacío si es inicio |
| `exit_criteria` | Condición verificable para cerrar la fase | Observable, no una intención vaga |
| `references` | Fuentes que gobiernan la fase | Enlaces relativos a documentos del proyecto |

### Tarea

Acción realizable que produce un artefacto, capacidad o evidencia.

| Field | Description | Validation |
|---|---|---|
| `id` | Identificador único dentro del roadmap | No duplicado |
| `title` | Acción expresada con verbo | Debe indicar un resultado concreto |
| `priority` | Orden de importancia dentro de la fase | P1 para ruta esencial; P2/P3 para cierre o ampliación |
| `requirement_type` | Obligatorio, decisión documentable u opcional | No confundir opcional con obligatorio |
| `prerequisites` | Tareas o fases necesarias antes de iniciar | Sin ciclos; usar solo dependencias reales |
| `subtasks` | Desglose de trabajo si la acción requiere varios pasos | Cada subtarea es accionable y no duplica otra tarea |
| `deliverable` | Artefacto o resultado producido | Identificable por el estudiante |
| `acceptance_evidence` | Prueba que acredita su finalización | Reproducible u observable |
| `references` | Requisito o aclaración de origen | Enlaces al enunciado, contrato o FAQ |

### Requisito de referencia

Obligación, límite, prueba de aceptación o entrega extraída de una fuente
normativa del proyecto.

| Field | Description | Validation |
|---|---|---|
| `id` | Identificador de trazabilidad del roadmap | Único |
| `statement` | Resumen fiel del requisito | No cambia su alcance normativo |
| `source` | Documento y sección de procedencia | Enlace resoluble |
| `type` | Arquitectura, datos, API, prueba, entrega, decisión u opcional | Clasificación coherente con la fuente |
| `covered_by` | Fases y tareas que lo satisfacen | Toda obligación obligatoria queda cubierta |

### Dependencia

Relación de precedencia entre dos tareas o fases.

| Field | Description | Validation |
|---|---|---|
| `predecessor` | Trabajo que debe completarse primero | Existe en el roadmap |
| `successor` | Trabajo que depende del anterior | Existe en el roadmap |
| `reason` | Por qué existe la dependencia | No inferida solo por el orden de lectura |

Las dependencias deben formar un grafo acíclico. Una tarea puede ser ejecutada
en paralelo con otra cuando no exista una dependencia funcional entre ambas.

### Evidencia

Resultado que permite verificar una tarea o requisito.

| Field | Description | Validation |
|---|---|---|
| `id` | Identificador de evidencia o prueba | Único en la matriz |
| `description` | Resultado que se observa | Debe ser comprobable |
| `method` | Acción o prueba para obtener el resultado | Reproducible y adecuada al requisito |
| `covers` | Tareas, requisitos o criterios de aceptación asociados | Enlaces existentes |

### Entregable

Artefacto final, publicación o evidencia que se presenta.

| Field | Description | Validation |
|---|---|---|
| `name` | Nombre descriptivo | Coherente con los documentos del proyecto |
| `content` | Qué debe incluir | Alineado con la rúbrica y requisitos |
| `produced_by` | Tarea o fase que lo genera | Enlace existente |
| `verification` | Cómo comprobar que está completo | Criterio observable |

## Relationships

- Una **Fase** contiene una o varias **Tareas**.
- Una **Tarea** puede contener **Subtareas** y depende de cero o más tareas
  anteriores.
- Una **Tarea** cubre uno o varios **Requisitos de referencia**.
- Un **Requisito de referencia** puede exigir varias tareas o evidencias.
- Una **Evidencia** valida una tarea, requisito o prueba de aceptación.
- Un **Entregable** es producido por una o más tareas y se verifica mediante
  evidencias.

## State and validation rules

- El roadmap se presenta en orden topológico: todo prerrequisito aparece antes
  del trabajo que lo requiere.
- Cada tarea obligatoria incluye al menos una evidencia de finalización.
- Cada prueba de aceptación del enunciado se relaciona con una tarea de prueba
  y un resultado esperado.
- Se distinguen mensajes repetidos, revisiones actuales y atrasadas, valores
  ausentes, geometría inválida, eventos sin país, desconexión y replay.
- El estado de progreso del estudiante no se fija en el documento; el roadmap
  es una secuencia de trabajo y criterios, no un registro de ejecución.
