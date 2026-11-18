# Evidencia de ejecución — Spec 006

**Fecha:** 2026-11-18

## Entorno

- Sistema: Linux
- Backend: Docker Compose, API FastAPI con Python 3.12
- Frontend: Angular 20.3, Node/npm disponible
- Navegador: Chrome Headless 140.0.0.0, Playwright Chromium build 1187
- URL visual local: `http://localhost:4200/`

## Validación técnica

| Comprobación | Resultado |
|---|---|
| Contratos API backend | 10/10 pruebas superadas |
| Cliente API frontend | 10/10 pruebas superadas |
| Suite Angular Jasmine/Karma | 35/35 pruebas superadas |
| Build Angular de producción | Superado |
| Respuesta `/api/eventos` en vivo | FeatureCollection con `metadata.truncated` y `properties.traceability` |
| Respuesta `/api/estadisticas` en vivo | Periodo, filtros, conteos horarios y distribuciones disponibles |

## Validación visual del logo

- Tema oscuro: comprobado, `width: 40px`, `object-fit: contain`.
- Tema claro: comprobado, `width: 40px`, `object-fit: contain`.
- Texto alternativo: `Logo del Observatorio de actividad sísmica`.
- Navegación y dashboard visualizados sobre datos reales de la API.
- Captura visual: `/tmp/spec006-light.png` (temporal; no forma parte del repositorio).

## Protocolo guiado SC-005

**Resultado comunicado:** aprobado.

- Participante: una persona
- Datos: datos conocidos del entorno de prueba
- Tiempo: 160 segundos
- Corrección: las tres tareas de identificación de actividad UTC, interpretacion de distribuciones y trazabilidad del evento se consideran superadas
- Resultado global: aprobado, dentro del limite de 180 segundos

Durante la ejecución también se identificaron dos detalles técnicos del entorno:

- ChromeHeadless no estaba declarado previamente como `CHROME_BIN`; la validación final usó explícitamente el binario local de Chromium.
- El build conserva una advertencia no bloqueante de Leaflet por el uso CommonJS/AMD.
