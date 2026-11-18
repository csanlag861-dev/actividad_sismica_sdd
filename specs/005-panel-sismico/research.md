# Research: Panel web del observatorio sísmico

## Alcance e insumos

Se revisaron la especificación aclarada, la constitución, `docs/ENUNCIADO.md`, `docs/CONTRATO-API.md`, `docs/README.md`, el sistema visual, `ROADMAP.md`, los artefactos de R18–R20, el cliente existente y el contenido actual de `frontend/`. No hay `package.json`, configuración Angular, componentes ni código de mapa en el árbol actual. El README define el arranque y la combinación de versiones del mapa que debe conservarse; Node 24 está instalado.

## Decisiones

### Base Angular y empaquetado

- **Decision**: Crear la SPA estática faltante con Angular 20.3, la estructura y scripts reproducibles que prescribe `docs/README.md`, Node 24 y salida `dist/observatorio/browser`. Conservar `config.json`, el cliente de transporte, las pruebas existentes y el GeoJSON; integrar rutas SPA en Netlify sin SSR.
- **Rationale**: Angular es obligatorio por enunciado/constitución; la guía local fija Angular 20.3 y el runtime Node 24 soportado. El árbol actual no contiene la aplicación base que describe el README, por lo que copiar o extender componentes inexistentes daría una falsa impresión de reutilización.
- **Alternatives considered**: Reemplazar Angular por una SPA nativa o actualizar a la última versión; ambas contradicen la restricción del proyecto o su combinación reproducible.

### Integración cartográfica

