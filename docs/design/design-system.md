# Design System — Observatorio de Actividad Sísmica

**Versión:** 1.0  
**Estado:** Propuesta de identidad visual  
**Proyecto:** Observatorio de Actividad Sísmica  
**Framework:** Angular  
**Estilo:** Dark Scientific  
**Objetivo:** Definir una identidad visual coherente para toda la aplicación y servir como referencia de diseño durante su desarrollo asistido por IA.

---

## 1. Objetivo del documento

Este documento establece los principios visuales, la identidad gráfica, los componentes y las reglas de diseño que debe seguir el frontend del Observatorio de Actividad Sísmica.

La aplicación debe transmitir la sensación de una plataforma científica profesional especializada en monitorización geoespacial y análisis de actividad sísmica.

El diseño debe combinar:

- Rigor científico y claridad informativa.
- Estética tecnológica y moderna.
- Visualizaciones geográficas y estadísticas.
- Interacciones fluidas e intuitivas.
- Una experiencia visual inmersiva, sin sacrificar la usabilidad.

**Principio fundamental:** la información científica debe ser siempre la protagonista. Los efectos visuales deben ayudar a comprender los datos, nunca competir con ellos.

## 2. Dirección artística

### 2.1. Concepto visual

La identidad visual se define como **Dark Scientific — Geospatial Observatory**.

La interfaz debe inspirarse en plataformas profesionales de monitorización científica, observatorios geológicos y herramientas de análisis geoespacial.

Sus características principales son:

- Diseño oscuro, elegante y tecnológico.
- Composiciones equilibradas entre mapas, gráficos y datos.
- Paneles diferenciados mediante fondos y bordes sutiles.
- Tipografía moderna y jerarquía visual clara.
- Iconografía minimalista.
- Animaciones suaves y funcionales.
- Elementos geográficos con protagonismo visual.

Evitar:
- Apariencia de plantilla administrativa genérica.
- Exceso de tarjetas estadísticas.
- Degradados y efectos luminosos innecesarios.
- Glassmorphism aplicado indiscriminadamente.
- Colores saturados en grandes superficies.
- Decoraciones que dificulten la lectura.

### 2.2. Referencias estéticas

Se utilizarán como referencias de inspiración:

- Plataformas de monitorización geoespacial.
- Interfaces científicas y cartográficas.
- Dashboards de análisis de datos.
- Sistemas de control y observación tecnológica.

Las referencias sirven para orientar el diseño, no para copiar interfaces existentes.

## 3. Sistema de colores

La aplicación tendrá dos temas: oscuro y claro.

El tema oscuro será el predeterminado porque representa mejor la identidad científica y tecnológica definida. El usuario podrá cambiar al tema claro desde la interfaz.

Los colores deben centralizarse mediante variables CSS o tokens de diseño y utilizarse de forma consistente.

### 3.1. Tema oscuro

| Token | Color | Uso |
|---|---|---|
| Background | #0B1120 | Fondo general |
| Surface | #111827 | Tarjetas y paneles |
| Surface elevated | #1E293B | Elementos elevados |
| Surface hover | #263244 | Estados hover |
| Border | #263244 | Separadores y bordes |
| Text primary | #F8FAFC | Texto principal |
| Text secondary | #94A3B8 | Texto secundario |
| Text muted | #64748B | Información auxiliar |
| Primary | #3B82F6 | Acciones principales |
| Secondary | #22D3EE | Acentos científicos |
| Accent | #818CF8 | Elementos complementarios |

### 3.2. Tema claro

| Token | Color | Uso |
|---|---|---|
| Background | #F8FAFC | Fondo general |
| Surface | #FFFFFF | Tarjetas y paneles |
| Surface elevated | #F1F5F9 | Elementos elevados |
| Surface hover | #E2E8F0 | Estados hover |
| Border | #E2E8F0 | Separadores y bordes |
| Text primary | #0F172A | Texto principal |
| Text secondary | #475569 | Texto secundario |
| Text muted | #64748B | Información auxiliar |
| Primary | #2563EB | Acciones principales |
| Secondary | #0891B2 | Acentos científicos |
| Accent | #6366F1 | Elementos complementarios |

Los colores semánticos deberán mantener suficiente contraste en ambos temas.

### 3.3. Colores de estado

| Estado | Color | Significado |
|---|---|---|
| Success | #22C55E | Operación correcta |
| Warning | #F59E0B | Advertencia o revisión |
| Danger | #EF4444 | Error o incidencia |
| Info | #3B82F6 | Información general |

No se deben confundir los colores semánticos de la aplicación con los utilizados para representar magnitudes o profundidades sísmicas.

