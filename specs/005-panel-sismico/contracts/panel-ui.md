# Contrato de interfaz: Panel sísmico

## Navegación

La SPA expone tres vistas públicas, solo lectura:

| Ruta | Contenido |
|---|---|
| `/` | Dashboard de entrada con periodo efectivo, estado de servicio/ingesta, resumen de datos consultados y accesos a exploración y análisis. |
| `/eventos` | Filtros compartidos, mapa Leaflet, tabla alternativa y ficha del evento seleccionado. |
| `/analisis` | Recuentos UTC/país, distribuciones y comparación histórica devueltos por la API. |

La navegación conserva un tema compartido. Dark Mars Station es el tema predeterminado; el toggle ofrece light Mars Station. No hay persistencia entre visitas. La navegación móvil mantiene las mismas vistas y acciones.

## Estados de consulta

Cada recurso distingue:

- **Cargando**: indicador y controles comprensibles; no mostrar cero como placeholder.
- **Éxito con datos**: presentar valores y su periodo/filtros.
- **Éxito vacío**: mensaje de que no hay eventos para la consulta; nunca se trata como error.
- **Error HTTP**: mostrar el estado/código seguro recibido, mensaje legible y acción de reintento.
- **Error de transporte/timeout**: indicar que no se obtuvo una respuesta HTTP accesible; no afirmar que CORS sea la causa.
- **Respuesta malformada/filtro rechazado**: explicar que la respuesta incumple el contrato o que la API rechazó la consulta y ofrecer reintentar la consulta vigente; un periodo inválido se explica antes de enviar y no inicia una solicitud.
- **Posible desactualización**: si falla una consulta posterior, conservar e identificar su última respuesta correcta, periodo/filtros y hora de lectura.
- **Truncamiento**: mostrar la metadata declarada; no afirmar recuentos globales basados en las features retornadas. No se inventa mecanismo de paginación.

No usar umbral de antigüedad de `last_ingestion` para declarar caída. `GET /api/salud` determina disponibilidad según su respuesta contractual; la frescura se presenta por separado.

## Filtros y sincronización

- Controles de periodo UTC (`start` inclusivo, `end` exclusivo), magnitud mínima y país.
- La opción inicial representa las últimas 24 horas y omite ambos límites para que el default móvil del backend avance con cada actualización.
- Periodo personalizado usa timestamps UTC ISO 8601; requiere inicio anterior al fin.
- Magnitud nula no cumple `min_mag`.
- País ofrece el catálogo local `ADM0_A3`/`NAME_ES`, compatible con `country_id`; «Sin país asignado» se muestra en resultados pero no se ofrece como filtro.
- No hay filtros regionales/subregionales o de tipo de magnitud en esta entrega.
- Cambiar un filtro inicia consultas equivalentes de eventos y estadísticas tras 300 ms de debounce; respuestas de una consulta anterior se descartan o cancelan.
- Los filtros confirmados se conservan al navegar entre exploración y análisis y sus controles muestran los valores compartidos vigentes.
- Cada 60 segundos la aplicación consulta eventos, estadísticas y salud. El transporte no realiza reintentos por su cuenta. La acción visible de reintentar inicia una nueva consulta del conjunto actual.
- Eventos, estadísticas y salud son requests independientes: cada respuesta conserva su estado, `queryId`, contexto de consulta y hora. Eventos muestran el intervalo y filtros enviados o, sin intervalo, el periodo móvil predeterminado de 24 horas sin inventar sus límites exactos ni tomar el periodo de estadísticas; estadísticas muestran periodo y filtros devueltos por su endpoint. La UI nunca presenta un resultado de un periodo anterior como si fuera el nuevo.

## Mapa y tabla

- El mapa conserva Leaflet, los límites del GeoJSON local y la atribución visible del mapa base.
- Los datos de evento proceden solo de la respuesta del backend. El mapa no calcula ni asigna países.
- Solo se dibujan posiciones GeoJSON con longitud en `[-180, 180]` y latitud en `[-90, 90]`; Leaflet recibe los argumentos en el orden que requiere su API.
- El radio de marcador en píxeles es `clamp(4 + 2 × max(0, magnitud), 4, 18)`. Magnitud nula usa radio de 5 px, contorno discontinuo y estilo neutral, sin sustituir el valor ausente por una magnitud.
- Color de profundidad usa bins semiabiertos de 10 km `[k*10, (k+1)*10)` con escala secuencial fija Mars Station. Valores negativos se etiquetan como valores recibidos fuera de los bins, no como una profundidad válida; los nulos tienen símbolo y etiqueta separados.
- La leyenda del mapa identifica la correspondencia del tamaño, los intervalos presentes y las categorías negativas/nulas cuando corresponda.
- Seleccionar un punto o fila abre la misma ficha; datos ausentes se rotulan como desconocidos. La nueva respuesta reemplaza la capa anterior.
- Tabla permite consultar eventos sin mapa/color; presenta datos disponibles y nulos, y su selección abre la ficha. No calcula estadísticas del total.

## Estadísticas y comparación

- Los gráficos se alimentan solo de `GET /api/estadisticas`.
- Cada visualización muestra título, periodo, filtros y unidades. Valores ausentes y cero se distinguen.
- Recuentos por hora UTC y por país, incluida la categoría null «Sin país asignado»; distribuciones de magnitud y profundidad declaran bins, denominadores y ausentes.
- Comparación expone baseline/periodo, disponibilidad, tasas, unidad eventos/día y diferencia/ratio solo si vienen en la respuesta. Baseline no disponible y tasa histórica cero no se representan como una comparación igual a cero.
- No presentar recuentos como predicción o riesgo. Las tres conclusiones cuantitativas se entregan en la memoria/informe, no se generan en la interfaz.

## Accesibilidad y responsive

- Los enlaces de navegación, el selector de tema, los controles de filtro, las acciones de actualizar/reintentar, la selección de eventos desde la tabla y los controles de divulgación son operables por teclado, tienen nombre accesible y foco visible.
- Ninguna distinción depende solo del color; mapa y gráficos tienen alternativas textuales/tabulares.
- Viewports móvil (320–760 px), tablet (761–1024 px) y escritorio (más de 1024 px) reorganizan navegación, filtros, tabla, mapa y visualizaciones sin ocultar filtros, valores ni acciones esenciales ni provocar desplazamiento horizontal de página; la tabla puede desplazarse dentro de su contenedor.
- Respeta reducción de movimiento del sistema.

## Límites de red

La configuración pública contiene únicamente `apiBaseUrl`. Datos del observatorio solo se obtienen de la API FastAPI. La capa de fondo de mapa y el catálogo local no son fuentes de eventos; atribuir las teselas de OpenStreetMap según su política. No se envían credenciales/cookies ni se exponen rutas internas.