- **Decision**: Usar `@bluehalo/ngx-leaflet` 20.0 y Leaflet 1.9.4, la combinación descrita por el README. Mantener una instancia de mapa y reemplazar la capa de eventos en cada respuesta válida; cargar fronteras desde el GeoJSON local. Mostrar popup/ficha con texto ligado a los campos de la API y atribución de la cartografía. El tema controla las superficies/leyenda de la interfaz, no altera los datos.
- **Rationale**: El wrapper está alineado con el stack local y su sincronización de capas encaja con el ciclo de actualización requerido. Los límites de país no implican inferir país para eventos: la asignación del evento viene del backend.
- **Alternatives considered**: Cesium/3D, otro motor o redibujar mapa completo por respuesta; no son necesarios y podrían retrasar el modo 2D obligatorio. Leaflet directo es técnicamente viable si durante la implementación se descubre una integración existente que deba preservarse, pero el árbol actual no contiene tal código.
- **Sources**: [README del proyecto](../../docs/README.md); [ngx-leaflet README](https://github.com/bluehalo/ngx-leaflet/blob/master/README.md); [gestión dinámica de capas](https://github.com/bluehalo/ngx-leaflet/blob/master/docs/API.md#advanced-layer-management); [ciclo de vida Angular](https://angular.dev/guide/components/lifecycle); [referencia Leaflet 1.9.4](https://leafletjs.com/reference-1.9.4.html#layergroup-clearlayers).

### Escala de profundidad

- **Decision**: Usar exactamente los bins semiabiertos de 10 km `[k*10, (k+1)*10)` definidos en el contrato de estadísticas. El color por intervalo emplea una escala secuencial de tonos Mars Station fija entre consultas; los valores sin profundidad tienen una categoría y símbolo de leyenda propios. La asignación visual no reclasifica ni modifica la profundidad numérica original.
- **Rationale**: La aclaración del usuario fija granularidad y paleta; se reutiliza el estándar del backend, no se seleccionan rangos según la muestra ni se les atribuyen categorías científicas inventadas.
- **Alternatives considered**: Cortes dinámicos por mínimo/máximo de la respuesta, que cambian el significado del color entre consultas; intervalos científicos somero/intermedio/profundo, que no están fijados por las fuentes.

### Gráficos y tema

- **Decision**: Incorporar Apache ECharts como dependencia aprobada por este plan técnico para las series horarias, recuentos por país, distribuciones y comparación ya exigidos. Encapsularlo en componentes Angular reutilizables, importar solo módulos/tipos de gráfico necesarios y conservar periodos, unidades y valores ausentes visibles fuera del color. Aplicar tokens del tema claro/oscuro a componentes, leyendas y gráficos.
- **Rationale**: El sistema de diseño nombra ECharts como motor posible si se aprueba técnicamente; las visualizaciones solicitadas incluyen series, distribuciones y comparación, y se evita escribir un motor ad hoc o duplicar bibliotecas.
- **Alternatives considered**: Chart.js (otra dependencia sin ventaja funcional definida) o SVG/Canvas artesanal (más código y lógica propia sin necesidad). No incluir Cesium, ni métricas adicionales no devueltas por API.
- **Sources**: [sistema de diseño](../../docs/design/design-system.md); [ECharts: inicio](https://echarts.apache.org/handbook/en/get-started/); [importación modular](https://echarts.apache.org/handbook/en/basics/import/); [tamaño y disposición](https://echarts.apache.org/handbook/en/concepts/chart-size/).

### Catálogo de países y filtro

- **Decision**: Poblar el selector desde el GeoJSON local `paises.geojson` usando `ADM0_A3` como identificador y `NAME_ES` como nombre. Mantener selección exacta por `country_id`; país nulo se representa como «Sin país asignado» pero no es seleccionable como filtro de país.
- **Rationale**: El backend carga el mismo catálogo con `ADM0_A3` como `country_id`, valida códigos de tres letras contra `country`, y utiliza `NAME_ES` para el nombre público. De este modo el selector no depende de países que casualmente tengan eventos en el periodo ni de un endpoint de catálogo inexistente.
- **Alternatives considered**: Derivar opciones solo de eventos o agregaciones de la consulta actual (omitiría países válidos sin eventos en ese periodo); tratar como ISO los códigos Natural Earth (la documentación advierte que no todos lo son); crear un endpoint adicional (fuera de alcance).
- **Sources**: [catálogo local y licencias](../../docs/FUENTES-Y-LICENCIAS.md); `backend/src/observatorio/db/catalog.py`; `backend/src/observatorio/api/routes.py`.

### Filtros, UTC y consultas paralelas

- **Decision**: Presentar las fechas del filtro en UTC y serializarlas con `Z` como ISO 8601; límites `[start, end)`. El estado inicial es el periodo de últimas 24 horas. Magnitud es mínima inclusiva y país compara código exacto. Al cambiar filtros, aplicar debounce de 300 ms y cancelación lógica de respuestas anteriores, luego emitir consultas de eventos y estadísticas con el mismo conjunto de parámetros; health se consulta junto con el refresco. Los recursos se refrescan cada 60 segundos, sin reintentos del transporte. Mostrar por separado el periodo declarado por cada respuesta.
- **Rationale**: UTC elimina ambigüedad de zona/horario de verano y coincide con los buckets horarios; se respetan los defaults y semánticas de API. Consultas simultáneas y descarte de respuestas fuera de orden evitan reemplazos por un filtro anterior. La decisión de refresco conjunto fue confirmada en la aclaración.
- **Alternatives considered**: Fechas locales sin zona (no válidas para contrato), filtros derivados solo en cliente (no equivalentes) y reintentos automáticos (contrarios al contrato de transporte).

### Estados de carga, error y retención

- **Decision**: Mantener instantáneas de éxito por consulta y endpoint, asociadas a los filtros/periodo efectivos. Un error muestra mensaje y última lectura correcta con marca de desactualización; un resultado vacío es éxito distinto. Si solo una consulta de evento/estadísticas falla, no etiquetar la instantánea anterior como si perteneciera a los filtros nuevos. Ofrecer reconsulta explícita; un refresco periódico futuro sigue el ciclo normal, no es retry del transporte.
- **Rationale**: El contrato preserva el éxito anterior y distingue transporte de HTTP; la constitución prohíbe respuestas vacías o ceros con forma de éxito tras un error.
- **Alternatives considered**: Borrar los últimos datos al primer fallo o combinar valores de distintas consultas sin indicar su periodo; ambos inducen a error.

### Datos visuales y orígenes de red

- **Decision**: Eventos, salud y estadísticas solo provienen de FastAPI. Se conservan las fronteras incluidas en el repositorio y las teselas OpenStreetMap documentadas como fondo cartográfico, con atribución visible; son cartografía, no una fuente sísmica. La UI es pública, de solo lectura y no introduce autenticación ni operaciones administrativas.
- **Rationale**: Se armoniza la exclusividad de la fuente de datos del observatorio con el mapa base indicado en la guía y las obligaciones de atribución.
- **Alternatives considered**: Consultas directas a USGS, tiles no documentadas, edición o administración; contrarias a arquitectura y alcance.

### Tabla, responsive y accesibilidad

- **Decision**: Reusar la ficha seleccionada desde tabla y mapa; mantener acceso alternativo tabular, foco de teclado, etiquetas accesibles, contraste/estados semánticos y disposición responsive de escritorio a móvil. No añadir persistencia de filtros/tema en almacenamiento local; el tema se mantiene al navegar y vuelve al oscuro en una sesión nueva.
- **Rationale**: El sistema visual exige navegación accesible, tabular como alternativa y responsive. No hay requisito de persistir preferencias; la decisión mínima evita guardar estado innecesario.
- **Alternatives considered**: Hacer del color o mapa el único medio de lectura, persistir preferencias sin requisito, o crear roles/autorizaciones para el panel público.

## Restricciones conocidas

- El contrato de eventos y estadísticas no define filtro de subregión ni de tipo; no se incorporan en el cliente.
- La comparación solo es con el baseline de 2025 que devuelve la API. Las tres conclusiones obligatorias se redactan en la memoria/informe, no en la UI.
- No existe límite API de tamaño implementado ni objetivo de volumen frontend; el estado `truncated` se reconoce y se presenta explícitamente si llega, sin derivar estadísticas globales de los puntos mostrados.
- No existe objetivo de disponibilidad o latencia; el timeout de 15 s del transporte solo limita la espera del navegador.
