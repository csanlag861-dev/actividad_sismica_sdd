# Quickstart: validar dashboard y trazabilidad

## Prerrequisitos

- Node.js 24 y npm instalados.
- Dependencias del frontend instaladas (`cd frontend && npm ci`).
- Para la verificación integrada, backend y PostgreSQL disponibles conforme a [`docs/README.md`](../../../docs/README.md).

## Pruebas y compilación

1. Ejecutar las pruebas del backend desde el contenedor Python del proyecto:

   ```bash
   docker compose run --rm --no-deps --entrypoint python api -m pytest -q tests/contract/test_api_contract.py
   ```

   Esperado: las pruebas de eventos verifican la forma GeoJSON existente y la metadata compacta de trazabilidad; los casos vacíos y errores conservan su semántica.

2. Ejecutar pruebas del cliente de transporte:

   ```bash
   cd frontend
   node --test tests/api-client.test.mjs
   ```

   Esperado: el validador acepta la trazabilidad nueva y sigue aceptando respuestas antiguas sin el objeto.

3. Ejecutar pruebas del frontend y build de producción:

   ```bash
   npm test
   npm run build
   ```

   Esperado: el dashboard presenta mapa, actividad horaria y distribuciones; la ficha muestra trazabilidad y los estados vacíos/error; el build incorpora `icon.png` y lo declara como favicon.

## Comprobación integrada

1. Arrancar la API y sus dependencias como se describe en [`docs/README.md`](../../../docs/README.md):

   ```bash
   docker compose up --build -d
   ```

2. Consultar el endpoint existente, sin incluir secretos en la URL:

   ```bash
   curl -fsS 'http://127.0.0.1:8000/api/eventos'
   ```

   Esperado: una `FeatureCollection`; cada feature incluye `properties.traceability` con modo, fuente segura, ingesta y ejecución, y conserva `id` y `updated`.

3. En otra terminal, iniciar la SPA:

   ```bash
   cd frontend
   npm start
   ```

4. Abrir `http://localhost:4200` y comprobar:
   - El favicon y la marca del encabezado muestran `icon.png`; recorrer cada tema disponible y comprobar que el logo se mantiene legible, proporcionado y con nombre accesible en la interfaz.
   - El mapa y la serie temporal corresponden a sus respuestas/periodos.
   - La lista o tabla accesible de eventos contiene los valores esenciales y seleccionar una fila abre la ficha del evento correspondiente.
   - Las distribuciones declaran unidad, bins y ausentes y cuentan con una alternativa tabular.
   - Seleccionar un evento abre su ficha con los metadatos de versión e ingesta.
   - Una respuesta sin trazabilidad se muestra como no disponible; error y colección vacía no se confunden.

Para comprobar despliegue escalonado, usar una respuesta de eventos anterior sin el objeto `traceability`; la UI debe mantener el evento y marcar únicamente la trazabilidad como no disponible.

## Protocolo guiado de usabilidad (SC-005)

Realizar la prueba en un entorno de prueba con respuestas conocidas que incluyan al menos un bucket horario, distribuciones de magnitud y profundidad con valores válidos y ausentes, y un evento con fuente y versión disponibles. No usar datos sintéticos como si fueran datos reales ni ejecutar la comprobación sobre una respuesta vacía.

1. Dejar visible el dashboard y preparar un cronómetro; iniciar el tiempo cuando el participante vea el dashboard.
2. Sin ayuda del facilitador, pedir al participante que (a) indique una hora UTC y su recuento en la actividad temporal, (b) interprete las unidades y distinga valores válidos de ausentes en las distribuciones de magnitud y profundidad, y (c) abra un evento e indique su fuente y versión.
3. Detener el cronómetro cuando complete las tres tareas. Registrar el entorno de ejecución, el tiempo transcurrido, si cada respuesta coincide con los datos conocidos y el resultado global.

**Criterio de aceptación**: las tres tareas se completan correctamente en un máximo de 180 segundos. Registrar aprobado solo si se cumplen tanto el tiempo como la corrección; si no, registrar el resultado y el paso que impidió completar la prueba. Conservar este registro en la evidencia de ejecución que acompaña a la entrega, no en este quickstart.
