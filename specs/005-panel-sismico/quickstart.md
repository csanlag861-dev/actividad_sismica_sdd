# Quickstart: Validación del panel web

## Requisitos

- Node.js 24 (o la rama 22 soportada por la guía del proyecto) y npm.
- Chrome/Chromium disponible para ejecutar Karma en modo `ChromeHeadless`.
- API FastAPI del proyecto disponible; para prueba publicada, HTTPS de ngrok con CORS configurado para el origen exacto.
- Acceso a Internet para instalar paquetes npm y, si se activa el fondo, solicitar teselas OpenStreetMap. Las fronteras del catálogo son locales.

## Instalar y servir

```bash
cd frontend
npm ci
npm start
```

Abrir `http://localhost:4200`. Para producción, ejecutar `npm run build`; el artefacto SPA queda en `dist/observatorio/browser`, con rutas de recarga para Netlify. No requiere SSR.

Configurar `public/config.json` con la URL base HTTPS real de la API, sin sufijo `/api` ni credenciales. Para desarrollo local, usar la dirección base que corresponda al backend; no guardar credenciales ni modificar el contrato.

La configuración incluida es un marcador de posición y no apunta a una instancia real. Sin una URL accesible, el dashboard debe comunicar el error de transporte; la aplicación no sustituye la respuesta por datos de ejemplo. El tema predeterminado es oscuro y la selección claro/oscuro solo vive en memoria durante la sesión.

## Validación automatizada

Desde `frontend/`:

```bash
npm test -- --watch=false
node --test tests/api-client.test.mjs
npm run build
```

Esperado: pruebas Angular/unitarias correctas, pruebas de transporte conservan la distinción HTTP/transport, última lectura y recuperación; el build estricto genera el bundle en la ruta SPA indicada.

## Escenarios manuales end-to-end

1. Abrir la aplicación con API y verificar navegación dashboard → eventos → análisis, tema oscuro/claro y que los requests apunten solo a `GET /api/eventos`, `GET /api/estadisticas` y `GET /api/salud`.
2. Confirmar que periodo inicial muestra últimas 24 horas; seleccionar periodo UTC, magnitud mínima y país y comprobar que eventos/estadísticas envían los mismos parámetros. Navegar de eventos a análisis y volver: los controles deben conservar los filtros compartidos.
3. Seleccionar un punto y su fila: deben mostrar la misma ficha; comprobar longitud/latitud, escala de profundidad en intervalos de 10 km, leyenda, nulos y atribución del mapa.
4. Verificar los buckets horarios, país (incluido «Sin país asignado»), distribuciones y baseline de 2025; confirmar unidades, periodo, valores ausentes y casos de baseline no disponible o tasa histórica cero.
5. Esperar un ciclo de 60 segundos y verificar que eventos, estadísticas y salud vuelven a consultarse. Al cambiar filtros deben actualizarse juntos eventos y estadísticas, sin enviar los parámetros a salud. Cambiar filtros durante una solicitud y comprobar que una respuesta antigua no sustituye el estado más reciente.
6. Desconectar la API o simular HTTP 503/timeout. La UI debe mostrar error, distinguirlo de colección vacía y conservar los datos previos como posiblemente desactualizados, junto con su periodo, filtros y hora de lectura originales; no debe atribuirlos a filtros de una solicitud fallida. Al reintentar tras restaurar API, debe mostrar la respuesta reciente y limpiar el error.
7. Probar sin eventos y con el tema claro en tamaños desktop/tablet/móvil; validar teclado, foco, nombres accesibles y alternativa tabular.

Las respuestas simuladas solo se usan en tests y se identifican como tales; no se mezclan en la configuración ni en vistas de datos reales. El GeoJSON local aporta fronteras del mapa y el catálogo de países, nunca eventos sísmicos.

## Referencias

- [Contrato de UI](contracts/panel-ui.md)
- [Contrato de consumo de API](contracts/api-consumption.md)
- [Modelo de datos de presentación](data-model.md)
- [Contrato API del proyecto](../../docs/CONTRATO-API.md)
