# Implementation Plan: Panel web del observatorio sísmico

**Branch**: `005-panel-sismico` | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/005-panel-sismico/spec.md`

## Summary

Completar H6 con una SPA pública en español para dashboard, exploración cartográfica y análisis sísmico. La interfaz consumirá exclusivamente los datos del observatorio a través de `GET /api/eventos`, `GET /api/estadisticas` y `GET /api/salud`, respetará los filtros contractuales y mantendrá juntas las consultas, el periodo y los estados de carga/error/desactualización. Se inicializará el frontend Angular que falta en el árbol de trabajo siguiendo el stack reproducible de la guía del proyecto, se reutilizarán el cliente de transporte existente y el catálogo cartográfico local, y no se modificarán el backend, el esquema ni los endpoints.

## Technical Context

**Language/Version**: TypeScript de Angular 20.3 y JavaScript nativo para el módulo de transporte existente. Node.js 24 está disponible y cumple la rama recomendada por `docs/README.md`.

**Primary Dependencies**: Angular 20.3, Angular Router, Tailwind CSS y Lucide según el sistema de diseño; `@bluehalo/ngx-leaflet` 20.0 con Leaflet 1.9.4 según la guía ejecutable del proyecto; Apache ECharts para las visualizaciones definidas y probado/registrado modularmente en componentes Angular. No se incorpora Cesium ni una segunda biblioteca de gráficos.

**Storage**: Sin almacenamiento de servidor ni nuevas tablas. El estado de consulta, filtros y tema vive en memoria durante la sesión; el filtro de país usa el GeoJSON local del catálogo Natural Earth ya incluido.

**Testing**: Conservar `node --test frontend/tests/api-client.test.mjs` para el transporte; añadir pruebas unitarias/componentes con el runner de Angular 20 para filtros, estados, tema, tablas, escalas y comparación. `npm run build` valida compilación y plantillas; `npm start` sirve la SPA para comprobación manual end-to-end con el backend o respuestas simuladas identificadas en pruebas.

**Target Platform**: SPA Angular en navegadores de escritorio, tablet y móvil; desarrollo en `http://localhost:4200`, build estático para Netlify en `dist/observatorio/browser`; sin SSR. API publicada mediante el HTTPS de ngrok conforme a la guía.

**Project Type**: Aplicación frontend Angular de solo lectura y cliente de la API FastAPI existente.

**Performance Goals**: No hay objetivo de latencia, concurrencia ni tamaño máximo de colección especificado. El transporte conserva el timeout contractual de 15 segundos; no se presenta como SLA de la aplicación o API. Evitar cálculos globales sobre una colección truncada.

**Constraints**: Respetar `docs/ENUNCIADO.md`, `docs/CONTRATO-API.md`, `docs/design/design-system.md` y la constitución. La consulta de datos sísmicos se limita a la API del proyecto; no hay acceso a USGS desde el navegador. Parámetros equivalentes `start`, `end`, `min_mag`, `country_id`; fechas UTC, `start` inclusivo y `end` exclusivo. Eventos y estadísticas (incluida comparación) se solicitan juntos al cambiar filtros y cada 60 segundos; los errores no se presentan como datos vacíos ni ceros. Mantener última lectura identificada ante fallos, filtrar respuestas fuera de orden, sustituir capas en vez de acumularlas y tratar nulos sin valores ficticios. El backend/contrato y las cinco unidades de servicio Docker quedan sin cambios. Conservar licencias y atribución del material geográfico y de las teselas cartográficas. No incluir configuración secreta en el bundle.