### 3.4. Colores de visualización sísmica

Los mapas deben diferenciar visualmente los terremotos según su profundidad, de acuerdo con el requisito funcional del proyecto.

La magnitud se representará mediante el tamaño de los círculos.

La profundidad se representará mediante una escala cromática continua o por intervalos claramente documentados.

Los valores nulos deben tener una representación diferenciada y una leyenda propia. Nunca se les asignará un valor ficticio para poder colorearlos.

La misma leyenda debe mantenerse en las diferentes visualizaciones geográficas.

## 4. Tipografía

Se utilizarán dos familias tipográficas.

### 4.1. Inter

Tipografía principal de la aplicación.

Uso:
- Títulos.
- Subtítulos.
- Navegación.
- Descripciones.
- Botones.
- Etiquetas.
- Textos generales.

### 4.2. JetBrains Mono

Tipografía secundaria para información técnica y numérica.

Uso:
- Magnitudes.
- Coordenadas geográficas.
- Identificadores de eventos.
- Fechas y timestamps.
- Valores estadísticos.
- Información técnica del sistema.

### 4.3. Jerarquía tipográfica

| Elemento | Tamaño orientativo |
|---|---|
| Título de página | 24–30 px |
| Título de sección | 18–22 px |
| Subtítulo | 14–16 px |
| Texto normal | 14 px |
| Texto secundario | 12–13 px |
| Datos destacados | 24–36 px |

La jerarquía debe ser consistente y adaptarse a diferentes resoluciones.

## 5. Layout general

### 5.1. Estructura principal

La aplicación utilizará una estructura de dashboard con tres elementos principales:

1. Sidebar lateral.
2. Header superior.
3. Área principal de contenido.

La sidebar será fija en escritorio y podrá contraerse para liberar espacio de trabajo.

El contenido deberá ocupar el espacio disponible sin generar desplazamientos horizontales innecesarios.

### 5.2. Sidebar

La navegación se organizará en grupos funcionales:

**OBSERVATORIO**
- Dashboard.
- Actividad reciente.
- Explorador sísmico.

**ANÁLISIS**
- Análisis estadístico.
- Comparador histórico.
- Placas tectónicas (si se implementa).

**SISTEMA**
- Estado del pipeline.
- Fuentes de datos.
- Exportación de datos.

**ADMINISTRACIÓN**
- Gestión de cuarentena.
- Historial de resoluciones.
- Auditoría.

Las secciones administrativas son una ampliación sujeta a la existencia de una autorización y un contrato de API adecuados. No deben exponerse operaciones administrativas mediante rutas públicas sin un modelo de seguridad definido.

La navegación debe indicar claramente la sección activa.

Se utilizarán iconos Lucide de estilo outline, manteniendo tamaños y proporciones consistentes.

### 5.3. Header

El encabezado podrá contener:

- Título de la sección actual.
- Descripción breve.
- Búsqueda, cuando tenga utilidad.
- Estado de conexión con el backend.
- Última actualización de datos.
- Selector de tema.
- Información de usuario, si existe autenticación.

No se deben mostrar indicadores de conexión que no estén respaldados por comprobaciones reales.

## 6. Componentes reutilizables

Se deberá establecer una biblioteca de componentes visuales compartidos para evitar duplicar estilos.

### 6.1. Cards

Las tarjetas tendrán:
- Fondo de superficie.
- Borde fino.
- Esquinas ligeramente redondeadas.
- Espaciado interior consistente.
- Sombras discretas, si aportan profundidad.

Se evitarán tarjetas excesivamente grandes o con decoraciones innecesarias.

### 6.2. KPI Cards

Se utilizarán para destacar métricas relevantes.

Ejemplos:
- Terremotos registrados.
- Magnitud máxima.
- Magnitud media.
- Profundidad media.
- Eventos sin país asignado.

Cada KPI debe incluir:
- Nombre del indicador.
- Valor.
- Unidad, cuando corresponda.
- Periodo al que corresponde.
- Contexto o descripción breve.

Las comparaciones porcentuales solo se mostrarán cuando exista una referencia válida.

### 6.3. Tablas

Las tablas deben ser legibles, compactas y funcionales.

Características:
- Encabezados diferenciados.
- Ordenación cuando proceda.
- Filtros.
- Paginación o tratamiento de resultados limitados.
- Estados visuales.
- Acceso al detalle del evento.
- Tratamiento explícito de valores nulos.

El mapa nunca será la única forma de consultar los terremotos.

### 6.4. Badges

Se utilizarán para representar estados como:
- Correcto.
- Pendiente.
- En revisión.
- Rechazado.
- Reprocesado.
- Error.

