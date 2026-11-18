# Observatorio de actividad sísmica

Proyecto de Sistemas de Big Data que ingiere GeoJSON de USGS, mantiene versiones
de eventos, integra el catálogo Natural Earth, y ofrece consultas y análisis
desde una SPA Angular.

## Arquitectura

Docker Compose ejecuta cinco servicios separados: productor Python, Kafka,
consumidor Python, PostgreSQL y API FastAPI. El frontend Angular se desarrolla
localmente y se puede publicar como SPA en Netlify. Durante una demostración
pública, ngrok expone únicamente la API.

Flujo: USGS → productor → Kafka → consumidor (validación, cuarentena e
integración geográfica) → PostgreSQL → FastAPI → Angular.

## Requisitos y puesta en marcha

- Docker Compose v2.
- Node.js 22.12+ o 24 y npm.
- Conexión a Internet para las consultas USGS y los mapas base.

1. Crea un `.env` local a partir de `.env.example` y sustituye la contraseña
   de PostgreSQL por un valor seguro. No subas `.env`.
2. Arranca el backend:

   ```sh
   docker compose up --build -d
   docker compose ps
   ```

3. La primera consulta live comienza al arrancar. Para cargar el baseline de
   2025 una vez, o reanudar una carga interrumpida:

   ```sh
   docker compose run --rm --no-deps productor \
     python -m observatorio.producer.replay \
     --year 2025 --min-magnitude 4 --event-type earthquake --interval-seconds 0
   ```

   Las respuestas originales y los checkpoints quedan en el volumen
   `source_archives`. La carga no borra los datos live ni los volúmenes.
4. Comprueba la API en `http://127.0.0.1:8000/api/salud` y
   `http://127.0.0.1:8000/api/estadisticas`.
5. Para desarrollar el panel:

   ```sh
   cd frontend
   npm ci
   npm start
   ```

   Abre `http://localhost:4200`. El build Netlify se genera con
   `npm run build` en `frontend/`; la carpeta publicada es
   `dist/observatorio/browser`.

   La ruta `/reproduccion` consulta de forma aislada los eventos históricos
   `replay`; permite cambiar el intervalo y la magnitud mínima sin alterar
   la exploración ni las estadísticas live.

Kafka y PostgreSQL no publican puertos en el host. El log de Kafka conserva
mensajes durante siete días; PostgreSQL y los archivos originales usan
volúmenes persistentes.

Para detener los contenedores sin borrar datos:

```sh
docker compose down
```

Los volúmenes nombrados se conservan al detener y recrear servicios. No uses
`docker compose down -v` si quieres mantener la base, los archivos originales
y sus checkpoints. Para revisar fallos:

```sh
docker compose logs --since 10m api consumidor productor kafka postgres
```

## Pruebas

Desde la raíz, si las dependencias de `backend/requirements.txt` están
instaladas:

```sh
cd backend
python -m pytest -q tests/unit tests/contract tests/integration
cd ../frontend
node --test tests/api-client.test.mjs
npm test
npm run build
```

`npm test` requiere Chrome/Chromium para ChromeHeadless. Las pruebas PostgreSQL
dependen del servicio Compose activo. La memoria y la evidencia de ejecución
indican qué verificaciones se pudieron completar en este entorno.

## Configuración pública y túnel

Para uso local, el backend se consulta en `http://127.0.0.1:8000`. Para Netlify,
ejecuta `ngrok http 8000`, configura el origen HTTPS exacto de Netlify en
`CORS_ALLOWED_ORIGINS` y apunta `frontend/public/config.json` a la URL HTTPS
asignada, sin `/api` ni credenciales. Reconstruye y publica después de cambiar
la configuración. El token de ngrok es un secreto y no pertenece al frontend.

## Documentación y evaluación

- [Enunciado y rúbrica](docs/ENUNCIADO.md)
- [FAQ del alumnado](docs/FAQ-ALUMNADO.md)
- [Guía de entregables](docs/Guia-entregables-observatorio-sismico.md)
- [Contrato de API](docs/CONTRATO-API.md)
- [Operación del pipeline](docs/PIPELINE-OPERACION.md)
- [Fuentes y licencias](docs/FUENTES-Y-LICENCIAS.md)
- [Memoria de evaluación y resultados medidos](docs/memoria-evaluacion.md)
- [Protocolo de evaluación de usabilidad](docs/evaluacion-usabilidad-007.md)
- [Validación y límites de las pruebas](docs/VALIDACION.md)

La memoria distingue el análisis de una captura real de USGS, las mediciones
sintéticas de rendimiento y las pruebas que todavía requieren navegador,
despliegue público o defensa oral.
