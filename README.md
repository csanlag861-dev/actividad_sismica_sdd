# Observatorio de actividad sísmica

Observatorio de actividad sísmica desarrollado para el proyecto de Sistemas
de Big Data. Recoge y versiona terremotos del catálogo de USGS, los procesa
con Kafka y PostgreSQL, y permite explorarlos desde una aplicación Angular.

> **Entrega:** la [memoria del proyecto](memoria-proyecto.md) documenta el
> modelo de datos, las decisiones de diseño, la procedencia y calidad de los
> datos, los análisis, las pruebas, las mediciones y los costes.

## Aplicación y demostración

- **Aplicación desplegada:** [actividad-sismica-sdd.netlify.app](https://actividad-sismica-sdd.netlify.app/)
- **Vídeo explicativo y demo:** [Ver en YouTube](https://youtu.be/hdkaBeDkLaQ)

El frontend se sirve desde Netlify y consulta una API desplegada localmente y
expuesta mediante ngrok. Por tanto, la aplicación puede abrirse aunque el
backend o el túnel estén apagados, pero no podrá cargar datos en ese caso.

## Funcionalidades

- Consulta y exploración de actividad sísmica reciente.
- Mapa, filtros, estadísticas y comparación con el histórico disponible.
- Carga histórica del año 2025 y vista de reproducción aislada de los datos
  live en la ruta `/reproduccion`.
- Trazabilidad de las versiones y ejecuciones de ingesta.
- Validación de eventos, integración geográfica con Natural Earth y registro
  de mensajes rechazados en cuarentena.

## Arquitectura

```text
USGS → productor Python → Kafka → consumidor Python
     → PostgreSQL → API FastAPI → aplicación Angular
                              (Netlify; API pública mediante ngrok)
```

Docker Compose ejecuta los cinco servicios del backend: productor, Kafka,
consumidor, PostgreSQL y API. La API aplica las migraciones de base de datos
al arrancar. Kafka y PostgreSQL no publican puertos en el host; la API local
está disponible en `127.0.0.1:8000`. Angular se ejecuta en desarrollo local
o se publica como una SPA en Netlify.

## Requisitos

- Docker Engine y Docker Compose v2.
- Node.js 22.12+ o 24 y npm, para ejecutar o compilar el frontend.
- Python 3.12, solo si se van a ejecutar las pruebas del backend directamente
  en el host.
- Conexión a Internet para consultar USGS y cargar los mapas base.

## Ejecutar el backend

Desde la raíz del repositorio:

1. Crea la configuración local y define una contraseña segura para PostgreSQL:

   ```sh
   cp .env.example .env
   ```

   Edita `.env` y sustituye `POSTGRES_PASSWORD`. El fichero `.env` está
   excluido del repositorio: no compartas ni publiques sus credenciales.
2. Construye e inicia los cinco servicios:

   ```sh
   docker compose up --build -d
   docker compose ps
   ```

   Espera a que los servicios estén saludables. El API aplica las migraciones
   y prepara el catálogo geográfico durante su inicialización.
3. Comprueba el API y la documentación interactiva:

   - Salud: <http://127.0.0.1:8000/api/salud>
   - Estadísticas: <http://127.0.0.1:8000/api/estadisticas>
   - OpenAPI/Swagger: <http://127.0.0.1:8000/docs>

La ingesta live comienza automáticamente y consulta el feed de USGS cada 60
segundos. Para cargar una vez el baseline histórico mundial de 2025
(terremotos de magnitud mínima 4), o reanudar una carga interrumpida, ejecuta:

```sh
docker compose run --rm --no-deps productor \
  python -m observatorio.producer.replay \
  --year 2025 --min-magnitude 4 --event-type earthquake --interval-seconds 0
```

Las respuestas originales y los checkpoints se guardan en el volumen
`source_archives`. La carga histórica no borra los datos live ni los
volúmenes. Para más detalles sobre la operación consulta
[PIPELINE-OPERACION.md](docs/PIPELINE-OPERACION.md).

## Ejecutar el frontend en local

Con el backend en marcha:

1. Abre `frontend/public/config.json` y configura temporalmente el origen del
   API local:

   ```json
   {
     "apiBaseUrl": "http://localhost:8000"
   }
   ```

   El origen debe ser la URL base, sin `/api`. No incluyas credenciales.
   Este cambio es solo para desarrollo local: restaura la URL pública anterior
   antes de publicar o confirmar cambios.
2. Instala las dependencias y arranca Angular:

   ```sh
   cd frontend
   npm ci
   npm start
   ```
3. Abre <http://localhost:4200>. Para compilar la SPA de producción:

   ```sh
   npm run build
   ```

   Netlify publica `frontend/dist/observatorio/browser`; la configuración de
   compilación y el fallback para rutas Angular están en
   [netlify.toml](frontend/netlify.toml).

## Publicación y demostración

Netlify aloja la SPA; para que esta consulte un backend local durante la
demostración, ngrok debe exponer el puerto `8000` con una URL HTTPS. Configura
esa URL en `frontend/public/config.json` como `apiBaseUrl`, sin `/api` ni
credenciales, y añade el origen exacto de Netlify a `CORS_ALLOWED_ORIGINS` en
`.env`. Después de cambiar la configuración del frontend, reconstruye y
publica el sitio. No publiques el token de ngrok ni expongas Kafka o
PostgreSQL.

La guía con los pasos completos está en
[GUIA-DESPLIEGUE.md](docs/GUIA-DESPLIEGUE.md). Si el equipo que ejecuta el
backend se apaga o el túnel deja de estar disponible, la API no será accesible
desde el sitio público.

## Pruebas

Las pruebas del backend se ejecutan desde `backend/` (las de integración que
requieren PostgreSQL necesitan el servicio correspondiente activo):

```sh
cd backend
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q tests/unit tests/contract tests/integration
deactivate
```

Las pruebas y la compilación del frontend:

```sh
cd frontend
node --test tests/api-client.test.mjs
npm test
npm run build
```

`npm test` requiere Chrome o Chromium para ChromeHeadless. La
[memoria del proyecto](memoria-proyecto.md) recoge los resultados ejecutados
y señala expresamente las verificaciones que no se pudieron completar.

## Detener el sistema y conservar los datos

Para detener los contenedores sin borrar la base de datos, Kafka ni los
archivos originales:

```sh
docker compose down
```

Los volúmenes nombrados se conservan al detener y recrear los servicios. No
ejecutes `docker compose down -v` si quieres conservarlos. Para consultar
errores recientes:

```sh
docker compose logs --since 10m api consumidor productor kafka postgres
```

## Documentación del proyecto

- [Memoria del proyecto: decisiones, análisis, pruebas y costes](memoria-proyecto.md)
- [Enunciado y rúbrica](docs/ENUNCIADO.md)
- [Guía de entregables](docs/Guia-entregables-observatorio-sismico.md)
- [FAQ del alumnado](docs/FAQ-ALUMNADO.md)
- [Contrato de API](docs/CONTRATO-API.md)
- [Guía de despliegue](docs/GUIA-DESPLIEGUE.md)
- [Operación del pipeline](docs/PIPELINE-OPERACION.md)
- [Fuentes y licencias](docs/FUENTES-Y-LICENCIAS.md)
- [Guion del vídeo de demostración](docs/guion-video-demostracion.md)
- [Protocolo de evaluación de usabilidad](docs/evaluacion-usabilidad-007.md)
- [Validación y límites de las pruebas](docs/VALIDACION.md)
- [Roadmap](ROADMAP.md)
