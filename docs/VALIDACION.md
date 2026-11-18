# Validación del material base

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
