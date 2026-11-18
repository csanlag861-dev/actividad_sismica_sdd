# Tasks: Panel web del observatorio sísmico

**Input**: Documentos de diseño de `/specs/005-panel-sismico/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`

**Tests**: Se incluyen tareas de pruebas porque el plan y el quickstart definen pruebas unitarias/componentes y validación automatizada.

**Organization**: Las tareas se agrupan por historia de usuario para permitir entregas incrementales y validables.

## Formato

- `[P]`: puede ejecutarse en paralelo con tareas de otros archivos sin dependencias pendientes.
- `[US#]`: historia de usuario de `spec.md`.
- Cada tarea identifica los archivos concretos que debe crear o modificar.

## Phase 1: Setup

**Purpose**: Inicializar la SPA Angular estática en la ubicación y versiones previstas por el plan.

- [X] T001 Crear `frontend/package.json` con scripts de desarrollo, pruebas y build, y dependencias Angular 20.3, Router, Tailwind, Lucide, `@bluehalo/ngx-leaflet` 20.0, Leaflet 1.9.4 y Apache ECharts.
- [X] T002 Configurar el proyecto Angular y TypeScript estricto en `frontend/angular.json`, `frontend/tsconfig.json`, `frontend/tsconfig.app.json` y `frontend/tsconfig.spec.json`, con salida `dist/observatorio/browser` y sin SSR.
- [X] T003 [P] Crear el punto de entrada y documento base de la SPA en `frontend/src/main.ts` y `frontend/src/index.html`, incluyendo idioma español, metadatos esenciales y montaje de la aplicación Angular.
- [X] T004 [P] Configurar publicación y fallback de rutas SPA en `frontend/netlify.toml` y `frontend/public/_redirects`, sin exponer configuración secreta.

## Phase 2: Foundational

**Purpose**: Preparar contratos, configuración y servicios compartidos que bloquean la implementación de las historias.

- [X] T005 Definir los tipos de filtros, respuestas API, entidades GeoJSON y estados efímeros según `data-model.md` en `frontend/src/app/core/models/api.models.ts` y `frontend/src/app/core/models/ui-state.models.ts`.
- [X] T006 Añadir la declaración TypeScript del cliente de transporte existente en `frontend/src/api-client.d.mts`, conservando `frontend/src/api-client.mjs` y sin añadir endpoints ni reintentos.
- [X] T007 [P] Implementar carga y validación de la única configuración pública `apiBaseUrl` desde `frontend/public/config.json` en `frontend/src/app/core/api/app-config.service.ts`.
- [X] T008 Integrar el transporte existente en un servicio tipado para `GET /api/eventos`, `GET /api/estadisticas` y `GET /api/salud` en `frontend/src/app/core/api/observatory-api.service.ts`; usar solo parámetros del contrato y distinguir errores HTTP de transporte.
- [X] T009 Implementar el estado compartido de consultas en `frontend/src/app/core/state/query-state.service.ts`, asociando respuesta válida, filtros/periodo, hora de lectura, error, identificador de consulta y posible desactualización por recurso.
- [X] T010 Configurar bootstrap y providers de la SPA en `frontend/src/app/app.config.ts` y declarar inicialmente la ruta raíz en `frontend/src/app/app.routes.ts`, manteniendo el árbol frontend fuera del backend.

**Checkpoint**: El proyecto compila y los servicios compartidos pueden ser usados por las historias sin alterar la API.

## Phase 3: User Story 1 - Orientarse en el observatorio (Priority: P1)

**Goal**: Entregar el dashboard de entrada, navegación principal y cambio de tema, comunicando periodo y estado del servicio sin inventar datos.

**Independent Test**: Con la API disponible, validar el dashboard, sus accesos de navegación y el cambio de tema; con fallo de API, comprobar que el estado se comunica sin presentarlo como saludable ni sustituirlo por datos ficticios. No requiere que los destinos de eventos y análisis estén terminados; el recorrido integral se valida tras US2 y US3.

### Tests for User Story 1