Los badges deben ser discretos y mantener contraste suficiente.

### 6.5. Tooltips

Se utilizarán para ampliar información sin saturar las interfaces.

Especialmente útiles en:
- Gráficos.
- Mapas.
- Indicadores estadísticos.
- Iconos de acciones.
- Información técnica.

### 6.6. Modales y paneles laterales

Se utilizarán para mostrar información complementaria, detalles de eventos y acciones que requieran confirmación.

No se deben utilizar modales para información extensa que merezca una página independiente.

## 7. Diseño de las pantallas

### 7.1. Dashboard principal

Será la pantalla de entrada al observatorio.

La composición debe ser equilibrada entre mapas, estadísticas y gráficos.

Distribución propuesta:

- Cabecera con título y periodo consultado.
- Fila de indicadores principales.
- Mapa mundial con protagonismo visual.
- Gráfico de actividad sísmica temporal.
- Distribución por magnitud.
- Resumen de profundidad.
- Tabla o lista de últimos eventos.

El mapa no debe ocupar toda la pantalla ni quedar reducido a una tarjeta secundaria.

La pantalla debe permitir entender rápidamente la situación de actividad sísmica del periodo seleccionado.

### 7.2. Explorador sísmico

Será una de las pantallas principales.

Debe incorporar:
- Mapa interactivo amplio.
- Filtros de fecha.
- Filtros de magnitud.
- Filtros geográficos.
- Leyenda de magnitud y profundidad.
- Ficha del terremoto seleccionado.
- Tabla alternativa de eventos.

Los filtros deben mantener coherencia entre mapa y resultados tabulares.

#### Modo 2D

La tecnología base será Leaflet.

Debe conservar el mapa proporcionado en el proyecto, incluyendo el fondo, las fronteras y la representación de eventos, ampliando sus capacidades sin reconstruirlo innecesariamente.

La representación deberá respetar:
- Tamaño proporcional a magnitud.
- Color por profundidad.
- Leyenda.
- Nulos.
- Selección de eventos.
- Información emergente.

#### Modo 3D

Se contempla como ampliación visual mediante CesiumJS.

La experiencia debe permitir explorar un globo terrestre tridimensional con terremotos georreferenciados.

Posibles elementos:
- Rotación y navegación.
- Marcadores sísmicos.
- Selección de eventos.
- Visualización de capas.
- Representación de profundidad.

La representación de profundidad deberá distinguir claramente los valores reales de cualquier exageración visual utilizada.

La implementación queda condicionada a su aprobación como funcionalidad independiente, a la disponibilidad de datos adecuados y a la evaluación de rendimiento. No debe sustituir ni retrasar el modo 2D obligatorio.

### 7.3. Análisis estadístico

La sección tendrá una composición orientada a la interpretación de datos.

Debe incluir:
- Distribución de magnitudes.
- Distribución de profundidades.
- Recuentos por país o subregión.
- Evolución por ventanas temporales.
- Comparación histórica equivalente.
- Información sobre valores nulos.

Cada gráfico debe incluir:
- Título.
- Descripción.
- Unidades.
- Periodo.
- Leyenda.
- Tooltips.
- Tratamiento de datos ausentes.

Los gráficos deben ser interactivos, pero no excesivamente decorativos.

### 7.4. Comparador histórico

Permitirá comparar periodos equivalentes.

La interfaz deberá mostrar:
- Periodos seleccionados.
- Indicadores comparativos.
- Diferencias absolutas y porcentuales cuando sean válidas.
- Gráficos comparativos.
- Filtros compartidos.

Se deben mostrar advertencias cuando un periodo todavía esté incompleto o existan diferencias de cobertura.

### 7.5. Monitorización del sistema

Esta sección estará orientada al funcionamiento técnico del observatorio.

Podrá mostrar:
- Último acceso correcto a la API.
- Última ingesta correcta de USGS.
- Periodo consultado.
- Estado de actualización.
- Errores de conexión.
- Información de procesamiento disponible mediante la API.

No se deben presentar datos de Kafka, PostgreSQL o del pipeline como información en tiempo real si no existe una fuente que los proporcione.

### 7.6. Administración y cuarentena

Se contempla una interfaz específica para gestionar eventos en cuarentena.

La composición podrá incluir:
- Tabla de eventos pendientes.
- Motivo de cuarentena.
- Datos originales.
- Información de validación.
- Acciones autorizadas.
- Historial de resoluciones.

Las operaciones de resolución y reprocesamiento deberán depender de funcionalidades reales del backend y de permisos expresamente definidos.

No se deben inventar endpoints ni permitir modificaciones directas de datos originales desde el frontend.

