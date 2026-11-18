# Implementation Plan: Dashboard de actividad y trazabilidad sísmica

**Branch**: `006-dashboard-trazabilidad-eventos` | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from [`spec.md`](spec.md)

## Summary

Completar el dashboard público con el mapa de eventos recientes, la serie de actividad horaria UTC y los resúmenes de las distribuciones de magnitud y profundidad ya devueltas por la API. Reutilizar el mapa, el estado compartido de consultas y los patrones de gráficos actuales. Ampliar de forma aditiva `GET /api/eventos` con trazabilidad compacta obtenida de los campos que ya conserva cada versión del evento; presentar esos datos en la ficha. Incorporar el logo aprobado como favicon y en la identidad global de la SPA.

## Technical Context

**Language/Version**: Backend Python 3.12; frontend TypeScript con Angular 20.3; JavaScript nativo en el cliente de transporte; Node.js 24.

**Primary Dependencies**: FastAPI, SQLAlchemy async y pytest en el backend; Angular Router, Leaflet 1.9.4 con `@bluehalo/ngx-leaflet` 20.0, Apache ECharts 6 y Jasmine/Karma en el frontend. Se reutilizan las dependencias y versiones ya instaladas.

**Storage**: PostgreSQL existente. `event_version` ya conserva `mode`, `event_id`, `updated_at`, `source`, `ingested_at` e `ingestion_run_id`; no se requieren columnas, tablas ni migraciones nuevas. No se añade almacenamiento frontend.

**Testing**: Pruebas de contrato de API con pytest en `backend/tests/contract`; pruebas Angular Jasmine/Karma para el dashboard, ficha, modelos y componentes; pruebas del cliente con `node --test frontend/tests/api-client.test.mjs`; compilación con `npm run build`.

**Target Platform**: API FastAPI bajo Docker Compose y SPA estática Angular para navegadores de escritorio, tableta y móvil, publicada en Netlify. Se conserva `frontend/public/icon.png`.

**Project Type**: Cambio de interfaz pública de solo lectura y ampliación aditiva del contrato de una API HTTP existente.

**Performance Goals**: No se introducen nuevos objetivos de latencia, disponibilidad, tamaño de respuesta ni concurrencia. Se conservan el timeout de transporte existente y el refresco del consumidor definido por la aplicación.

**Constraints**: Respetar la constitución, `docs/ENUNCIADO.md`, `docs/CONTRATO-API.md` y el sistema visual. Las estadísticas y eventos siguen procediendo de FastAPI; los gráficos presentan los valores recibidos y no recalculan agregados. `GET /api/eventos` sigue devolviendo la versión actual y los campos existentes. Los nuevos metadatos de trazabilidad no exponen payload, hash, credenciales, secretos, parámetros de consulta ni fragmentos de URL. Los errores y los nulos no se presentan como ceros o datos ficticios. El cliente tolera respuestas previas sin trazabilidad y etiqueta esos metadatos como no disponibles. El logo no se deforma ni se repite como adorno en cada vista.

**Scale/Scope**: Una vista de dashboard que presenta eventos recientes del periodo predeterminado (24 horas), horarios UTC y distribuciones de magnitud/profundidad; una ficha enriquecida; una estructura compacta de trazabilidad por evento; favicon y marca global. Se actualiza una ruta API ya existente y su documentación; no se añade endpoint, migración, dependencia ni servicio de infraestructura.

## Constitution Check