- [X] T011 [P] [US1] Añadir pruebas de rutas, navegación y persistencia del tema solo durante la sesión en `frontend/src/app/app.component.spec.ts`.
- [X] T012 [P] [US1] Añadir pruebas del dashboard para respuestas de salud correctas y fallidas, periodo e información respaldada por API en `frontend/src/app/features/dashboard/dashboard-page.component.spec.ts`.

### Implementation for User Story 1

- [X] T013 [US1] Implementar el shell accesible con el dashboard y las secciones previstas en la navegación; mantener disponibles solo las rutas implementadas y señalar de forma inequívoca los destinos pendientes. Añadir tema oscuro predeterminado y toggle oscuro/claro en `frontend/src/app/app.component.ts`, `frontend/src/app/app.component.html` y `frontend/src/app/app.component.css`.
- [X] T014 [US1] Implementar la página dashboard con periodo consultado, estado de salud/última ingesta y accesos a exploración y análisis en `frontend/src/app/features/dashboard/dashboard-page.component.ts`, `frontend/src/app/features/dashboard/dashboard-page.component.html` y `frontend/src/app/features/dashboard/dashboard-page.component.css`.
- [X] T015 [US1] Registrar en `frontend/src/app/app.routes.ts` la vista dashboard como ruta inicial; esta tarea inicia la integración secuencial de rutas.
- [X] T016 [US1] Aplicar tokens, tipografía, jerarquía, estados y temas Mars Station globales en `frontend/src/styles.css`.

**Checkpoint**: La historia queda navegable de forma autónoma y el dashboard comunica explícitamente fallos del servicio.

## Phase 4: User Story 2 - Explorar eventos en el mapa y consultar su ficha (Priority: P1)

**Goal**: Mostrar eventos de la API en Leaflet y permitir consultar la misma ficha desde el mapa, sin inferir propiedades ni acumular capas entre consultas.

**Independent Test**: Con una respuesta conocida de eventos, comprobar orden longitud/latitud, tamaño por magnitud, color por intervalo de profundidad, tratamiento de nulos, sustitución de capa y coincidencia de la ficha con las propiedades originales.

### Tests for User Story 2

- [X] T017 [P] [US2] Añadir pruebas de conversión de geometría, tamaño por magnitud y bins semiabiertos de profundidad de 10 km en `frontend/src/app/shared/map/event-map.utils.spec.ts`.
- [X] T018 [P] [US2] Añadir pruebas de la selección de eventos y presentación de atributos nulos/unidades en `frontend/src/app/features/events/event-detail.component.spec.ts`.

### Implementation for User Story 2

- [X] T019 [P] [US2] Implementar utilidades de geometría, radio de marcador y clasificación de profundidad, incluyendo leyenda y símbolo para nulos, en `frontend/src/app/shared/map/event-map.utils.ts`.
- [X] T020 [P] [US2] Cargar las fronteras del catálogo local `frontend/public/datos/paises.geojson` y definir capas base/atribución Leaflet en `frontend/src/app/shared/map/map-layers.service.ts`.
- [X] T021 [US2] Implementar el mapa Leaflet con `frontend/src/app/shared/map/map-layers.service.ts` y reemplazar la capa de eventos ante cada respuesta correcta en `frontend/src/app/shared/map/event-map.component.ts`, `frontend/src/app/shared/map/event-map.component.html` y `frontend/src/app/shared/map/event-map.component.css`.
- [X] T022 [US2] Implementar ficha accesible de evento con propiedades API, unidades y nulos explícitos en `frontend/src/app/features/events/event-detail.component.ts`, `frontend/src/app/features/events/event-detail.component.html` y `frontend/src/app/features/events/event-detail.component.css`.
- [X] T023 [US2] Después de T015, añadir `/eventos` a `frontend/src/app/app.routes.ts` e implementar la vista que comparte selección entre mapa y ficha en `frontend/src/app/features/events/events-page.component.ts`, `frontend/src/app/features/events/events-page.component.html` y `frontend/src/app/features/events/events-page.component.css`.

