# Implementation Plan: Consulta API y estadísticas sísmicas

**Branch**: `004-api-consultas-estadisticas` | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-api-consultas-estadisticas/spec.md`

## Summary

Implementar las tres operaciones de consulta establecidas por el contrato: colección GeoJSON de los eventos live actuales y filtrables, estado de salud que verifica API/base/esquema y estadísticas coherentes con el estado actual y el histórico replay. Se añadirán contratos REST explícitos, configuración CORS de orígenes permitidos y comportamiento de timeout/error del cliente de consulta, sin construir el mapa ni el panel analítico visual. El backend existente ya contiene los modelos, la persistencia versionada, PostgreSQL y el chequeo de revisión/esquema; se reutilizarán en vez de introducir otro almacenamiento o esquema.

## Technical Context

**Language/Version**: Python 3.12 para el backend (imagen del proyecto); JavaScript nativo en un módulo `.mjs` aislado para el transporte del navegador. La integración de ese transporte en la aplicación Angular queda para la siguiente especificación.

**Primary Dependencies**: FastAPI y Uvicorn para la API HTTP (requeridos por la arquitectura del proyecto, aún no declarados en `backend/requirements.txt`); SQLAlchemy 2.0 async, asyncpg, PostgreSQL 16, pytest y pytest-asyncio. Middleware CORS compatible con FastAPI. El transporte del navegador usa `fetch`/AbortController nativos, sin introducir framework/página en el frontend todavía vacío.

**Storage**: PostgreSQL 16; modelos existentes `EventCurrent`, `EventVersion`, `Country` e `IngestionRun`. No se prevé nueva tabla ni migración para esta funcionalidad.

**Testing**: pytest/pytest-asyncio; pruebas unitarias para filtros y agregaciones, pruebas de contrato HTTP/JSON y CORS, integración con base de datos para disponibilidad/esquema y comparación live/replay. Quickstart con Compose y `curl`.

**Target Platform**: Cinco servicios del proyecto bajo Docker Compose; Uvicorn escucha en `0.0.0.0:8000` dentro del contenedor y el puerto publicado en el host se limita a `127.0.0.1:8000`, dejando el acceso público HTTPS al túnel descrito en la documentación.

**Project Type**: Servicio web REST de consulta más módulo aislado de transporte del cliente web.

**Performance Goals**: No se establece objetivo de latencia/throughput del servidor en las fuentes. El módulo de transporte cancela/declara timeout de consulta a los 15 segundos; no constituye una garantía de latencia del servidor.

**Constraints**: Respetar `docs/CONTRATO-API.md`; consultas basadas en una sola versión actual por evento; UTC y epochs en milisegundos donde aplique; null explícito; estadísticas no pueden tratar errores como ceros ni calcular globales sobre muestra truncada; porcentajes de distribución usan `valid_count` y los valores ausentes se contabilizan aparte; filtros idénticos entre eventos y estadísticas; errores de sintaxis no parseable usan HTTP 400 y parámetros desconocidos/inválidos HTTP 422, con envelope JSON común en errores de consulta y cuerpo contractual específico en salud; CORS solo para orígenes exactos HTTPS configurados y `http://localhost:4200`, con configuración inválida reportada explícitamente y sin aplicación parcial; el cliente distingue errores de transporte sin respuesta accesible de errores HTTP de API y puede recuperarse mediante una nueva llamada explícita, sin reintentos ni refresco periódico; sin credenciales/cookies/secrets públicos. Live y replay permanecen aislados.

**Scale/Scope**: Feed live móvil y conjunto histórico 2025 del proyecto; sin volumen máximo ni objetivo de concurrencia establecido. El endpoint de eventos devolverá la colección completa sin paginación ni límite en esta entrega; si una restricción futura introduce un límite, deberá comunicar total, truncamiento y continuación sin truncar los datos usados por estadísticas.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio/gate | Evaluación |
|---|---|
| Cumplir enunciado, contrato y roadmap | Pasa: diseño traza R18–R20 y define contratos a partir de `CONTRATO-API.md`, `ENUNCIADO.md` y README. |
| Calidad, procedencia, UTC y nulos explícitos | Pasa: lectura desde el evento actual persistido, `null` para valores ausentes y tiempos/ventanas UTC documentados. |
| Idempotencia, revisiones y agregados actuales | Pasa: se une `event_current` con su versión referenciada; las estadísticas nunca cuentan mensajes ni versiones antiguas. |
| Interoperabilidad y exposición segura | Pasa: GeoJSON/JSON contractual, errores explícitos, CORS limitado a orígenes configurados y sin secretos públicos. |
| Análisis reproducible | Pasa: cada grupo/agregado declara periodo, filtros, unidad y ausentes; comparación y muestra de aceptación se pueden reconciliar. |
| Arquitectura de cinco servicios | Pasa: se modifica únicamente el servicio API ya existente; no se añaden servicios. |
| Evitar complejidad opcional | Pasa: sin nueva base, tablas, caché, autenticación, cookies ni paginación preventiva. |

No hay violaciones que requieran justificación.

