---

description: "Tareas para crear y validar el roadmap integral del Observatorio sísmico"
---

# Tasks: Roadmap integral del Observatorio sísmico

**Input**: Design documents from `specs/001-roadmap-sismico/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/roadmap-format.md`, `quickstart.md`

**Tests**: No se generan tareas de código ni TDD: esta feature produce
documentación. La validación documental y las pruebas de aceptación deben
quedar descritas en `ROADMAP.md`.

**Organization**: Las fases se organizan por las historias de usuario de
`spec.md`. Los cambios de contenido se hacen en `ROADMAP.md`; las fuentes
obligatorias son los documentos bajo `docs/`.

## Formato y rutas

- Cada tarea sigue el formato `- [ ] T### [P?] [US#?] Acción en ruta`.
- `[P]` solo se utiliza cuando la tarea puede completarse en paralelo sin
  dependencia pendiente y sin editar el mismo archivo que otra tarea paralela.
- Toda tarea de historia de usuario lleva su etiqueta `[US1]`, `[US2]` o
  `[US3]`.
- Las tareas obligatorias documentan resultado, criterio de finalización y
  evidencia en `ROADMAP.md`.

## Phase 1: Setup

**Purpose**: Crear el documento final y fijar sus fuentes autoritativas antes
de añadir las fases de trabajo.

- [X] T001 Crear `ROADMAP.md` en la raíz con título, propósito, fecha de
  preparación y enlaces a `docs/ENUNCIADO.md`, `docs/CONTRATO-API.md` y
  `docs/FAQ-ALUMNADO.md`; indicar que el enunciado define requisitos y rúbrica,
  el contrato define el servicio de consulta y el FAQ solo aclara.

**Checkpoint**: Existe `ROADMAP.md`, se entiende qué proyecto guía y enlaza
correctamente sus tres fuentes principales.

## Phase 2: Foundational

**Purpose**: Establecer una estructura común para que las fases sean
accionables, trazables y verificables.

- [X] T002 Añadir a `ROADMAP.md` una leyenda que diferencie requisitos
  obligatorios, decisiones que el estudiante debe justificar y ampliaciones
  opcionales; contrastarla con `docs/ENUNCIADO.md` y
  `docs/FAQ-ALUMNADO.md` para no convertir ejemplos en obligaciones.
- [X] T003 Añadir a `ROADMAP.md` el índice de hitos y el formato fijo de cada
  fase y tarea: objetivo, prerrequisitos, tareas/subtareas, resultado,
  condición de salida, evidencia y referencias; basarse en
  `specs/001-roadmap-sismico/contracts/roadmap-format.md`.

**Checkpoint**: `ROADMAP.md` tiene reglas de lectura, hitos ordenados y un
formato consistente para describir todo el trabajo posterior.

## Phase 3: User Story 1 - Seguir una ruta de trabajo completa (Priority: P1)

**Goal**: Describir en `ROADMAP.md` una ruta de trabajo desde la comprensión
del encargo hasta la construcción funcional del flujo de datos y el análisis.

**Independent Test**: Un estudiante puede seguir los hitos de principio a fin
hasta obtener un flujo mínimo verificable; cada fase declara sus
prerrequisitos y su criterio de salida.

### Implementation for User Story 1

- [X] T004 [US1] Añadir a `ROADMAP.md` una primera fase para leer
  `docs/ENUNCIADO.md`, `docs/CONTRATO-API.md`, `docs/FAQ-ALUMNADO.md` y
  `docs/README.md`; registrar alcance, rúbrica, entregables, límites y
  preguntas que el estudiante debe llevar a clase, sin inventar fechas.
- [X] T005 [US1] Añadir a `ROADMAP.md` la fase de exploración del material y
  entorno: verificar los requisitos descritos en `docs/README.md`, ejecutar
  el mapa demo siguiendo sus instrucciones, identificar los datos ficticios y
  anotar prerrequisitos locales; definir como evidencia una captura o nota de
  verificación del entorno.
- [X] T006 [US1] Añadir a `ROADMAP.md` la fase de exploración de fuentes desde
  `docs/ENUNCIADO.md`: inspeccionar un registro reciente, planificar la
  descarga histórica por intervalos, identificar unidades/campos y revisar el
  catálogo geográfico y sus licencias; exigir como resultado un diccionario
  inicial de datos y un registro de consultas/procedencia.
- [X] T007 [US1] Añadir a `ROADMAP.md` la fase de diseño de datos desde
  `docs/ENUNCIADO.md` y `docs/CONTRATO-API.md`: documentar grano, claves,
  tablas de evento actual/versiones, dimensiones, cuarentena, estado de
  ingesta, índices y reglas geográficas; exigir diagramas conceptual, lógico
  y físico y decisiones justificadas como evidencia.