**Checkpoint**: El visitante puede explorar y seleccionar eventos sin que la cartografía se convierta en fuente de datos sísmicos.

## Phase 5: User Story 3 - Filtrar y consultar eventos y estadísticas (Priority: P2)

**Goal**: Aplicar filtros contractuales coherentes a mapa, tabla y estadísticas, con refresco coordinado y estados distinguibles.

**Independent Test**: Aplicar periodo UTC, magnitud mínima y país a respuestas conocidas; comprobar los parámetros comunes, resultados, agregados, valores ausentes, estado vacío/error/truncado y actualización conjunta cada 60 segundos.

### Tests for User Story 3

- [X] T024 [P] [US3] Añadir pruebas de validación/serialización de filtros: `start` inclusivo, `end` exclusivo, UTC `Z`, `start < end`, `min_mag` finita y `country_id` exacto en `frontend/src/app/features/events/event-filters.component.spec.ts`.
- [X] T025 [P] [US3] Añadir pruebas de tabla, selección compartida y presentación de errores, datos vacíos y truncamiento en `frontend/src/app/features/events/events-table.component.spec.ts`.
- [X] T026 [P] [US3] Añadir pruebas de visualizaciones estadísticas para periodo, unidades, valores ausentes y uso de datos API sin recalcular agregados en `frontend/src/app/features/analytics/statistics-view.component.spec.ts`.
- [X] T027 [P] [US3] Escribir antes de T029 y ejecutar tras T029 pruebas del estado compartido para debounce y refresco temporal, descarte de respuestas fuera de orden, conservación de la última instantánea ante fallos, recuperación y errores parciales en `frontend/src/app/core/state/query-state.service.spec.ts`.

### Implementation for User Story 3

- [X] T028 [US3] Implementar filtros de periodo UTC, magnitud y catálogo `ADM0_A3`/`NAME_ES`; mantener el default móvil de últimas 24 horas sin enviar `start` ni `end`, y no ofrecer filtros regionales, de tipo o de país nulo en `frontend/src/app/features/events/event-filters.component.ts`, `frontend/src/app/features/events/event-filters.component.html` y `frontend/src/app/features/events/event-filters.component.css`.
- [X] T029 [US3] Coordinar filtros, debounce de 300 ms, actualización de eventos/estadísticas/salud cada 60 segundos, reintento explícito y descarte de respuestas anteriores en `frontend/src/app/core/state/query-state.service.ts`.
- [X] T030 [US3] Implementar tabla de eventos como alternativa consultable al mapa, con nulos explícitos y selección de la misma ficha en `frontend/src/app/features/events/events-table.component.ts`, `frontend/src/app/features/events/events-table.component.html` y `frontend/src/app/features/events/events-table.component.css`.
- [X] T031 [US3] Implementar gráficos de recuentos horarios UTC, recuentos por país y distribuciones de magnitud/profundidad usando exclusivamente la respuesta de estadísticas en `frontend/src/app/features/analytics/statistics-view.component.ts`, `frontend/src/app/features/analytics/statistics-view.component.html` y `frontend/src/app/features/analytics/statistics-view.component.css`.
- [X] T032 [US3] Después de T023, añadir `/analisis` a `frontend/src/app/app.routes.ts` e implementar la página que conecta filtros, estados de recursos y visualizaciones estadísticas en `frontend/src/app/features/analytics/analytics-page.component.ts`, `frontend/src/app/features/analytics/analytics-page.component.html` y `frontend/src/app/features/analytics/analytics-page.component.css`.
- [X] T033 [US3] Implementar estados reutilizables de carga, vacío, error HTTP/transporte, truncamiento y posible desactualización en `frontend/src/app/shared/status/resource-status.component.ts`, `frontend/src/app/shared/status/resource-status.component.html` y `frontend/src/app/shared/status/resource-status.component.css`.

**Checkpoint**: Mapa, tabla y estadísticas identifican su consulta efectiva y no transforman errores en cero o vacío.

## Phase 6: User Story 4 - Interpretar la comparación histórica (Priority: P3)