**Scale/Scope**: Tres superficies de navegación (dashboard, exploración de eventos y análisis), cuatro operaciones visuales basadas en recursos actuales (mapa/ficha, tabla, estadísticas, comparación), dos temas y una colección de eventos live del periodo consultado. El frontend actual solo contiene transporte, configuración y recursos GeoJSON, no una aplicación Angular completa; se deberá crear la estructura inicial documentada sin copiar datos demo al modo real.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio/gate | Evaluación |
|---|---|
| Cumplir enunciado, contrato y roadmap | Pasa: diseño traza H6 y R21–R23; usa solo endpoints/campos existentes y aplica el alcance `api_only` confirmado. |
| Procedencia, calidad, UTC y nulos explícitos | Pasa: eventos de la API; fechas y buckets en UTC; null se muestra como desconocido; el filtro de país reutiliza el catálogo cuyo `ADM0_A3` coincide con `country_id`. |
| Idempotencia y revisiones correctas | Pasa: UI reemplaza cada capa/resultado con la respuesta actual, no agrega eventos por actualización; revisión y deduplicación siguen siendo responsabilidad de la API. |
| Contratos interoperables y exposición segura | Pasa: fetch exclusivamente a la API para datos sísmicos; sin credenciales, cookies, acceso a almacenamiento o servicios de administración. La base cartográfica no es fuente de eventos y conserva atribución. |
| Análisis reproducible y conclusiones proporcionadas | Pasa: cada consulta muestra periodo/filtros/unidades/ausentes y comparación del backend; la memoria documenta tres conclusiones, el panel no las genera ni presenta predicción/riesgo. |
| Arquitectura frontend y cinco servicios | Pasa: crea solo la SPA estática; no añade ni sustituye servicios backend/Compose. |
| Evitar complejidad opcional | Pasa: excluye Cesium, edición, autenticación, exportación e indicadores no respaldados. ECharts se aprueba en este plan técnico para representar las series/distribuciones obligatorias; no agrega datos ni endpoints. |

No hay violaciones que requieran justificación.

## Project Structure

### Documentation (this feature)

```text
specs/005-panel-sismico/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── panel-ui.md
    └── api-consumption.md
```

### Source Code (repository root)

```text
frontend/
├── package.json
├── package-lock.json
├── angular.json
├── tsconfig*.json
├── netlify.toml
├── public/
│   ├── _redirects
│   ├── config.json
│   └── datos/
│       └── paises.geojson
├── src/
│   ├── main.ts
│   ├── index.html
│   ├── styles.css
│   ├── api-client.d.ts
│   ├── api-client.mjs
│   └── app/
│       ├── app.component.*
│       ├── app.routes.ts
│       ├── core/
│       │   ├── api/
│       │   ├── models/
│       │   └── state/
│       ├── features/
│       │   ├── dashboard/
│       │   ├── events/
│       │   └── analytics/
│       └── shared/
│           ├── layout/
│           ├── map/
│           ├── charts/
│           ├── table/
│           └── status/
└── tests/
    └── api-client.test.mjs
```

**Structure Decision**: Inicializar una única SPA bajo `frontend/`, conforme a las ubicaciones de Angular que define `docs/README.md` y a la organización por funcionalidades recomendada en el sistema visual. La navegación separa dashboard, explorador y análisis; modelos y llamadas API compartidas viven en `core`, y visualizaciones/componentes de interacción reutilizables en `shared`. Reutilizar el módulo de transporte JavaScript y mantener sus pruebas Node; aportar declaración TypeScript para su integración Angular. Crear filtros/catálogo y tema en cliente sin persistencia ni nuevos servicios backend. Mantener en `public/datos/paises.geojson` la copia existente. OSM es solo fondo cartográfico según la guía, con atribución visible; los eventos/estadísticas nunca se obtienen de OSM ni de otro feed. No modificar `backend/`, `compose.yaml` ni el contrato API.

## Phase 0: Outline & Research

Completada en [research.md](research.md): fija versiones y puntos de integración usando la documentación local, el código existente y documentación oficial de Angular/Leaflet/ECharts. No queda ninguna pregunta `NEEDS CLARIFICATION` en el contexto técnico.

## Phase 1: Design & Contracts

Completada mediante [data-model.md](data-model.md), [panel-ui.md](contracts/panel-ui.md), [api-consumption.md](contracts/api-consumption.md) y [quickstart.md](quickstart.md). Los contratos del backend se referencian y no se redefinen.

## Constitution Check (post-design)

Pasa: el diseño conserva solo datos y operaciones existentes, respeta la separación entre aplicación de consulta pública y servicios de datos, define estados explícitos para fallos/nulos y mantiene contexto temporal/filtros en gráficos. No se añaden almacenamiento, autenticación, API ni servicios de infraestructura. Se documenta el único origen adicional de red aceptado por el proyecto (teselas del mapa) como cartografía, no como fuente de datos sísmicos.

## Complexity Tracking

No hay violaciones de la constitución ni complejidad opcional que requiera justificación adicional.