- [X] T008 [US1] Añadir a `ROADMAP.md` la fase de infraestructura mínima:
  describir la creación de los cinco servicios separados de Docker Compose,
  imágenes reproducibles, dependencias fijadas, configuración de entorno,
  salud/reintentos, volúmenes y retención; precisar que Kafka y PostgreSQL no
  se exponen por el túnel conforme a `docs/ENUNCIADO.md`.
- [X] T009 [US1] Añadir a `ROADMAP.md` el hito de recorrido vertical mínimo:
  usar un evento de prueba y verificar publicación, consumo, persistencia,
  consulta y representación en el mapa; enumerar comandos/acciones de
  comprobación y el resultado esperado, tomando el itinerario de
  `docs/FAQ-ALUMNADO.md` como aclaración.
- [X] T010 [US1] Añadir a `ROADMAP.md` la fase de extracción e ingesta:
  separar feed reciente y carga histórica, registrar originales y metadatos,
  configurar frecuencia/reintentos, deduplicar límites de intervalos y
  persistir el estado de publicación; referenciar las reglas de fuentes e
  ingesta de `docs/ENUNCIADO.md`.
- [X] T011 [US1] Añadir a `ROADMAP.md` la fase de validación y
  transformación: especificar UTC/unidades, validación de tipos y coordenadas,
  filtros de tipo de evento, cuarentena duradera, conservación de nulos,
  integración punto-en-polígono y categoría «Sin país asignado» según
  `docs/ENUNCIADO.md`.
- [X] T012 [US1] Añadir a `ROADMAP.md` la fase de idempotencia y revisiones:
  describir comparación por identificador/versión, actualización condicional
  del estado actual, conservación de versiones, transacción de escritura y
  confirmación posterior del offset; incluir las secuencias de duplicado,
  versión nueva y versión antigua de `docs/FAQ-ALUMNADO.md`.
- [X] T013 [US1] Añadir a `ROADMAP.md` la fase de servicio de consulta:
  enumerar `GET /api/eventos`, `GET /api/salud` y `GET /api/estadisticas`,
  filtros, GeoJSON, timestamps UTC, nulos, truncamiento/paginación y error
  explícito de base de datos conforme a `docs/CONTRATO-API.md`; incluir
  comprobación de cada operación.
- [X] T014 [US1] Añadir a `ROADMAP.md` las fases de integración del panel:
  conectar el panel entregado al servicio propio, completar filtros
  coherentes, mapa/leyenda, tabla accesible, recuentos por hora y país,
  distribuciones, estado/desactualización y comparación histórica; conservar
  en `docs/ENUNCIADO.md` y `docs/CONTRATO-API.md` las reglas de periodo,
  filtros, unidades y valores ausentes.

**Checkpoint**: La historia queda completa cuando `ROADMAP.md` describe
secuencialmente desde lectura y preparación hasta API y análisis, con un
resultado y evidencia por fase.

## Phase 4: User Story 2 - Comprobar la cobertura de requisitos (Priority: P2)

**Goal**: Permitir rastrear los requisitos, pruebas de aceptación, rúbrica y
entregables desde `ROADMAP.md` hasta una tarea y evidencia.

**Independent Test**: Se puede comprobar que el 100 % de las obligaciones
enumeradas en las fuentes autoritativas aparece en la matriz con una tarea
asociada y un resultado verificable.

### Implementation for User Story 2

- [X] T015 [US2] Añadir a `ROADMAP.md` una matriz de cobertura que relacione
  los requisitos funcionales del proyecto con sus fases y tareas; contrastar
  la matriz con `docs/ENUNCIADO.md` y `docs/CONTRATO-API.md` y no dejar
  requisitos obligatorios sin referencia.
- [X] T016 [US2] Completar en `ROADMAP.md` la matriz de pruebas de aceptación
  de `docs/ENUNCIADO.md`: evento nuevo, reenvío duplicado, revisión posterior,
  revisión antigua, magnitud nula, coordenadas inválidas, evento marítimo,
  reinicio del consumidor, cierre y recuperación del túnel y reproducción
  histórica; asignar a cada caso su tarea y resultado esperado.
- [X] T017 [US2] Añadir a `ROADMAP.md` la matriz de rúbrica y entregables
  usando `docs/ENUNCIADO.md`: vincular extracción, calidad, modelado, análisis
  y reflexión con las evidencias pedidas, e incluir modelo, diccionario,
  procedencia, memoria/notebook, conclusiones, costes, mediciones y material
  de defensa.