**Goal**: Presentar la comparación del periodo consultado con el baseline 2025 de la API, haciendo visibles cobertura, filtros, unidades y límites.

**Independent Test**: Usar respuestas con baseline disponible, incompleto/no disponible y tasa histórica cero; cotejar periodos, filtros, unidades, diferencias y cocientes con el contrato, sin mostrar predicción o evaluación de riesgo.

### Tests for User Story 4

- [X] T034 [P] [US4] Añadir pruebas de baseline disponible/no disponible, promedio histórico cero y campos opcionales de diferencia/ratio en `frontend/src/app/features/analytics/historical-comparison.component.spec.ts`.

### Implementation for User Story 4

- [X] T035 [US4] Implementar la comparación histórica con periodo consultado, baseline 2025, filtros, tasas, eventos/día y solo diferencias/cocientes presentes en la respuesta en `frontend/src/app/features/analytics/historical-comparison.component.ts`, `frontend/src/app/features/analytics/historical-comparison.component.html` y `frontend/src/app/features/analytics/historical-comparison.component.css`.
- [X] T036 [US4] Integrar el componente de comparación en la vista `/analisis`, conservando la distinción entre baseline no disponible y cero en `frontend/src/app/features/analytics/analytics-page.component.html`.

**Checkpoint**: La comparación comunica cobertura y no se presenta como predicción ni como riesgo sísmico.

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Validar el conjunto integrado, accesibilidad, adaptación responsive y documentación de arranque.

- [X] T037 [P] Ajustar navegación, filtros, tabla, mapa y gráficos a escritorio/tablet/móvil, foco visible, teclado y alternativas no basadas solo en color en `frontend/src/styles.css`.
- [X] T038 [P] Actualizar pasos de instalación, configuración pública y escenarios de validación para reflejar los archivos finales en `specs/005-panel-sismico/quickstart.md`.
- [X] T039 Ejecutar pruebas Angular y de transporte (`npm test -- --watch=false` y `node --test tests/api-client.test.mjs`) desde `frontend/` y corregir regresiones reflejadas en `frontend/package.json`.
- [X] T040 Ejecutar el build de producción y validar la salida estática `dist/observatorio/browser` mediante `frontend/angular.json`.
- [X] T041 Recorrer los escenarios de navegación, filtros, estados de fallo/recuperación, comparación y tamaños responsive del quickstart y registrar cualquier divergencia en `specs/005-panel-sismico/quickstart.md`.

## Dependencies & Execution Order

### Dependencias entre fases

- **Setup (Phase 1)**: Sin dependencias; establece la base Angular.
- **Foundational (Phase 2)**: Depende de Setup y bloquea todas las historias.
- **US1 (Phase 3)** y **US2 (Phase 4)**: ambas son P1 y sus componentes pueden desarrollarse en paralelo tras Foundation. La edición de `frontend/src/app/app.routes.ts` tiene un único flujo secuencial: T015 crea `/`, T023 añade `/eventos` después de T015 y T032 añade `/analisis` después de T023.
- **US3 (Phase 5)**: sus componentes pueden desarrollarse tras Foundation; la integración accesible depende del shell/navegación de US1 y de la vista de eventos de US2, donde se conectan filtros y tabla. La incorporación de `/analisis` a las rutas espera la integración de `/eventos` de T023.
- **US4 (Phase 6)**: depende de la respuesta de estadísticas/estado de filtros de US3 y del shell de navegación de US1 para integrar la comparación en la página de análisis.
- **Polish (Phase 7)**: depende de las historias que se incluyan en la entrega; T037 y T038 pueden avanzar en paralelo, las validaciones T039–T041 requieren la implementación integrada.

### Grafo de historias

```text
Phase 1 Setup
    ↓
Phase 2 Foundational
    ├── US1 (P1) ─────┐
    └── US2 (P1) ─────┴──> US3 (P2) ──> US4 (P3)
                                             │
                                             ↓
                                    Phase 7 Polish
```

### Oportunidades de paralelismo