## Project Structure

### Documentation (this feature)

```text
specs/004-api-consultas-estadisticas/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── query-api.md
    └── browser-client.md
```

### Source Code (repository root)

```text
backend/
├── requirements.txt
├── src/observatorio/
│   ├── api/
│   │   ├── bootstrap.py
│   │   ├── app.py                 # Aplicación HTTP, lifecycle y middleware
│   │   ├── routes.py              # Operaciones eventos, salud y estadísticas
│   │   ├── schemas.py             # Tipos/validación de consulta y respuesta
│   │   ├── queries.py             # Consultas de lectura
│   │   └── statistics.py          # Agregaciones actuales y comparación histórica
│   ├── db/
│   │   └── session.py             # Sesión/engine existentes
│   ├── models/                    # Modelos persistidos existentes
│   └── health.py                  # Readiness/schema checks existentes
└── tests/
    ├── unit/
    │   ├── test_api_queries.py
    │   └── test_statistics.py
    ├── contract/
    │   ├── test_api_contract.py
    │   ├── test_health_contract.py
    │   ├── test_statistics_contract.py
    │   └── test_cors_contract.py
    └── integration/
        ├── test_event_query_database.py
        └── test_statistics_database.py

frontend/
├── public/
│   └── config.json                # URL pública de la API; sin secretos
├── src/
│   └── api-client.mjs             # Transporte puro, sin mapa ni componentes
└── tests/
    └── api-client.test.mjs
```

**Structure Decision**: Mantener el servicio REST dentro de `backend/src/observatorio/api/`, reutilizando `db/session.py`, los modelos y readiness existentes. El servicio `api` debe servir HTTP sin bloquear su arranque por la disponibilidad de PostgreSQL o del esquema; el bootstrap se ejecutará/reintentará de forma independiente y el readiness permanecerá no disponible hasta que base y esquema pasen sus comprobaciones, para que `/api/salud` pueda responder HTTP 503 durante esos fallos. La configuración CORS multi-origen se valida estrictamente al arrancar: una entrada inválida produce un error explícito y no se descarta para aplicar una lista parcial. El bootstrap y Uvicorn permanecen en el mismo contenedor, sin crear un sexto servicio. El puerto del contenedor escucha en `0.0.0.0:8000`, pero su publicación local se enlaza exclusivamente a `127.0.0.1:8000`; el acceso externo se realiza por el túnel. El healthcheck Compose seguirá verificando base y revisión/esquema. Las pruebas nuevas siguen la separación `unit/`, `contract/`, `integration/`; el módulo `.mjs` del navegador y sus pruebas usan APIs web nativas y `node:test`. El snapshot de `frontend/` solo contiene el GeoJSON de países: se añadirá exclusivamente un módulo de transporte que expone resultado/estado para su consumidor, recuperable mediante una nueva llamada explícita tras un fallo, sin reintentos automáticos ni refresco periódico, aplicación Angular, mapa, panel, filtros visuales, tabla ni componentes, que corresponden a R21–R23. La configuración pública `frontend/public/config.json`, ya referenciada por README pero aún ausente, contendrá la URL de API sin secretos.

## Phase 0: Outline & Research

Ver [research.md](research.md). Las decisiones locales resuelven los detalles no fijados por el contrato: modo y unicidad de la consulta, filtros/ventanas, resumen de estadísticas, baseline histórico, salud, manejo de fallos y CORS. No quedan decisiones técnicas bloqueantes.

## Phase 1: Design & Contracts

- [data-model.md](data-model.md): modelo lógico de respuesta y entidades persistidas que la alimentan; no requiere migración.
- [contracts/query-api.md](contracts/query-api.md): parámetros, forma de respuesta y errores para los tres endpoints.
- [contracts/browser-client.md](contracts/browser-client.md): orígenes, preflight, configuración, timeout y estados de lectura.
- [quickstart.md](quickstart.md): pasos repetibles para probar endpoints, filtros, estadísticas, salud y CORS.

### Post-Design Constitution Check

| Gate | Resultado tras diseño |
|---|---|
| Contrato y alcance R18–R20 | Pasa: contratos cubren operaciones y dejan explícitamente fuera el panel de R21–R23. |
| Estado/versiones/nulos/UTC | Pasa: evento actual vinculado a su versión; criterios de filtro, null, fechas y modo quedan explícitos. |
| Errores frente a vacío y cero | Pasa: códigos de error no exitosos separados de colección vacía/estadística válida con cero. |
| CORS y secretos | Pasa: origen de producción exacto configurable, desarrollo explícito, sin comodines ni credenciales. |
| Estadística reproducible | Pasa: modo fuente, intervalos de magnitud/profundidad, denominadores y filtros se documentan en contrato. |
| Arquitectura y complejidad | Pasa: no se añaden servicios, persistencia, autenticación ni dependencias fuera del servicio API necesario. |

No hay violaciones ni preguntas bloqueantes pendientes. Los objetivos de capacidad no exigidos siguen deliberadamente fuera del alcance, no son un supuesto de rendimiento prometido.
