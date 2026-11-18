# Observatorio de actividad sísmica

El proyecto implementa el pipeline, API y panel descritos en `ENUNCIADO.md`.
Para arrancarlo desde la raíz, sigue [`../README.md`](../README.md). Este
documento conserva la explicación histórica del mapa del material de partida
y amplía la referencia técnica de frontend; no debe interpretarse como una
lista de componentes aún pendientes. La aplicación actual usa MapLibre, no
Leaflet.

## 1. Mapa de demostración del material de partida

La siguiente descripción se refiere al mapa original del paquete docente; el
modo de ejecución actual está en el README de raíz.

El paquete original requería Node.js 22.12 o posterior dentro de la rama 22, o
Node 24; npm; acceso a Internet para instalar dependencias y descargar el mapa
base.

```bash
cd frontend
npm ci
npm start
```

En la muestra inicial se veían fronteras y **cuatro eventos ficticios**. Esos
puntos solo servían para probar la cartografía y no son datos sísmicos reales.

La base inicial fijaba Angular 20.3, ngx-leaflet 20.0 y Leaflet 1.9.4. La
implementación actual conserva Angular 20.3 y usa MapLibre, deck.gl y Cesium;
consulta `frontend/package.json` y `FUENTES-Y-LICENCIAS.md`.

## 2. Archivos del mapa de partida

| Archivo | Función |
|---|---|
| `src/app/app.component.ts` | Inicializa capas, carga GeoJSON y actualiza los puntos |
| `src/app/app.component.html` | Contenedor del mapa, estado y leyenda |
| `src/app/app.component.css` | Tamaño y presentación del mapa |
| `src/styles.css` | Estilos globales |
| `public/datos/paises.geojson` | Catálogo completo entregado, sin modificación |
| `public/datos/terremotos-demo.geojson` | Muestra sintética inicial |
| `public/config.json` | Modo demo o API y URL del backend |
| `angular.json` | Carga también el CSS de Leaflet y copia public al build |

`L.geoJSON()` interpreta Polygon/MultiPolygon y el orden de coordenadas automáticamente. Para crear un círculo manualmente se utiliza `[latitud, longitud]`. Las fronteras se dibujan sin relleno sobre OpenStreetMap. Se utiliza la proyección predeterminada del mapa base (Web Mercator): no superpongas un mapamundi equirectangular como si fuera compatible sin reproyectarlo. El catálogo ya contiene la representación cartográfica; no es necesario dibujar sobre una imagen JPG.

El componente sustituye la capa de eventos en cada respuesta: no acumula una copia por refresco. El backend sigue siendo responsable de servir una sola versión actual por evento. Se usan nodos DOM con texto para las fichas, evitando interpretar descripciones como HTML.

## 3. Conectar la API

El backend completo se ejecuta en Docker: productor Python, consumidor Python, Kafka, PostgreSQL y API FastAPI, como cinco servicios de Compose. La API publica el puerto 8000 en `127.0.0.1` para el túnel local y escucha en `0.0.0.0:8000` dentro del contenedor.

Una vez implementados esos archivos, arranca los servicios:

```bash
docker compose up --build -d
```

Usa nombres de servicio entre contenedores (por ejemplo `kafka`, `postgres` y `api`), configura salud/reintentos y conserva los datos en volúmenes. La API debe escuchar en `0.0.0.0:8000` dentro del contenedor y respetar `CONTRATO-API.md`.

**Opción A: ngrok instalado en el equipo.** Publica el puerto de la API con `127.0.0.1:8000:8000`. Configura ngrok en tu cuenta y ejecuta:

```bash
ngrok http 8000
```

**Opción B: ngrok en otro contenedor de la misma red Compose.** El comando del agente apuntará al nombre del servicio:

```bash
ngrok http http://api:8000
```

No uses `localhost:8000` desde el contenedor de ngrok: apuntaría al propio contenedor. Para esta opción no es necesario publicar el puerto de la API en el host. Proporciona el authtoken al agente mediante una variable de entorno o secreto, nunca en el frontend ni en Git.

**HTTPS sin certificados en FastAPI.** La dirección pública es HTTPS y ngrok proporciona y renueva el certificado. La conexión con el agente también está cifrada; el agente puede comunicarse con la API por HTTP dentro del equipo o de la red Docker. No hace falta configurar certificados en Uvicorn ni añadir un proxy TLS para esta práctica. El plan gratuito tiene cuotas de uso.

Cambia `frontend/public/config.json` a la URL HTTPS de la API publicada:

```json
{
  "apiBaseUrl": "https://TU-DOMINIO-ASIGNADO"
}
```

`apiBaseUrl` no termina en `/api`: el módulo de transporte consulta `/api/eventos`. Usa el dominio asignado realmente a tu cuenta. Recarga la página después de cambiar la configuración. La configuración es pública y no debe contener credenciales, tokens ni secretos. CORS permite `http://localhost:4200` y la lista exacta de orígenes HTTPS definida mediante `CORS_ALLOWED_ORIGINS`, separada por comas. No se admiten comodines, credenciales, rutas ni valores inválidos; una configuración inválida impide el arranque en lugar de aplicar una lista parcial. Una llamada OPTIONS puede preceder a GET por la cabecera de ngrok o a POST por `Content-Type` en el comparador; no la bloquees.