- Setup: T003 y T004 son paralelizables respecto a la configuración Angular; T002 requiere T001.
- Foundation: T007 puede avanzarse en paralelo con T005/T006; T008 requiere tipos/configuración y T009 requiere la integración API.
- US1: T011 y T012 son pruebas en archivos separados; el trabajo del shell y dashboard se puede dividir una vez acordados sus puntos de integración.
- US2: T017 y T018 son pruebas independientes; T019 y T020 son tareas de archivos separados.
- US3: T024–T027 son pruebas en archivos separados; tabla y visualizaciones pueden implementarse en paralelo tras establecer filtros/estado compartidos. T027 se escribe antes y se ejecuta tras T029, que implementa el servicio probado; la integración de rutas T015 → T023 → T032 no se paraleliza.
- US4: T034 puede prepararse en paralelo con componentes no dependientes; integración final requiere terminar los componentes de US3.
- Polish: T037 y T038 son independientes.

## Parallel Examples

### User Story 1

```text
Task: T011 pruebas de navegación/tema en frontend/src/app/app.component.spec.ts
Task: T012 pruebas del dashboard en frontend/src/app/features/dashboard/dashboard-page.component.spec.ts
```

### User Story 2

```text
Task: T017 pruebas de utilidades cartográficas en frontend/src/app/shared/map/event-map.utils.spec.ts
Task: T018 pruebas de ficha en frontend/src/app/features/events/event-detail.component.spec.ts
Task: T020 capas base/catálogo Leaflet en frontend/src/app/shared/map/map-layers.service.ts
```

### User Story 3

```text
Task: T024 pruebas de filtros en frontend/src/app/features/events/event-filters.component.spec.ts
Task: T025 pruebas de tabla en frontend/src/app/features/events/events-table.component.spec.ts
Task: T026 pruebas estadísticas en frontend/src/app/features/analytics/statistics-view.component.spec.ts
Task: T027 pruebas del estado compartido en frontend/src/app/core/state/query-state.service.spec.ts
```

## Implementation Strategy

### MVP sugerido: User Story 1

1. Completar Setup y Foundation.
2. Completar US1: dashboard, navegación, tema y estado real de salud.
3. Validar US1 de forma independiente con la API disponible y con respuesta fallida.
4. Continuar con US2 para completar R21 y con US3/US4 para R22/R23.

### Entrega incremental

1. Setup + Foundation: proyecto ejecutable, cliente y estado compartido.
2. US1: punto de entrada funcional demostrable.
3. US2: mapa y ficha de eventos.
4. US3: filtros, tabla y estadísticas coordinados.
5. US4: comparación histórica integrada.
6. Polish: build estático, pruebas y comprobación de accesibilidad/responsive.

## Notes

- Los eventos, la salud y las estadísticas proceden únicamente de la API FastAPI; Leaflet y el GeoJSON local no son fuentes de datos sísmicos.
- No modificar endpoints, backend, `compose.yaml` ni añadir filtros de región/subregión o tipo de magnitud.
- Mantener nulos explícitos, fechas UTC y el periodo/filtros propios de cada respuesta; para eventos son los valores enviados y para estadísticas los efectivos declarados por la API.
- Las tres conclusiones cuantitativas de R23 corresponden a la memoria/informe, no a la UI.

## Phase 8: Convergence

- [X] T042 CRITICAL: Conservar el periodo, los filtros, el identificador de consulta y la hora de lectura de la última respuesta válida mientras se carga o falla una consulta nueva, sin atribuir los datos retenidos a filtros nuevos, per Constitution II, FR-011 y SC-003 (contradicts).
- [X] T043 Sincronizar los controles de filtros con el estado compartido al entrar o volver a `/eventos` y `/analisis`, de modo que aplicar el formulario no elimine filtros activos, per FR-006, SC-002 y US3/AC1.
- [X] T044 Mostrar el periodo y los filtros asociados a los resultados del mapa, la tabla y cada visualización estadística: enviados para eventos y efectivos declarados por la API para estadísticas, además de las unidades requeridas, per FR-006, FR-008 y SC-002.
