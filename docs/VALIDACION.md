# Validación del material de partida

Esta primera sección registra las comprobaciones del mapa/material base, no el
estado final del proyecto. La implementación posterior del backend, las
pruebas y su evaluación se documentan al final y en
[memoria-proyecto.md](../memoria-proyecto.md).

Comprobaciones realizadas el 27 de octubre de 2026:

- Instalación de las dependencias fijadas y generación de `package-lock.json`.
- `npm run build`: compilación de producción correcta, con TypeScript estricto y comprobación de plantillas Angular.
- Aviso de compilación: Leaflet 1.9.4 utiliza CommonJS; no impide generar el build.
- Catálogo JSON válido: 177 entidades, 177 códigos `ADM0_A3` distintos, geometrías Polygon/MultiPolygon.
- El build incluye config.json, el catálogo, la muestra y `_redirects`.
- Las muestras están etiquetadas como sintéticas, separadas del modo API.

Límites de esta comprobación:

- No se completó una prueba visual en navegador: el entorno no disponía de Chromium y no pudo descargar su ejecutable correctamente.
- No se ha desplegado una cuenta real de Netlify ni abierto un túnel ngrok del alumnado.
- La API y el pipeline son parte del trabajo a implementar, no servicios incluidos y probados en este paquete.

Antes de distribuir/defender, ejecutar la comprobación manual:

1. `npm ci` y `npm start` en frontend.
2. Verificar cuatro eventos ficticios y fronteras; abrir una ficha y el selector de capas.
3. Comprobar zoom, leyenda y atribución del mapa base.
4. Configurar vuestra API, confirmar la petición OPTIONS/GET y los datos recibidos.
5. Cerrar y reabrir el túnel; comprobar aviso y recuperación en el siguiente refresco.
6. Publicar en Netlify y repetir desde otro dispositivo.

## Implementación de exploración avanzada (spec 007)

Las pruebas unitarias y de contrato backend, junto con los tests del cliente API, se ejecutan sin servicios externos. `npm run build` genera correctamente el frontend con MapLibre, sus worker y CSS, chunks diferidos de deck.gl/Cesium y los assets estáticos del globo. El worker quedó en `dist/observatorio/browser/assets/maplibre/maplibre-gl-worker.mjs`; los cuatro directorios requeridos por Cesium se publican bajo `dist/observatorio/browser/assets/cesium/`.

El runner `npm test` compila el bundle de pruebas, pero este entorno no tiene Chrome/Chromium para ejecutar ChromeHeadless. Un smoke-test con navegador integrado confirmó la ruta directa `/globo-3d`, el canvas de Cesium y el canvas MapLibre con su atribución OpenStreetMap. Las consultas de eventos desde el puerto temporal 4300 fueron bloqueadas por CORS; no había datos para validar marcadores/selección y no se completó la interacción con deck.gl ni el fallback WebGL.

Los umbrales de rendimiento SC-002 y la evaluación humana de diez participantes SC-003/SC-006 no se midieron en este entorno. Deben ejecutarse con la fixture, el método y el registro definidos en `specs/007-exploracion-sismica-avanzada/quickstart.md`; no se sustituyen por resultados estimados.

## Validación del proyecto implementado

Comprobaciones ejecutadas el 18 de noviembre de 2026:

- Backend: 124 pruebas unitarias/de contrato y 18 pruebas de integración
  (17 generales y una con PostgreSQL aislado) superadas.
- Frontend: 13 pruebas del cliente de API superadas y build Angular de
  producción superado.
- La suite Karma no se pudo ejecutar: este entorno no tiene un binario
  Chrome/Chromium para `ChromeHeadless`.
- Los cinco servicios de Docker Compose quedaron activos y saludables tras
  aplicar la migración `0007_event_time_query_index` y reiniciar Kafka con
  `KAFKA_LOG_RETENTION_HOURS=168`; se verificó que el índice existe en
  PostgreSQL.
- Se probó `GET /api/eventos?mode=replay` con periodo histórico, validación de
  parámetros y aislamiento live/replay. La nueva ruta `/reproduccion` se
  comprobó en navegador local con un día de 2025 y sus datos reales.
- El feed de las últimas 24 horas pudo consultarse en USGS directamente.
  La carga del histórico de 2025 se ejecutó por intervalos mediante el
  productor y Kafka. El perfil SQL anual cubrió 18.302 eventos; se conciliaron
  los 60 ACK previos con la ejecución completa y se documentaron el método y
  las limitaciones en la memoria.
- Un smoke test en `http://localhost:4200/reproduccion` confirmó la consulta
  de 60 eventos para el 1 de enero de 2025. No equivale a una evaluación de
  usabilidad ni a una prueba de despliegue.
- El alumno confirma que ha probado la publicación del frontend en Netlify y
  la API local expuesta por ngrok. En caso de caída del túnel, el frontend
  presenta un error de conexión con la API. Esta revisión no accedió a los
  dominios públicos, así que se registra como validación comunicada por el
  alumno; no se afirma un reintento automático al recuperarse el túnel.
- Una persona probó informalmente la aplicación y la encontró intuitiva,
  según el alumno. No se siguió el protocolo definido ni se midieron tareas o
  tiempos; no equivale a la evaluación formal de diez participantes.
- El guion de la evaluación humana SC-003/SC-006 está preparado en
  [`evaluacion-usabilidad-007.md`](evaluacion-usabilidad-007.md), pero no se
  ejecutó: faltan diez participantes reales y una fixture de prueba aislada.
  No se han medido esos criterios ni los umbrales de rendimiento SC-002.

La respuesta local de `/api/estadisticas` consultada el 19-11-2026 incluía
`USA` («Estados Unidos») con 169 eventos. El gráfico no acomodaba bien todas
las categorías porque su altura era fija; ahora aumenta con el número de
países, ordena por recuento descendente y permite desplazarse por el contenido.
Una comprobación visual con datos de muestra confirmó que Estados Unidos queda
al inicio del gráfico y que una lista extensa conserva el desplazamiento.

Las mediciones de búsqueda incluidas en la memoria son microbenchmarks locales
con identificadores sintéticos, no estadísticas sísmicas. Los resultados del
feed y del histórico sísmico se identifican como datos reales USGS y llevan su
periodo y procedencia.