El módulo aislado `frontend/src/api-client.mjs` solo ofrece transporte y estado de consulta, no construye una interfaz ni programa refrescos. Cada consulta tiene un timeout de 15 segundos. Distingue errores HTTP accesibles de errores de transporte sin respuesta accesible (que pueden deberse a red o CORS), conserva la última respuesta correcta ante un fallo y limpia el error/desactualización si una consulta posterior iniciada por el consumidor tiene éxito. Las respuestas HTTP de error siguen el envelope documentado en `CONTRATO-API.md`.

## 4. Publicar en Netlify

1. Sube el proyecto a tu repositorio sin node_modules ni secretos.
2. Conecta el repositorio a Netlify.
3. Si el repositorio contiene todo el paquete, establece **Base directory: frontend**. Si subes solo frontend como raíz, deja la base vacía.
4. Comando de build: `npm run build`. Carpeta publicada relativa a esa base: `dist/observatorio/browser`.
5. El `netlify.toml` incluido contiene esos valores; `_redirects` permite recargar rutas SPA.
6. Ajusta CORS al dominio de Netlify. Verifica la web desde otro dispositivo.

No requiere SSR. Si integras el componente en una aplicación SSR existente, carga Leaflet solo en navegador; el ejemplo entregado es exclusivamente SPA.

`config.json` se copia al build: cuando cambies el dominio del backend, publica una nueva versión o actualiza el archivo servido por tu procedimiento de despliegue. No guardes claves en ese archivo público.

## 5. Implementación del proyecto

Productor, consumidor, persistencia, API, integración espacial, agregaciones,
filtros y gráficas están implementados en `backend/` y `frontend/src/`. El
mapa cartográfico inicial fue reemplazado por un explorador con MapLibre, tabla
paginada, comparador y vista opcional de globo Cesium. La clasificación por
país la calcula el consumidor mediante el catálogo Natural Earth; dibujar
fronteras no la sustituye.

Consulta el README de raíz para ejecutar el proyecto y
[`memoria-evaluacion.md`](memoria-evaluacion.md) para el modelo, análisis,
mediciones, pruebas y límites de evaluación. `VALIDACION.md` distingue la
validación del paquete de partida de las comprobaciones del proyecto actual.

## 6. Cómo documentar la calidad, sin añadir una aplicación de informes

Incluye un apartado en la memoria o un notebook con tus comprobaciones, resultados y decisiones. Puedes ejecutar consultas SQL sobre PostgreSQL o código Python sobre los datos originales y preparados; no necesitas desarrollar un generador de informes.

Ejemplo: muestra la consulta/código que cuenta magnitudes nulas, su resultado y el porcentaje; explica por qué conservas los nulos y cómo los tratas al calcular medias. Haz lo mismo con duplicados, anomalías y las demás dimensiones que analices. Indica el conjunto de datos, periodo y denominador utilizado y compara antes/después cuando corresponda.

El consumidor valida, transforma y persiste datos; además conserva los rechazos y sus motivos. El alumnado prepara el apartado de calidad a partir de esas evidencias. **No es obligatorio crear `generar_informe_calidad.py`, una tabla específica de métricas/incidencias de calidad ni un panel de calidad en Angular.** El registro duradero de cuarentena solicitado en el enunciado sí debe conservarse, mediante una tabla o una solución equivalente documentada.

Generar automáticamente un Markdown/HTML de calidad o mostrar esas métricas en la web son ampliaciones opcionales. No añaden por sí mismas puntos ni son necesarias para el nivel máximo: se evalúan la calidad del análisis y las acciones justificadas.

## 7. Exploración avanzada (spec 007)

La aplicación de observatorio añade tablas paginadas independientes en resumen y exploración, con páginas de 25, 50 o 100 eventos y el total filtrado. El mapa 2D usa MapLibre GL JS y el worker local `/assets/maplibre/maplibre-gl-worker.mjs`; OpenStreetMap conserva su atribución visible. El anillo rojo identifica todos los eventos con la fecha de ocurrencia más reciente dentro de la colección mostrada. La API y el globo solicitan como máximo 100 eventos; la interfaz comunica cuando esa muestra es parcial. deck.gl se carga de forma diferida solo al activar la capa hexagonal.

La ruta `/globo-3d` carga CesiumJS únicamente al entrar en la vista y copia `Workers`, `ThirdParty`, `Assets` y `Widgets` bajo `/assets/cesium/`. No se necesita ni se debe añadir un token de Cesium ion. El mapa base declara la atribución de OpenStreetMap y el widget conserva los créditos Cesium. Los eventos válidos se dibujan sobre la superficie; el color/tamaño comunica la profundidad conocida y la ficha muestra el valor exacto, sin situar puntos bajo el elipsoide. Si WebGL, los assets o el proveedor no están disponibles, se puede regresar a exploración 2D y a la tabla.

El comparador de `/analisis` usa `POST /api/comparaciones`, acepta de dos a cinco grupos y poblaciones globales, de país o sin país, y expresa las diferencias como segundo grupo menos primero. Los datos con cobertura incompleta no generan tasas ni distribuciones aparentes; la comparación histórica existente permanece separada.

La validación reproducible de paquetes se ejecuta con `npm ci`, `npm run build` y `node --test tests/api-client.test.mjs` desde `frontend/`; contratos y pruebas unitarias backend con `python -m pytest tests/unit tests/contract` desde `backend/`. La ejecución de `npm test` requiere un navegador Chromium compatible con ChromeHeadless. Véase `VALIDACION.md` para los resultados automatizados y los límites de prueba visual y de usabilidad.