| Principio / gate | Evaluación |
|---|---|
| Cumplir enunciado, contrato y referencias | Pasa: se actualiza el contrato vigente de eventos; no se inventan rutas ni campos estadísticos. |
| Procedencia, calidad, UTC y nulos explícitos | Pasa: la procedencia procede de la versión actual persistida; las fechas se exponen como epoch milisegundos UTC; los datos no disponibles son `null`/«No disponible». |
| Idempotencia y revisiones correctas | Pasa: la consulta conserva la selección de `event_current`; no cambia la persistencia, deduplicación ni cálculo estadístico. |
| Contratos interoperables y exposición segura | Pasa: los campos nuevos son aditivos y de procedencia compacta; no se publica el payload original, hash, secretos o URL con consultas. El panel sigue usando solo la API del proyecto para datos sísmicos. |
| Análisis reproducible y conclusiones proporcionadas | Pasa: periodo, filtros, unidades, bins y ausentes proceden de la respuesta estadística. No se calculan indicadores sísmicos nuevos ni conclusiones de riesgo. |
| Servicios separados y límites de infraestructura | Pasa: no se añaden servicios, almacenamiento o migraciones; solo se modifican API, SPA, documentación y pruebas. |
| Complejidad opcional justificada | Pasa: se reutilizan mapa, ficha, ECharts y logo existentes; no se incorpora otra biblioteca visual ni funcionalidad administrativa. |

No hay violaciones que requieran justificación.

## Project Structure

### Documentation (this feature)

```text
specs/006-dashboard-trazabilidad-eventos/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dashboard-ui.md
    └── event-traceability.md
```

### Source Code (repository root)

```text
backend/
├── src/observatorio/api/
│   ├── queries.py
│   └── routes.py
└── tests/contract/
    └── test_api_contract.py

docs/
└── CONTRATO-API.md

frontend/
├── public/
│   └── icon.png
└── src/
    ├── index.html
    └── app/
        ├── app.component.html
        ├── core/models/api.models.ts
        ├── features/dashboard/
        │   ├── dashboard-page.component.*
        │   ├── activity-timeline.component.{ts,html,css}
        │   └── distribution-summary.component.{ts,html,css}
        ├── features/events/
        │   ├── event-detail.component.*
        │   └── event-detail.component.spec.ts
        └── shared/map/
            └── event-map.component.*
```

**Structure Decision**: Mantener la SPA Angular y el servicio FastAPI en sus ubicaciones actuales. Componer en el dashboard el componente compartido `EventMapComponent` y una presentación compacta de estadísticas horarias y distribuciones, tomando el patrón visual de ECharts ya usado por `StatisticsViewComponent`. Reutilizar `EventDetailComponent` en exploración y dashboard para evitar dos fichas incompatibles. Añadir los campos de contrato a los modelos TypeScript y al validador del cliente, manteniendo compatibilidad con respuestas antiguas. Serializar metadatos desde `EventVersion` en la consulta existente; sus campos persistidos evitan cambios de esquema. Documentar la forma de respuesta junto a los contratos del dashboard/API y en `docs/CONTRATO-API.md`.

## Phase 0: Outline & Research

Completada en [research.md](research.md). La inspección del código local confirma que el dashboard, mapa, ficha, estado de consultas, gráficos ECharts y metadatos de persistencia existen ya; el trabajo integra esas piezas y no recrea la aplicación. La revisión de compatibilidad y exposición segura se fundamenta en el contrato, las etiquetas de fuente y los campos persistidos actuales.

## Phase 1: Design & Contracts

Completada con [data-model.md](data-model.md), [contracts/dashboard-ui.md](contracts/dashboard-ui.md), [contracts/event-traceability.md](contracts/event-traceability.md) y [quickstart.md](quickstart.md). El contrato de trazabilidad mantiene `Feature.id` como identidad del evento y `properties.updated` como fecha de versión existentes; añade un objeto compacto para modo, fuente pública segura, fecha de ingesta e identificador de ejecución.

## Constitution Check (post-design)

Pasa: el diseño no requiere migración y mantiene separadas la fuente de datos sísmicos (API) y la cartografía. La ampliación conserva el GeoJSON y metadatos actuales; la visualización declara contexto estadístico, valores ausentes y estados de error. Los datos de fuente se limitan a identificadores/URL sin consulta ni fragmento y la compatibilidad con respuestas antiguas evita tratar la falta del objeto nuevo como fallo de toda la colección.

## Complexity Tracking

No hay violaciones constitucionales, nuevos servicios, dependencias o persistencia que requieran justificación adicional.