- [X] T018 [US2] Revisar en `ROADMAP.md` cada requisito y ejemplo de
  `docs/FAQ-ALUMNADO.md` contra `docs/ENUNCIADO.md`; etiquetar explícitamente
  automatización de informes de calidad, panel de calidad y demás extensiones
  como opcionales cuando corresponda, y corregir cualquier obligación nueva
  inferida solo de un ejemplo.

**Checkpoint**: La historia queda completa cuando cada requisito obligatorio,
prueba, criterio de rúbrica y entregable está cubierto, y los opcionales no se
confunden con requisitos.

## Phase 5: User Story 3 - Preparar la demostración y la entrega (Priority: P3)

**Goal**: Cerrar `ROADMAP.md` con pruebas integrales, despliegue, documentación,
evidencias y preparación de la defensa.

**Independent Test**: Una persona puede seguir las tareas finales para
verificar el sistema, publicarlo y demostrarlo, incluso si no hay eventos
nuevos en vivo; encuentra todas las evidencias y entregables que debe
presentar.

### Implementation for User Story 3

- [X] T019 [US3] Añadir a `ROADMAP.md` la fase de calidad y pruebas
  integrales: cubrir dimensiones de calidad, resultados antes/después,
  nulos/anomalías, prueba de contrato y criterios del
  `specs/001-roadmap-sismico/quickstart.md`; indicar que las pruebas no pasan
  hasta registrar resultados y decisiones.
- [X] T020 [US3] Añadir a `ROADMAP.md` la fase de reproducción demostrativa:
  documentar selección ordenada, tiempo original y de reproducción,
  aislamiento respecto a datos live, etiqueta «REPRODUCCIÓN» y casos
  controlados de duplicado/revisión conforme a `docs/ENUNCIADO.md` y
  `docs/FAQ-ALUMNADO.md`.
- [X] T021 [US3] Añadir a `ROADMAP.md` la fase de complejidad, rendimiento y
  costes: exigir tres tamaños de entrada, tiempo/memoria, equipo y método,
  análisis de estructuras/operaciones, costes de hardware/energía/
  almacenamiento/transferencia/mantenimiento/desarrollo y propuesta de
  escalado conforme a `docs/ENUNCIADO.md`.
- [X] T022 [US3] Añadir a `ROADMAP.md` la fase de publicación y operación:
  incluir `.env.example` sin secretos, publicación del panel en Netlify,
  configuración HTTPS/CORS/ngrok, exposición solo de la API, prueba desde
  otro dispositivo, apagado y recuperación; referenciar
  `docs/CONTRATO-API.md` y `docs/README.md`.
- [X] T023 [US3] Añadir a `ROADMAP.md` la fase de documentación y entrega:
  enumerar instrucciones reproducibles, arquitectura, diccionario y
  procedencia, modelo/SQL/índices, apartado de calidad, análisis con tres
  conclusiones, costes/limitaciones, evidencias y limpieza de secretos,
  dependencias o datos binarios según `docs/ENUNCIADO.md`.
- [X] T024 [US3] Añadir a `ROADMAP.md` una lista de preparación de defensa
  basada en `docs/ENUNCIADO.md` y `docs/FAQ-ALUMNADO.md`: levantar servicios y
  túnel, comprobar el panel desde otro dispositivo, preparar replay aislado,
  verificar duplicados/revisiones y ensayar explicación de un evento y una
  decisión técnica.

**Checkpoint**: La historia queda completa cuando `ROADMAP.md` cubre
verificación final, reproducción, publicación, documentación, evidencias y
defensa en ese orden.

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validar el roadmap completo, su utilidad y la conformidad con
fuentes y contrato de formato.

- [X] T025 Revisar en `ROADMAP.md` el orden y prerrequisitos de todas las
  fases; comprobar que no haya dependencias circulares ni fases que omitan
  objetivo, condición de salida, resultado o evidencia usando
  `specs/001-roadmap-sismico/data-model.md`.
- [X] T026 Validar todos los escenarios de `specs/001-roadmap-sismico/quickstart.md` contra `ROADMAP.md`:
  recorrido de principio a fin, cobertura, límites entre obligatorio/opcional
  y claridad de tareas; corregir cualquier fallo directamente en `ROADMAP.md`.
- [X] T027 Comprobar los enlaces relativos de `ROADMAP.md` hacia
  `docs/ENUNCIADO.md`, `docs/CONTRATO-API.md`, `docs/FAQ-ALUMNADO.md`,
  `docs/README.md` y las referencias internas; entregar el documento solo si
  todos resuelven.