Esta sección no forma parte del panel público obligatorio y deberá implementarse únicamente cuando exista una especificación funcional y de seguridad aprobada.

## 8. Sistema de gráficos

Se priorizará una visualización clara y científicamente correcta.

Los gráficos deberán:
- Mantener la identidad cromática.
- Evitar escalas engañosas.
- Mostrar unidades.
- Diferenciar ausencia de datos de valor cero.
- Mostrar el periodo analizado.
- Respetar los filtros globales.
- Adaptarse a diferentes tamaños de pantalla.

Apache ECharts puede utilizarse como motor de visualización, siempre que su incorporación sea compatible con el proyecto existente y se apruebe en la especificación técnica.

La integración Angular deberá realizarse mediante componentes reutilizables.

## 9. Sistema de mapas

Leaflet será el motor cartográfico del modo 2D.

El mapa deberá:
- Utilizar la información geográfica disponible.
- Mostrar fronteras y terremotos.
- Mantener una leyenda permanente o fácilmente accesible.
- Permitir seleccionar eventos.
- Mostrar información detallada.
- Adaptarse al tema visual.

El mapa no debe introducir inferencias geográficas que el backend no haya realizado.

Los eventos sin país asignado deben conservarse y visualizarse correctamente.

La capa de placas tectónicas se considera una ampliación opcional, condicionada a disponer de una fuente geográfica adecuada y documentada.

## 10. Interacciones y animaciones

La experiencia debe ser visual e inmersiva, pero mantener una finalidad funcional.

Se permitirán:
- Transiciones suaves entre estados.
- Animaciones de entrada discretas.
- Efectos hover.
- Realce de eventos seleccionados.
- Transiciones en gráficos.
- Animaciones de navegación en el globo 3D.

Las transiciones generales tendrán una duración orientativa de 150–250 ms.

Evitar:
- Animaciones constantes sin utilidad.
- Parpadeos.
- Movimientos que dificulten la lectura.
- Efectos excesivos en tarjetas y botones.

Se respetará la preferencia del sistema para reducir movimiento (`prefers-reduced-motion`).

## 11. Diseño responsive

La aplicación debe ser utilizable en escritorio, tablet y móvil.

### Escritorio
- Sidebar visible.
- Dashboard en varias columnas.
- Mapas amplios.
- Gráficos distribuidos en rejilla.

### Tablet
- Sidebar colapsable.
- Reorganización de tarjetas.
- Gráficos en dos columnas cuando sea posible.
- Filtros adaptados.

### Móvil
- Navegación compacta.
- Contenido en una columna.
- Tablas con desplazamiento controlado o presentación alternativa.
- Filtros en panel desplegable.
- Mapas adaptados al tamaño disponible.

La visualización 3D deberá disponer de controles táctiles y una alternativa de consulta accesible.

## 12. Accesibilidad

Se deberán respetar buenas prácticas de accesibilidad:

- Contraste suficiente.
- Navegación mediante teclado.
- Indicadores de foco visibles.
- Etiquetas accesibles.
- Iconos acompañados de información cuando sea necesario.
- No depender exclusivamente del color.
- Respeto a la reducción de movimiento.
- Alternativas tabulares a las visualizaciones geográficas.

Se procurará cumplir WCAG 2.2 nivel AA.

## 13. Tecnologías frontend

El diseño se desarrollará respetando el stack y las dependencias existentes.

| Tecnología | Responsabilidad |
|---|---|
| Angular | Framework de aplicación |
| TypeScript | Tipado y lógica |
| Tailwind CSS | Sistema de estilos |
| Lucide | Iconografía |
| Leaflet | Mapas 2D |
| Apache ECharts | Gráficos y visualizaciones |
| CesiumJS | Globo 3D opcional |
| date-fns | Formateo de fechas |

Antes de añadir dependencias, se deberá inspeccionar `package.json`, el archivo de bloqueo, la versión de Angular y el código proporcionado.

No se actualizarán versiones principales ni se sustituirán dependencias existentes sin justificación y aprobación.

Angular CDK podrá incorporarse cuando aporte una necesidad concreta de accesibilidad o comportamiento de componentes.

No se incorporarán bibliotecas de componentes visuales que impongan una identidad gráfica diferente de la definida en este documento.

## 14. Arquitectura visual y reutilización

Los componentes visuales deben ser independientes de la lógica de negocio y de la comunicación con la API.

Se recomienda organizar el frontend por funcionalidades y mantener una capa compartida para elementos comunes.

Ejemplo orientativo:

```text
src/app/
├── core/
│   ├── services/
│   ├── models/
│   └── interceptors/
│
├── features/
│   ├── dashboard/
│   ├── earthquake-explorer/
│   ├── analytics/
│   ├── system-monitoring/
│   └── administration/
│
└── shared/
    ├── components/
    ├── layouts/
    ├── charts/
    └── styles/
```

Esta estructura es orientativa y deberá adaptarse a la organización real del proyecto Angular.

Se evitará duplicar componentes, estilos, escalas cromáticas y lógica de presentación.

## 15. Integración con el backend

El frontend consumirá exclusivamente la API FastAPI.

No deberá consultar directamente USGS para obtener los datos del observatorio.

Los componentes deben representar correctamente:
- Datos reales.
- Valores nulos.
- Resultados vacíos.
- Errores de comunicación.
- Datos desactualizados.
- Resultados limitados.
- Diferencias entre live y replay.

Todos los filtros compartidos deberán aplicarse de forma coherente a los elementos que representen el mismo conjunto de datos.

El frontend no deberá modificar ni reinterpretar arbitrariamente los datos procesados.

Se respetarán estrictamente los endpoints, parámetros, unidades, respuestas y limitaciones definidos en `CONTRATO-API.md`.

El modo demo existente debe identificarse claramente como demostración con datos sintéticos. Nunca se mezclarán silenciosamente eventos ficticios y reales.

## 16. Estados de interfaz

Todas las pantallas que dependan de información externa deben contemplar:

**Loading:** mostrar un indicador de carga apropiado.

**Success:** presentar los datos correctamente.

**Empty:** explicar que no existen resultados para los filtros seleccionados.

**Error:** informar del problema sin mostrar información ficticia.

**Stale:** indicar que los datos mostrados no están actualizados.

**Partial:** informar cuando exista información incompleta o limitada.

Los estados deben mantener la identidad visual de la aplicación y utilizar mensajes comprensibles.

## 17. Reglas obligatorias para los agentes de IA

Cualquier agente que implemente funcionalidades frontend deberá cumplir estas reglas:

1. Leer este documento antes de desarrollar o modificar componentes visuales.
2. Inspeccionar la implementación existente antes de realizar cambios.
3. Respetar la identidad visual y los tokens definidos.
4. Reutilizar los componentes existentes siempre que sea posible.
5. No introducir bibliotecas o dependencias sin justificación.
6. No modificar contratos de API ni requisitos funcionales desde una tarea de diseño.
7. No inventar datos, estados, indicadores ni funcionalidades.
8. Mantener la coherencia visual entre todas las secciones.
9. Implementar los estados de carga, error, vacío y desactualización.
10. Garantizar la accesibilidad y el comportamiento responsive.
11. Priorizar la claridad de los datos sobre los efectos visuales.
12. No sustituir tecnologías obligatorias por alternativas sin aprobación.
13. No presentar ampliaciones opcionales como funcionalidades ya implementadas.
14. Comprobar visualmente los cambios realizados y documentar las limitaciones.

## 18. Criterios de aceptación visual

El diseño se considerará correctamente aplicado cuando:

- Todas las secciones compartan una identidad visual reconocible.
- Los temas oscuro y claro funcionen correctamente.
- La navegación sea consistente.
- Los colores y tipografías respeten el sistema definido.
- Las tarjetas, tablas y gráficos mantengan patrones comunes.
- El mapa sea un elemento visual importante y equilibrado.
- Los gráficos sean comprensibles y científicamente correctos.
- Los estados de error y ausencia de datos estén contemplados.
- La interfaz sea responsive.
- Las interacciones sean accesibles.
- No existan componentes visuales duplicados innecesariamente.
- La aplicación no introduzca funcionalidades contrarias a los requisitos originales.

---

## 19. Principio de prioridad documental

Este documento define exclusivamente las decisiones de diseño y presentación.

En caso de discrepancia, se aplicará el siguiente orden:

1. `constitution.md` y las reglas generales del proyecto.
2. `ENUNCIADO.md` y demás fuentes de verdad funcionales.
3. `CONTRATO-API.md` para la integración frontend-backend.
4. Especificaciones funcionales aprobadas de cada característica.
5. Este documento de diseño.
6. Preferencias de implementación del agente.

Una decisión visual nunca podrá justificar la modificación unilateral de requisitos funcionales, datos, contratos o arquitectura.

Cualquier ampliación, como CesiumJS, administración avanzada, placas tectónicas o reproducción visual, deberá contar con su correspondiente definición funcional antes de implementarse.

**Resultado esperado:** un observatorio científico moderno, inmersivo y profesional, donde mapas, estadísticas y datos sísmicos convivan bajo una identidad visual coherente y una experiencia de usuario cuidada.