- [X] T028 Revisar `ROADMAP.md` con
  `specs/001-roadmap-sismico/contracts/roadmap-format.md`: confirmar que
  todas las tareas obligatorias tienen ID, tipo, prerrequisitos, pasos,
  resultado, criterio, evidencia y referencia, y que no se añadieron
  tecnologías o requisitos ajenos.

**Checkpoint**: Roadmap listo para utilizarse como guía ejecutable; todos los
escenarios de validación pasan y las fuentes autoritativas están enlazadas.

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sin dependencias; crea el archivo de destino y enlaza
  las fuentes.
- **Foundational (Phase 2)**: Depende de T001; fija el formato antes de
  incorporar contenido.
- **User Story 1 (Phase 3)**: Depende de T001–T003; crea la ruta técnica y
  académica principal.
- **User Story 2 (Phase 4)**: Depende de las fases y tareas de US1 para
  relacionar requisitos con elementos concretos del roadmap.
- **User Story 3 (Phase 5)**: Depende de US1 para completar la secuencia del
  sistema y de US2 para que pruebas y entregables finales queden cubiertos.
- **Polish (Phase 6)**: Depende de US1–US3 completos.

### User Story Dependencies

- **US1 (P1)**: Inicia tras Setup y Foundational. MVP del roadmap: proporciona
  ruta completa hasta panel y análisis.
- **US2 (P2)**: Requiere el borrador de fases de US1 para realizar una
  trazabilidad útil; su comprobación de cobertura es independiente de la
  implementación del sistema.
- **US3 (P3)**: Requiere la secuencia de US1 y la cobertura de US2 para cerrar
  pruebas, despliegue, documentación y defensa.

### Parallel Opportunities

- No hay tareas de edición marcadas `[P]`: todas las tareas escriben o
  actualizan el mismo `ROADMAP.md`, por lo que ejecutarlas concurrentemente
  arriesgaría conflictos.
- Durante T004–T014 se pueden leer en paralelo secciones independientes de
  `docs/ENUNCIADO.md` y `docs/CONTRATO-API.md`, pero la incorporación al
  documento debe ser secuencial para preservar el orden y evitar sobrescribir
  cambios.
- En T016–T017 la extracción de casos de aceptación y de criterios de rúbrica
  puede hacerse simultáneamente como análisis, pero las entradas de la matriz
  se consolidan en `ROADMAP.md` antes de cerrar US2.
- Las revisiones de enlaces y de cobertura de T026–T028 pueden asignarse a
  revisores distintos; los cambios correctivos se integran de forma
  secuencial.

## Parallel Example: User Story 1

```text
Lectura de fuentes:
  - Extraer requisitos de fuentes e ingesta de docs/ENUNCIADO.md
  - Extraer reglas de respuesta y errores de docs/CONTRATO-API.md
  - Extraer el itinerario de inicio de docs/FAQ-ALUMNADO.md

Integración (secuencial en ROADMAP.md):
  - Registrar resultados en T006–T014 y verificar los prerrequisitos de cada fase.
```

## Parallel Example: User Story 2

```text
Análisis simultáneo de fuentes:
  - Enumerar las pruebas de aceptación de docs/ENUNCIADO.md
  - Enumerar criterios de rúbrica y entregables de docs/ENUNCIADO.md
  - Contrastar notas aclaratorias y opcionales de docs/FAQ-ALUMNADO.md

Integración (secuencial en ROADMAP.md):
  - Completar las matrices y revisar su cobertura mediante T015–T018.
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Completar Setup y Foundational.
2. Completar US1, incluyendo hitos, dependencias, resultados y evidencias
   desde el encargo hasta el panel y el análisis.
3. **DETENERSE Y VALIDAR**: seguir la secuencia de fases y confirmar que cada
   una define prerrequisitos y condición de salida.

### Incremental Delivery

1. Añadir US2 y comprobar que requisitos, pruebas, rúbrica y entregables
   quedan trazados a tareas.
2. Añadir US3 para aceptación integral, replay, mediciones, publicación,
   documentación y defensa.
3. Completar Polish con validación de enlaces, fuentes, criterios y
   opcionales.

### Definition of Done

- `ROADMAP.md` cubre desde preparación hasta defensa.
- Cada tarea del roadmap tiene criterio de salida y evidencia.
- Las dependencias y las tareas opcionales están identificadas.
- Todos los requisitos, pruebas de aceptación, criterios de rúbrica y
  entregables tienen cobertura.
- Todos los enlaces relativos funcionan y no se agregaron requisitos no
  respaldados por las fuentes.
