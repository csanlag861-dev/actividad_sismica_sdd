# Roadmap integral del Observatorio de actividad sísmica

Guía secuencial para construir, probar, desplegar, documentar y defender el
proyecto. Está pensada para seguirla desde la primera lectura hasta la entrega.
No fija fechas ni duración: el enunciado indica que el calendario y la
modalidad se comunicarán en clase.

## Antes de empezar

### Fuentes y prioridad

1. El [enunciado](docs/ENUNCIADO.md) fija los requisitos, la arquitectura,
   las pruebas de aceptación, los entregables y la rúbrica.
2. El [contrato mínimo de la API](docs/CONTRATO-API.md) define las respuestas
   y reglas del servicio de consulta.
3. El [FAQ del alumnado](docs/FAQ-ALUMNADO.md) y el
   [README del material](docs/README.md) aclaran el enunciado y dan ejemplos;
   no crean requisitos nuevos ni sustituyen la rúbrica.
4. Si hay una discrepancia, no inventes una regla: aplica el documento
   autoritativo y consulta al docente cuando afecte al alcance.

### Leyenda

- **Obligatorio**: requerido explícitamente por el enunciado, su rúbrica o el
  contrato.
- **Documentar decisión**: el proyecto exige elegir una regla y explicar el
  criterio utilizado.
- **Opcional**: ampliación que no es necesaria para cumplir el proyecto.

### Cómo usar cada tarea

Cada tarea tiene identificador, tipo, prerrequisitos, actividades, resultado,
criterio de finalización, evidencia y fuente. No la marques como terminada por
haberla intentado: satisface su criterio y conserva su evidencia. Las
dependencias describen bloqueos reales; tareas independientes pueden
avanzarse en paralelo. Dentro de cada fase, conserva el orden indicado cuando
una tarea dependa del resultado de otra.

## Vista general de hitos

| Hito | Resultado | Depende de |
|---|---|---|
| H0. Comprender el encargo | Requisitos, alcance y entregables anotados | Inicio |
| H1. Preparar y explorar | Material inicial ejecutado y fuentes entendidas | H0 |
| H2. Diseñar datos y pruebas | Modelo, calidad y decisiones documentadas | H1 |
| H3. Preparar infraestructura | Cinco servicios levantan y se comunican | H2 |
| H4. Recorrido mínimo | Un evento de prueba llega a la interfaz | H3 |
| H5. Completar pipeline | Ingesta, revisiones, histórico y enriquecimiento operativos | H4 |
| H6. Completar consulta y panel | Contrato, filtros y análisis visibles | H5 |
| H7. Aceptación y mediciones | Casos funcionales, fallos, replay y costes verificados | H6 |
| H8. Desplegar y documentar | Panel publicado, documentación y evidencias listas | H7 |
| H9. Defender y entregar | Demostración repetible y entrega revisada | H8 |

---

## Fase 0 — Comprender el encargo y organizar el trabajo

**Objetivo**: saber qué se debe entregar y evitar empezar por componentes sin
requisitos claros.

**Prerrequisitos**: ninguno.

### R00 — Leer las fuentes en el orden correcto

- **Tipo**: Obligatorio.
- **Depende de**: Ninguna.
- **Actividades**:
  1. Leer las secciones de alcance, arquitectura, fuentes, ingesta, calidad,
     modelado, análisis, despliegue, pruebas, entregables y evaluación de
     [ENUNCIADO.md](docs/ENUNCIADO.md).
  2. Leer el [contrato de consulta](docs/CONTRATO-API.md) completo.
  3. Leer las preguntas de inicio y los ejemplos relevantes del
     [FAQ](docs/FAQ-ALUMNADO.md).
  4. Revisar las instrucciones de ejecución y publicación en
     [README.md](docs/README.md).
- **Resultado**: resumen de requisitos y preguntas pendientes.
- **Criterio de fin**: puedes explicar el flujo USGS → productor → Kafka →
  consumidor → PostgreSQL → servicio de consulta → panel, y distinguir lo
  obligatorio de lo opcional.
- **Evidencia**: notas propias de alcance y lista de preguntas para clase.
- **Referencia**: enunciado, secciones 1–3 y 12–13; FAQ, preguntas 1–7.

### R01 — Crear una lista de entregables y criterios de evaluación

- **Tipo**: Obligatorio.
- **Depende de**: R00.
- **Actividades**:
  1. Convertir las cinco dimensiones de la rúbrica en una lista de evidencias:
     extracción, calidad, modelado, análisis y reflexión.
  2. Registrar los elementos de entrega: código, Compose, dependencias,
     `.env.example`, URL/procedimiento del panel, diccionario/procedencia,
     modelo, memoria o notebook, conclusiones, mediciones, costes, pruebas y
     defensa.
  3. Marcar los criterios cuyo calendario o modalidad se comunicará en clase,
     sin asignar fechas supuestas.
- **Resultado**: checklist de evaluación personal.
- **Criterio de fin**: cada criterio de la rúbrica y cada entregable del
  enunciado tiene una línea en la lista.
- **Evidencia**: checklist guardado en la memoria, notebook o notas del
  proyecto.
- **Referencia**: enunciado, secciones 12–13.

## Fase 1 — Preparar el entorno y explorar el material entregado

**Objetivo**: confirmar que el material inicial funciona antes de desarrollar
el backend.

**Prerrequisitos**: H0.

### R02 — Verificar herramientas y estructura del proyecto

- **Tipo**: Obligatorio.
- **Depende de**: R00.
- **Actividades**:
  1. Revisar los requisitos de Node.js/npm indicados en el README.
  2. Identificar las carpetas y archivos proporcionados, en especial
     `frontend/`, `public/config.json`, el GeoJSON de países y el GeoJSON
     ficticio.
  3. Registrar herramientas de desarrollo disponibles para Docker y Python,
     sin sustituir el stack requerido.
  4. Si el trabajo se versiona con Git, revisar antes de subir que no hay
     secretos, dependencias instaladas ni datos binarios en el material
     versionado.
- **Resultado**: entorno y estructura comprendidos.
- **Criterio de fin**: se puede localizar el mapa, la configuración, los
  datos demo y la documentación fuente.
- **Evidencia**: lista de versiones/herramientas y estructura relevante.
- **Referencia**: README, secciones 1–2; enunciado, secciones 2–3 y 12.

### R03 — Ejecutar y verificar el mapa de demostración

- **Tipo**: Obligatorio.
- **Depende de**: R02.
- **Actividades**:
  1. Seguir los comandos de instalación y ejecución del README.
  2. Comprobar fronteras, capa base, zoom, desplazamiento y fichas emergentes.
  3. Confirmar que los puntos iniciales son ficticios y que el mapa en modo
     demo no demuestra conexión con el backend.
  4. Anotar cualquier fallo y resolverlo antes de usar el mapa como base.
- **Resultado**: frontend inicial conocido y ejecutable.
- **Criterio de fin**: el mapa abre y se visualizan las fronteras y los cuatro
  eventos demo proporcionados.
- **Evidencia**: captura del mapa y apunte de cómo iniciar/detener el frontend.
- **Referencia**: README, sección 1; FAQ, preguntas 3 y 6.

### R04 — Crear estructura de trabajo y control de secretos

- **Tipo**: Obligatorio.
- **Depende de**: R00.
- **Actividades**:
  1. Organizar el trabajo para separar backend, frontend, datos y
     documentación, respetando la estructura existente.
  2. Registrar dónde se almacenan los originales descargados y qué no se
     versiona.
  3. Preparar configuración de ejemplo sin credenciales y un mecanismo local
     para suministrar secretos que no se publique.
  4. Confirmar que las muestras sintéticas estén identificadas y separadas
     del análisis real.
- **Resultado**: espacio de trabajo ordenado y regla de secretos definida.
- **Criterio de fin**: existe un lugar documentado para cada artefacto y no se
  introduce ningún secreto en frontend o repositorio.
- **Evidencia**: árbol de carpetas y configuración de ejemplo sin valores
  sensibles.
- **Referencia**: enunciado, secciones 3, 9 y 12; README, secciones 3–4.

## Fase 2 — Entender las fuentes, definir calidad y diseñar los datos

**Objetivo**: conocer la forma y limitaciones de los datos antes de
implementar transformaciones y consultas.

**Prerrequisitos**: H1.

### R05 — Explorar y documentar el feed reciente de USGS

- **Tipo**: Obligatorio.
- **Depende de**: R00.
- **Actividades**:
  1. Obtener y examinar una respuesta de la fuente reciente indicada en el
     enunciado.
  2. Registrar campos identificadores y propiedades, geometría, tipos,
     unidades, frecuencia y ventana temporal.
  3. Distinguir `time`, `updated` e `ingested_at`, y registrar que la ventana
     móvil puede cambiar y revisar eventos.
  4. Determinar cómo excluir eventos cuyo tipo no sea `earthquake` y conservar
     el motivo de exclusión.
- **Resultado**: ficha de fuente reciente.
- **Criterio de fin**: otro integrante puede interpretar un registro y
  explicar la ventana móvil y los campos temporales sin adivinar.
- **Evidencia**: ejemplo anonímizado/ficticio o muestra con procedencia,
  diccionario de campos y fecha de extracción.
- **Referencia**: enunciado, sección 4.1.

### R06 — Planificar y descargar el conjunto histórico

- **Tipo**: Obligatorio.
- **Depende de**: R05.
- **Actividades**:
  1. Elegir y documentar ámbito, año, tipo de evento y umbral de magnitud; el
     ejemplo orientativo del enunciado es 2025, mundial, magnitud ≥4 y
     `earthquake`.
  2. Dividir la carga por meses y subdividir intervalos que excedan el límite
     de resultados de la fuente.
  3. Evitar truncamientos silenciosos y deduplicar eventos en límites
     temporales compartidos.
  4. Registrar parámetros, fecha de consulta, cantidad recibida y ubicación
     de los archivos.
  5. Documentar la instantánea temporal y su límite respecto a revisiones
     históricas pasadas.
- **Resultado**: conjunto histórico descargable y procedimiento repetible.
- **Criterio de fin**: los intervalos cubren todo el periodo declarado y sus
  conteos concilian con las respuestas guardadas.
- **Evidencia**: registro de consultas, conteos por intervalo y resumen de
  filtros.
- **Referencia**: enunciado, sección 4.2.

### R07 — Revisar catálogo geográfico, licencias y regla de asignación

- **Tipo**: Obligatorio; la regla de borde requiere decisión documentada.
- **Depende de**: R05.
- **Actividades**:
  1. Revisar `frontend/public/datos/paises.geojson` y los atributos disponibles.
  2. Comprobar que `ADM0_A3` es utilizable como identificador del catálogo;
     no asumir que es un código ISO oficial.
  3. Documentar CRS compatible, orden longitud/latitud y tratamiento de
     puntos en frontera o con varias coincidencias.
  4. Definir «Sin país asignado» para eventos marítimos o sin coincidencia;
     no asignar por cercanía.
  5. Registrar atribuciones y licencias del catálogo según la documentación
     de fuentes del proyecto.
- **Resultado**: ficha del catálogo y regla de enriquecimiento espacial.
- **Criterio de fin**: hay una regla reproducible para país, borde, múltiples
  polígonos y ausencia de asignación.
- **Evidencia**: nota de decisión espacial y referencia de licencia.
- **Referencia**: enunciado, sección 4.3; `docs/FUENTES-Y-LICENCIAS.md`.

### R08 — Definir reglas de calidad y cuarentena

- **Tipo**: Obligatorio.
- **Depende de**: R05–R07.
- **Actividades**:
  1. Definir validaciones de estructura, fechas, coordenadas finitas/en rango y
     geometría.
  2. Definir tratamiento de nulos sin reemplazarlos indiscriminadamente por
     cero; no descartar magnitudes o profundidades inusuales sin investigar.
  3. Especificar exclusiones de tipo de evento, duplicados, revisiones,
     asignación geográfica y registro de motivo.
  4. Mantener los datos de pruebas artificialmente dañados separados e
     identificados.
  5. Planificar evidencias para completitud, unicidad, validez, consistencia,
     actualidad y exactitud, justificando limitaciones.
- **Resultado**: reglas de calidad y tratamiento escritas.
- **Criterio de fin**: cada caso previsto tiene decisión, acción y evidencia
  sin eliminar silenciosamente el original.
- **Evidencia**: tabla de reglas, motivos de rechazo y consulta/código
  previsto para medir cada dimensión.
- **Referencia**: enunciado, sección 6; FAQ, preguntas 16–17.

### R09 — Diseñar modelo conceptual, lógico y físico

- **Tipo**: Obligatorio; estructura exacta requiere decisión documentada.
- **Depende de**: R05–R08.
- **Actividades**:
  1. Definir el grano de evento actual, versión observada, dimensión
     geográfica/temporal, original, consulta de ingesta y cuarentena.
  2. Identificar claves, unicidad, relaciones, valores opcionales e índices
     según las consultas esperadas.
  3. Definir cómo versionar sin reemplazar una versión más reciente por una
     atrasada.
  4. Diseñar persistencia de originales, retención y consulta reproducible.
  5. Dibujar los modelos conceptual, lógico y físico y justificar las
     decisiones.
- **Resultado**: modelo y diccionario de datos.
- **Criterio de fin**: el modelo explica origen, grano, claves, nulos,
  versiones, relaciones, índices y uso de cada tabla/entidad.
- **Evidencia**: diagramas, diccionario y decisiones documentadas.
- **Referencia**: enunciado, sección 7; FAQ, pregunta 20.

### Hito H2 — Diseño listo

Continúa cuando la ficha de fuentes, descarga histórica, regla geográfica,
reglas de calidad y modelos están documentados y no quedan decisiones
estructurales sin justificar.

## Fase 3 — Construir la infraestructura y demostrar el recorrido mínimo

**Objetivo**: poder levantar el esqueleto de los servicios y demostrar un
evento de punta a punta antes de completar todas las reglas.

**Prerrequisitos**: H2.

### R10 — Definir Compose y configuración segura

- **Tipo**: Obligatorio.
- **Depende de**: R09.
- **Actividades**:
  1. Crear `compose.yaml` con cinco servicios separados: productor, Kafka,
     consumidor, PostgreSQL y API.
  2. Decidir qué imágenes Python pueden compartirse con comandos de inicio
     separados y documentar la decisión.
  3. Crear Dockerfile(s) reproducibles, fijar dependencias y añadir
     `.env.example` sin credenciales.
  4. Configurar volúmenes persistentes y retención limitada para Kafka.
  5. Configurar healthchecks y reintentos; no depender solo del orden de
     arranque.
  6. Usar DNS/nombres de servicio dentro de Compose y documentar listeners de
     Kafka para conexiones desde host si se habilitan.
  7. Asegurar que solo la API se exponga para consulta; Kafka y PostgreSQL no
     deben publicarse por el túnel.
- **Resultado**: estructura de infraestructura reproducible.
- **Criterio de fin**: el comando de entrega
  `docker compose up --build -d` levanta los cinco servicios y los datos
  persisten al reiniciar contenedores.
- **Evidencia**: `compose.yaml`, Dockerfile(s), dependencias, `.env.example`,
  salida de `docker compose ps` y prueba de persistencia.
- **Referencia**: enunciado, secciones 2 y 9; README, sección 3.

### R11 — Verificar conectividad y servicio de base de datos

- **Tipo**: Obligatorio.
- **Depende de**: R10.
- **Actividades**:
  1. Inicializar PostgreSQL y verificar disponibilidad desde consumidor y API
     usando el nombre de servicio de Compose.
  2. Inicializar Kafka y verificar que productor y consumidor alcanzan el
     listener interno correcto.
  3. Verificar healthchecks, reintentos y logs ante servicio todavía no listo.
  4. Crear tablas/esquema inicial según el modelo aprobado.
- **Resultado**: dependencias operativas.
- **Criterio de fin**: las aplicaciones esperan/reintentan con claridad y
  pueden conectarse al broker y a la base sin usar `localhost` incorrectamente.
- **Evidencia**: logs de conexión, estado saludable y esquema inicializado.
- **Referencia**: enunciado, secciones 2, 7 y 9; FAQ, pregunta 28.

### R12 — Crear el recorrido vertical mínimo con evento de prueba

- **Tipo**: Obligatorio.
- **Depende de**: R11.
- **Actividades**:
  1. Publicar un evento ficticio/controlado usando Kafka.
  2. Consumirlo y persistirlo en PostgreSQL.
  3. Exponerlo mediante una primera respuesta de consulta conforme al contrato.
  4. Conectar localmente el panel de apoyo y comprobar el punto.
  5. Marcar el dato de prueba como sintético y no incluirlo en análisis real.
- **Resultado**: primer flujo integrado comprobable.
- **Criterio de fin**: el mismo evento controlado puede identificarse en el
  mensaje, base, respuesta y mapa; repetir la comprobación no confunde datos
  ficticios con producción.
- **Evidencia**: mensaje/log, consulta SQL, respuesta JSON y captura del mapa.
- **Referencia**: FAQ, preguntas 6–7; enunciado, secciones 2–3.

### Hito H3/H4 — Infraestructura y recorrido mínimo

Continúa cuando los cinco servicios están en ejecución, con salud observable,
y un evento de prueba completa el recorrido Kafka → PostgreSQL → consulta →
mapa.

## Fase 4 — Completar ingesta, transformación, calidad y persistencia

**Objetivo**: procesar datos reales y reintentos sin perder procedencia ni
crear eventos/versiones incorrectos.

**Prerrequisitos**: H3/H4.

### R13 — Implementar productor live de USGS

- **Tipo**: Obligatorio.
- **Depende de**: R12, R05.
- **Actividades**:
  1. Consultar el feed móvil aproximadamente cada 60 segundos con timeout.
  2. Manejar HTTP 429/5xx, errores de red y JSON con espera progresiva.
  3. Conservar respuesta original y metadatos de extracción antes de
     transformar, evitando retención ilimitada de copias idénticas.
  4. Comparar identificador y `updated` con estado persistente; publicar
     eventos nuevos y revisiones posteriores, omitiendo versiones ya
     publicadas.
  5. Publicar con ID como clave y metadatos `source`, `ingested_at`, `mode`
     y evento original.
  6. Esperar confirmación Kafka antes de marcar la versión publicada.
  7. No interpretar ausencia de la ventana móvil como eliminación del evento.
- **Resultado**: ingesta live recuperable.
- **Criterio de fin**: consultas repetidas no vuelven a publicar versiones
  idénticas; fallos no borran estado correcto ni se ocultan.
- **Evidencia**: logs de consulta, conteos, metadatos guardados y comprobación
  de reenvío tras interrupción.
- **Referencia**: enunciado, secciones 4.1 y 5.

### R14 — Implementar validación, limpieza y cuarentena del consumidor

- **Tipo**: Obligatorio.
- **Depende de**: R13, R08, R09.
- **Actividades**:
  1. Validar campos requeridos, tipos, geometría, fechas y coordenadas.
  2. Normalizar fechas a UTC conservando originales y unidades.
  3. Filtrar `properties.type != "earthquake"` con motivo de exclusión.
  4. Mantener nulos como desconocidos y valores válidos aunque sean
     inusuales, salvo regla documentada.
  5. Enviar registros no procesables a cuarentena duradera con original,
     motivo y referencia al mensaje.
  6. Confirmar el offset después de persistir resultado o cuarentena.
- **Resultado**: procesamiento explícito y recuperable de registros válidos e
  inválidos.
- **Criterio de fin**: ninguna entrada inválida se transforma en punto
  inventado ni se pierde silenciosamente; un rechazo no bloquea
  indefinidamente el resto de la cola.
- **Evidencia**: muestra de aceptado, excluido y cuarentena con motivos y
  offsets asociados.
- **Referencia**: enunciado, secciones 5–7 y 11; FAQ, preguntas 13 y 16.

### R15 — Implementar persistencia idempotente y versionada

- **Tipo**: Obligatorio.
- **Depende de**: R14, R09.
- **Actividades**:
  1. Persistir versiones distintas una sola vez mediante la clave acordada.
  2. Actualizar evento actual solo si la versión recibida es más reciente.
  3. Guardar versión y estado actual de forma transaccional.
  4. Confirmar offset después del commit de base.
  5. Comprobar recuperación tras caída entre escritura y confirmación.
  6. Asegurar que un reenvío repetido no incrementa recuentos ni efectos.
- **Resultado**: estado actual correcto con historial observado.
- **Criterio de fin**: la secuencia primera versión, duplicado, revisión nueva,
  versión antigua y segundo evento da el recuento y versión final previstos.
- **Evidencia**: resultados antes/después de base y prueba repetible de
  reinicio del consumidor.
- **Referencia**: enunciado, sección 7 y 11; FAQ, preguntas 12–14.

### R16 — Incorporar catálogo y enriquecimiento geográfico

- **Tipo**: Obligatorio; la regla exacta para fronteras se documenta.
- **Depende de**: R14, R07.
- **Actividades**:
  1. Cargar el GeoJSON de países sin alterar el original.
  2. Aplicar punto dentro de polígono en CRS compatible.
  3. Asignar atributos del catálogo, usando identificador verificado.
  4. Aplicar la decisión documentada a fronteras o coincidencias múltiples.
  5. Conservar país desconocido como «Sin país asignado», sin inferir por texto
     ni por cercanía.
- **Resultado**: eventos integrados con atributos geográficos.
- **Criterio de fin**: puntos de control sobre tierra y mar producen la
  asignación esperada y los no asignados permanecen consultables.
- **Evidencia**: casos de prueba espacial, regla de frontera y conteo de
  asignaciones/nulos.
- **Referencia**: enunciado, sección 4.3 y 7; FAQ, preguntas 18–19.

### R17 — Cargar histórico y conservar origen

- **Tipo**: Obligatorio.
- **Depende de**: R06, R14–R16.
- **Actividades**:
  1. Procesar los archivos históricos por intervalos usando reglas comunes de
     calidad/enriquecimiento.
  2. Evitar duplicados de intervalos y aplicar persistencia idempotente.
  3. Mantener los datos históricos ante desaparición del feed live.
  4. Registrar filtros, intervalos, fecha de extracción y conteos.
  5. Documentar el procedimiento para recuperar huecos tras una parada superior
     a 24 horas.
- **Resultado**: dataset histórico persistido y reproducible.
- **Criterio de fin**: el histórico queda disponible después de reiniciar y
  puede reconstruirse desde los archivos/registro sin duplicar resultados.
- **Evidencia**: conteos por intervalo, consulta de base y registro de
  procedencia.
- **Referencia**: enunciado, secciones 4.2, 5 y 7; FAQ, preguntas 15 y 21.

### Hito H5 — Pipeline completo

Continúa cuando la ingesta live e histórica, validación, cuarentena,
enriquecimiento, persistencia versionada e idempotencia pasan los casos de
control, y los originales/procedencia se conservan.

## Fase 5 — Completar servicio de consulta y panel analítico

**Objetivo**: servir el estado preparado y permitir explorar los datos con
filtros y estadísticas coherentes.

**Prerrequisitos**: H5 y modelo de datos R09.

### R18 — Implementar consulta de eventos según contrato

- **Tipo**: Obligatorio.
- **Depende de**: R15–R17.
- **Actividades**:
  1. Implementar `GET /api/eventos` con `FeatureCollection`, metadatos y una
     versión actual por evento.
  2. Respetar ventana predeterminada de últimas 24 horas.
  3. Implementar `start` inclusivo, `end` exclusivo, `min_mag` y `country_id`.
  4. Representar coordenadas como longitud, latitud, profundidad y fechas en
     milisegundos Unix UTC.
  5. Usar `null` para valores desconocidos y geometría válida obligatoria.
  6. Si se aplica límite, documentar total, `truncated` y paginación; impedir
     estadísticas globales engañosas de una muestra truncada.
- **Resultado**: endpoint de eventos compatible con el panel.
- **Criterio de fin**: respuesta cumple el contrato en colección vacía, nulos,
  filtros temporales, magnitud y país.
- **Evidencia**: ejemplos de respuestas y comprobaciones de límites/filtros.
- **Referencia**: contrato, sección `GET /api/eventos`.

### R19 — Implementar salud y estadísticas

- **Tipo**: Obligatorio.
- **Depende de**: R18.
- **Actividades**:
  1. Implementar `GET /api/salud` con estado y última ingesta, sin
     credenciales.
  2. Implementar `GET /api/estadisticas` con recuentos por hora UTC/país,
     distribuciones y comparación histórica.
  3. Hacer que los filtros equivalgan a los del mapa.
  4. Devolver en cada estadística periodo, filtros, unidad y número de
     registros sin valor.
  5. Ante fallo de base, devolver error explícito y no resultado de cero
     eventos.
- **Resultado**: endpoints operativos de salud y análisis agregado.
- **Criterio de fin**: valores agregados concuerdan con cálculos sobre una
  muestra conocida y errores no parecen resultados válidos.
- **Evidencia**: respuestas de salud/estadísticas, muestra reconciliada y
  prueba de error.
- **Referencia**: contrato, sección «Otros endpoints a implementar».

### R20 — Configurar CORS y manejo del cliente

- **Tipo**: Obligatorio.
- **Depende de**: R18.
- **Actividades**:
  1. Permitir el origen exacto de Netlify y `http://localhost:4200` en
     desarrollo.
  2. Permitir GET, OPTIONS y `ngrok-skip-browser-warning`.
  3. Verificar preflight OPTIONS; no usar `no-cors` como solución.
  4. Añadir timeout y comunicación clara de error/desactualización en el
     cliente.
  5. No añadir cookies/autenticación que no se requieren para los datos
     públicos ni secretos a `config.json`.
- **Resultado**: comunicación navegador-servicio configurada sin credenciales
  expuestas.
- **Criterio de fin**: las peticiones de desarrollo/publicación pasan CORS y
  los fallos se distinguen de respuestas vacías.
- **Evidencia**: comprobación GET/OPTIONS desde cada origen y captura de error.
- **Referencia**: contrato, sección «Acceso desde Netlify»; README, sección 3.

### R21 — Integrar mapa y ficha de evento

- **Tipo**: Obligatorio.
- **Depende de**: R18, R20.
- **Actividades**:
  1. Cambiar modo demo a API siguiendo el formato de `public/config.json`.
  2. Representar una única capa actualizada por respuesta.
  3. Mostrar ficha con datos del evento y tratar nulos visiblemente.
  4. Mantener longitud/latitud correctas al dibujar puntos y fronteras.
  5. Mantener atribución cartográfica del material base.
- **Resultado**: mapa conectado a datos reales del servicio del proyecto.
- **Criterio de fin**: puntos aparecen donde corresponde, no se acumulan al
  refrescar y una respuesta errónea no se presenta como información nueva.
- **Evidencia**: captura con datos del backend, filtros activos y estado de
  actualización.
- **Referencia**: enunciado, sección 8; README, secciones 2–3.

### R22 — Añadir filtros, tabla y visualizaciones

- **Tipo**: Obligatorio.
- **Depende de**: R19, R21.
- **Actividades**:
  1. Añadir filtros de fecha, magnitud y país/región aplicados coherentemente
     al mapa y estadísticas.
  2. Añadir tabla consultable como alternativa al mapa/color.
  3. Añadir tamaño por magnitud, color por profundidad, leyenda y tratamiento
     visible de nulos.
  4. Mostrar recuentos por hora UTC y país/subregión, incluidos eventos sin
     país.
  5. Mostrar distribuciones de magnitud/profundidad con registros sin valor.
  6. Añadir aviso y comportamiento visible ante API caída o datos desactualizados.
- **Resultado**: panel de exploración y consulta con vistas complementarias.
- **Criterio de fin**: mapa, tabla y gráficas muestran el mismo conjunto bajo
  filtros equivalentes y exponen ausentes/truncamiento.
- **Evidencia**: capturas de filtros, tabla, leyendas y estado de error.
- **Referencia**: enunciado, sección 8; contrato, filtros y truncamiento.

### R23 — Implementar comparación histórica y conclusiones

- **Tipo**: Obligatorio.
- **Depende de**: R17, R19, R22.
- **Actividades**:
  1. Comparar periodo reciente e histórico con mismo tipo, ámbito y filtros.
  2. Incluir días con cero eventos en el denominador histórico donde aplique.
  3. Explicar retrasos y que el periodo reciente puede estar incompleto.
  4. Manejar media histórica cero sin división inválida y mostrar ND cuando
     corresponda.
  5. Redactar al menos tres conclusiones con cifras, filtros, periodo y
     denominador.
  6. No presentar recuentos como predicción o evaluación de riesgo.
- **Resultado**: análisis histórico comparable y conclusiones defendibles.
- **Criterio de fin**: filtros y periodos quedan visibles; otro lector puede
  repetir la comparación y las tres conclusiones están respaldadas por datos.
- **Evidencia**: consulta/código, capturas de filtros y resultados, texto de
  conclusiones.
- **Referencia**: enunciado, sección 8; FAQ, preguntas 22–24.

### Hito H6 — Servicio y panel listos

Continúa cuando las tres operaciones de consulta, filtros, errores, estados,
tabla, mapa, distribuciones y comparación histórica se verifican con una
muestra conocida y con datos persistidos reales.

## Fase 6 — Probar aceptación, replay, rendimiento y costes

**Objetivo**: demostrar el comportamiento ante datos repetidos, revisiones,
fallos, desconexión y volumen.

**Prerrequisitos**: H6.

### R24 — Ejecutar las pruebas de aceptación del pipeline

- **Tipo**: Obligatorio.
- **Depende de**: R13–R23.
- **Actividades**:
  1. Probar evento nuevo visible en almacenamiento, consulta, mapa y análisis.
  2. Reenviar versión idéntica y comprobar que no aumenta el recuento.
  3. Enviar revisión posterior y comprobar actualización del estado y
     agregaciones afectadas.
  4. Enviar versión antigua después y comprobar que no reemplaza la actual.
  5. Probar magnitud nula, coordenada inválida en cuarentena y evento marítimo
     sin país.
  6. Reiniciar consumidor y comprobar reanudación sin duplicar efectos.
- **Resultado**: pruebas de aceptación del pipeline ejecutadas.
- **Criterio de fin**: cada caso del pipeline tiene resultado esperado,
  resultado obtenido y estado pasa/falla; las pruebas externas del túnel
  quedan reservadas para R30, después de la publicación.
- **Evidencia**: matriz firmada/fechada, logs, consultas y capturas pertinentes.
- **Referencia**: enunciado, sección 11; contrato; FAQ, preguntas 12–16 y 31.

### R25 — Crear y probar reproducción histórica aislada

- **Tipo**: Obligatorio.
- **Depende de**: R17, R24.
- **Actividades**:
  1. Seleccionar una muestra histórica ordenada por fecha.
  2. Mantener el tiempo original y registrar aparte el tiempo de reproducción.
  3. Aislar topic/esquema/tablas o usar mecanismo equivalente para no mezclar
     replay y live.
  4. Etiquetar claramente «REPRODUCCIÓN» y consultar su periodo histórico
     correcto, sin falsear fechas originales.
  5. Incluir duplicado y revisión controlada, y comprobar reutilización del
     procesamiento de consumo.
- **Resultado**: procedimiento demostrable sin depender de un sismo nuevo.
- **Criterio de fin**: replay circula por el flujo previsto, queda aislado y
  se puede distinguir en respuestas y panel.
- **Evidencia**: pasos de ejecución, conteos por separado y captura con
  indicador REPRODUCCIÓN.
- **Referencia**: enunciado, sección 11; FAQ, pregunta 32.

### R26 — Medir complejidad, tiempo y memoria

- **Tipo**: Obligatorio.
- **Depende de**: R24.
- **Actividades**:
  1. Elegir al menos tres operaciones/estructuras justificadas: búsqueda por
     ID/versión, integración geográfica y agregación por ventanas.
  2. Medir tiempo y memoria con al menos tres tamaños de entrada.
  3. Documentar equipo, datos reales o sintéticos, procedimiento y
     repetibilidad.
  4. Comparar búsqueda secuencial con diccionario o consulta con/sin índice,
     según la implementación.
  5. Razonar sobre escala de 100 millones sin mezclar réplicas sintéticas con
     resultados sísmicos reales.
- **Resultado**: análisis cuantitativo de complejidad y rendimiento.
- **Criterio de fin**: las tablas permiten reproducir cada medición y se
  explican coste medio/peor caso donde corresponda.
- **Evidencia**: script/cuaderno/consulta, datos de prueba, tablas y método.
- **Referencia**: enunciado, sección 10.

### R27 — Estimar costes y alternativas de escalado

- **Tipo**: Obligatorio.
- **Depende de**: R26.
- **Actividades**:
  1. Estimar hardware, electricidad, almacenamiento, transferencia,
     mantenimiento y tiempo de desarrollo.
  2. Separar precios observados de supuestos y registrar fecha/fuente de
     estimación.
  3. Evaluar límites de cuotas gratuitas y necesidades de disponibilidad.
  4. Proponer un escalado proporcionado sin contratar infraestructura no
     requerida ni inventar beneficios/ROI.
- **Resultado**: sección de costes y propuesta de escalado.
- **Criterio de fin**: cada cifra tiene unidad, supuesto y método; cuota gratis
  no se presenta como coste total cero.
- **Evidencia**: tabla de costes y texto de limitaciones.
- **Referencia**: enunciado, secciones 9–10; FAQ, pregunta 33.

### Hito H7 — Aceptación demostrada

Continúa cuando las pruebas del pipeline tienen resultado, el replay está
aislado, las mediciones cubren tres tamaños de entrada y los costes están
justificados. El cierre y la recuperación del túnel se verifican después de
la publicación, en R30.

## Fase 7 — Publicar y operar durante la demostración

**Objetivo**: proporcionar acceso al panel desde fuera del equipo y comprobar
el tratamiento de indisponibilidad.

**Prerrequisitos**: H7.

### R28 — Preparar configuración de publicación

- **Tipo**: Obligatorio.
- **Depende de**: R20, R24.
- **Actividades**:
  1. Completar `.env.example` sin secretos y mantener credenciales fuera de
     Git/frontend.
  2. Elegir si ngrok se ejecuta en host o contenedor y configurar ruta de API
     correspondiente.
  3. Confirmar Uvicorn en `0.0.0.0:8000` dentro del contenedor.
  4. Permitir solo los orígenes CORS exactos requeridos y mantener cerrados
     Kafka/PostgreSQL al túnel.
  5. Configurar el frontend con la URL pública HTTPS antes de compilarlo.
- **Resultado**: configuración de entorno segura y reproducible.
- **Criterio de fin**: ninguna credencial aparece en archivos públicos y la
  URL HTTPS es la que consulta el panel.
- **Evidencia**: `.env.example` revisado, configuración sin secretos y
  comprobación de puerto/orígenes.
- **Referencia**: enunciado, sección 9; contrato, «Acceso» y «Transporte»;
  README, sección 3.

### R29 — Publicar panel como SPA en Netlify

- **Tipo**: Obligatorio.
- **Depende de**: R28.
- **Actividades**:
  1. Publicar el proyecto fuente sin `node_modules`, secretos ni volúmenes.
  2. Configurar directorio base, comando de build y carpeta de publicación
     siguiendo `docs/README.md`.
  3. Configurar redirecciones SPA si son parte del material inicial.
  4. Ajustar CORS al dominio exacto publicado.
  5. Volver a desplegar cuando cambie la URL pública de configuración.
- **Resultado**: panel accesible por HTTPS.
- **Criterio de fin**: Netlify carga la SPA y solicita datos a la API sin
  errores de CORS ni configuración demo accidental.
- **Evidencia**: URL publicada, build exitoso y capturas/log de consulta.
- **Referencia**: enunciado, sección 9; README, sección 4.

### R30 — Verificar acceso externo y recuperación operativa

- **Tipo**: Obligatorio.
- **Depende de**: R29.
- **Actividades**:
  1. Abrir la URL desde otro dispositivo/red y confirmar datos del backend.
  2. Cerrar el túnel y verificar aviso visible, última lectura identificada y
     ausencia de falsos datos frescos.
  3. Reabrir túnel y confirmar que las consultas se recuperan.
  4. Parar productor manteniendo API activa y comprobar antigüedad de ingesta.
  5. Reiniciar servicios y verificar volúmenes y recuperación.
- **Resultado**: despliegue accesible y comportamiento operacional probado.
- **Criterio de fin**: quedan comprobados acceso externo, cierre, recuperación,
  productor detenido y persistencia.
- **Evidencia**: checklist de operación, capturas y horarios/resultados.
- **Referencia**: contrato, CORS; enunciado, sección 9 y pruebas de aceptación;
  FAQ, preguntas 29–31.

### Hito H8 — Publicación funcional

Continúa cuando el panel público usa HTTPS, la API responde a través del
túnel, CORS es exacto y los casos de desconexión/recuperación están probados.

## Fase 8 — Documentar, preparar entrega y defender

**Objetivo**: reunir la memoria, la evidencia y el procedimiento que permitan
reproducir y explicar el trabajo.

**Prerrequisitos**: H7; publicación H8 para incluir URL/procedimiento de
demostración.

### R31 — Escribir instrucciones reproducibles

- **Tipo**: Obligatorio.
- **Depende de**: R10, R29.
- **Actividades**:
  1. Documentar dependencias, configuración, inicialización de base y orden
     operativo.
  2. Incluir comandos para levantar y detener Compose y procedimiento para
     activar túnel.
  3. Explicar recuperación de histórico, ubicación de originales y
     persistencia.
  4. Documentar configuración de URL/CORS y acceso al panel.
  5. Registrar limitaciones conocidas y procedimiento para detectar errores.
- **Resultado**: instrucciones reproducibles de instalación y operación.
- **Criterio de fin**: otra persona puede seguirlas sin credenciales incluidas
  ni conocimiento oral no documentado.
- **Evidencia**: ejecución limpia del procedimiento y URL de panel.
- **Referencia**: enunciado, secciones 9 y 12; README, secciones 3–4.

### R32 — Completar memoria o notebook y evidencias de calidad

- **Tipo**: Obligatorio.
- **Depende de**: R08, R14–R17, R24.
- **Actividades**:
  1. Documentar fuente, periodo, filtros y conjunto analizado.
  2. Incluir código/consultas y resultados de las dimensiones de calidad
     evaluadas, con denominadores.
  3. Comparar antes/después cuando proceda y explicar decisiones y
     limitaciones.
  4. Separar mensajes, versiones, eventos actuales y datos sintéticos.
  5. Incluir modelo, diccionario, procedencia, consultas, claves e índices.
- **Resultado**: memoria o notebook con evidencias auditables.
- **Criterio de fin**: afirmaciones reproducibles tienen consulta/código y
  resultado; no se exige generador automático ni panel de calidad.
- **Evidencia**: memoria/notebook ejecutado o apartado de resultados y
  consultas.
- **Referencia**: enunciado, secciones 6–7 y 12; FAQ, pregunta 17.

### R33 — Completar análisis, conclusiones y reflexión

- **Tipo**: Obligatorio.
- **Depende de**: R23, R26–R27.
- **Actividades**:
  1. Presentar resultados de ventanas, distribuciones y comparación
     histórica.
  2. Incluir al menos tres conclusiones numéricas con periodo, filtros y
     denominador.
  3. Documentar mediciones, costes, limitaciones de datos y propuesta de
     escalado.
  4. Evitar afirmaciones de predicción o evaluación de riesgo.
- **Resultado**: sección de análisis y reflexión lista para evaluación.
- **Criterio de fin**: las conclusiones usan muestras comparables y toda cifra
  puede rastrearse a una consulta o resultado.
- **Evidencia**: capturas con filtros usados, resultados y tablas de
  mediciones/costes.
- **Referencia**: enunciado, secciones 8, 10 y 12.

### R34 — Revisar paquete de entrega

- **Tipo**: Obligatorio.
- **Depende de**: R31–R33.
- **Actividades**:
  1. Comprobar archivos fuente, Dockerfile(s), `compose.yaml`, dependencias,
     inicialización de base y `.env.example`.
  2. Comprobar URL/procedimiento de activación del panel y backend para la
     defensa.
  3. Comprobar modelo, SQL, diccionario, fuentes/licencias y registro de
     consultas.
  4. Comprobar análisis, memoria/notebook, conclusiones, mediciones, costes y
     aceptación.
  5. Eliminar secretos, `node_modules`, volúmenes binarios y datasets grandes
     no permitidos; dejar método de regeneración cuando aplique.
- **Resultado**: paquete completo y sin archivos prohibidos.
- **Criterio de fin**: todos los ítems de entrega del enunciado tienen
  ubicación y verificación.
- **Evidencia**: checklist final de entrega sin pendientes.
- **Referencia**: enunciado, sección 12; FAQ, pregunta 35.

### R35 — Ensayar la defensa

- **Tipo**: Obligatorio.
- **Depende de**: R30, R34.
- **Actividades**:
  1. Levantar contenedores y túnel con las instrucciones de R31.
  2. Abrir el panel desde otro dispositivo.
  3. Mostrar fuente, validación, evento, persistencia y consulta.
  4. Demostrar duplicado, revisión más nueva y versión antigua sin regresión.
  5. Ejecutar replay aislado con la etiqueta visible.
  6. Explicar una decisión técnica, evidencia de calidad, conclusión,
     medición, coste y limitación.
- **Resultado**: presentación repetible.
- **Criterio de fin**: demostración completa sin depender de la llegada de un
  nuevo terremoto y sin confundir replay con live.
- **Evidencia**: guion breve, checklist de defensa y capturas de respaldo.
- **Referencia**: enunciado, secciones 11–13; FAQ, preguntas 32–35.

## Fase 9 — Validación final y cierre

**Objetivo**: comprobar que no hay requisitos, pruebas, enlaces o evidencias
pendientes.

**Prerrequisitos**: H8 y R31–R35.

### R36 — Hacer revisión final de cobertura y funcionamiento

- **Tipo**: Obligatorio.
- **Depende de**: R24, R30, R34, R35.
- **Actividades**:
  1. Recorrer de nuevo las pruebas de aceptación del enunciado y comprobar
     evidencias.
  2. Verificar cobertura de las cinco dimensiones de la rúbrica.
  3. Confirmar enlaces, estado de salud, recencia de ingesta, errores,
     filtros, nulos, truncamiento y datos de replay.
  4. Repetir el arranque desde el procedimiento documentado.
  5. Registrar cualquier limitación que no se resuelva y no presentarla como
     funcionalidad completada.
- **Resultado**: entrega revisada y estado real de cada requisito.
- **Criterio de fin**: no hay requisitos obligatorios sin prueba ni
  discrepancias sin explicar; los fallos pendientes se comunican con
  claridad.
- **Evidencia**: checklist final, logs/capturas y registro de limitaciones.
- **Referencia**: enunciado, secciones 11–13; constitución del proyecto.

### Hito H9 — Proyecto listo para entregar

La entrega queda lista cuando:

- el arranque y la recuperación se han probado siguiendo la documentación;
- las pruebas de aceptación están registradas;
- el panel y el túnel pueden activarse para la defensa;
- el replay se distingue de live;
- memoria, evidencias, análisis, costes y documentación están incluidos;
- no hay secretos ni archivos que el enunciado prohíbe entregar.

---

## Dependencias y paralelismo

### Camino principal

`R00 → R01 → R02 → R03 → R05–R09 → R10–R12 → R13–R17 → R18–R23 → R24–R27
→ R28–R30 → R31–R36`

### Trabajo que puede avanzar en paralelo

- R02 y el análisis inicial de fuentes R05 pueden empezar después de R00.
- Las tareas de análisis de fuentes recientes, históricas y catálogo
  (R05–R07) pueden repartirse; las reglas de calidad/modelo se cierran
  después.
- La preparación visual del panel basado en datos demo puede continuar
  mientras se desarrolla el backend, pero las pruebas de integración esperan
  R18–R20.
- La documentación de mediciones y costes puede prepararse en paralelo con
  pruebas una vez estén definidos método y alcance; los resultados finales
  dependen de R24–R27.
- Ninguna tarea paralela debe sobrescribir el mismo archivo o avanzar sobre
  un prerrequisito aún no validado.

### Puertas de calidad

No avances al siguiente hito si:

1. Hay datos que se pierden sin registro o se convierten en valores inventados.
2. Un reenvío duplica eventos o una revisión antigua reemplaza una posterior.
3. El servicio responde cero como si fuera éxito cuando la base falla.
4. Mapa y estadísticas aplican filtros diferentes sin indicarlo.
5. Se comparan periodos o poblaciones no equivalentes.
6. La interfaz presenta datos desactualizados como recién consultados.
7. El túnel expone Kafka, PostgreSQL, secretos o rutas administrativas.
8. El replay se confunde con actividad live.

## Matriz de cobertura de aceptación

| Prueba del enunciado | Tarea(s) | Resultado requerido |
|---|---|---|
| Evento nuevo | R12, R13, R24 | Una fila actual visible en servicio, mapa y análisis |
| Repetición idéntica | R15, R24 | No aumenta número de eventos |
| Revisión posterior | R15, R24 | Cambia estado actual y agregaciones afectadas |
| Revisión antigua | R15, R24 | No sustituye a la versión más reciente |
| Magnitud nula | R08, R14, R18, R22, R24 | Se conserva y se muestra como desconocida |
| Coordenadas inválidas | R08, R14, R24 | Cuarentena con motivo, sin punto inventado |
| Evento marítimo | R07, R16, R24 | Se conserva sin país asignado |
| Reiniciar consumidor | R15, R24 | Reanuda sin duplicar efectos |
| Cerrar túnel | R30 | Panel avisa y señala última lectura |
| Reabrir túnel | R30 | Las consultas se recuperan |
| Replay histórico | R25, R35 | Procesa aislado, conserva tiempo y lleva etiqueta de replay |

## Matriz de rúbrica y entregables

| Área/entregable | Tarea(s) | Evidencia principal |
|---|---|---|
| Extracción | R05–R06, R13, R17 | Campos/unidades, consultas, conteos y automatización |
| Calidad | R08, R14, R24, R32 | Reglas, cuarentena, resultados, decisiones y limitaciones |
| Modelado | R07, R09, R15–R16 | Integración espacial, claves, versiones e índices |
| Análisis | R19, R22–R23, R33 | Ventanas, distribuciones, filtros y conclusiones |
| Reflexión | R26–R27, R33 | Complejidad, mediciones, costes y propuestas |
| Código y despliegue reproducible | R10–R11, R28–R31 | Compose, Dockerfiles, dependencias, `.env.example`, instrucciones |
| Panel y acceso | R20–R22, R28–R30 | URL publicada, CORS, error y acceso externo |
| Procedencia y diccionario | R05–R09, R17, R32 | Registro de consultas, fuentes, unidades y modelo |
| Memoria/notebook | R32–R34 | Consultas/código, resultados y decisiones |
| Aceptación y defensa | R24–R25, R30, R34–R36 | Matriz, replay y guion repetible |

## Fuera del alcance obligatorio

Estas ampliaciones pueden añadirse si hay tiempo, pero no bloquean la entrega:

- generar automáticamente un informe de calidad;
- presentar métricas de calidad en un panel específico;
- resolver exhaustivamente eliminaciones/fusiones de eventos ya fuera del feed;
- añadir Spark, Flink, Kubernetes, aprendizaje automático o un servidor cloud
  permanente;
- desplegar Kafka o PostgreSQL a través del túnel;
- calcular ROI sin beneficio medible y justificable.

La reconciliación de eventos retirados/fusionados tras salir del feed debe
documentarse como limitación del alcance mínimo.

## Checklist final para el estudiante

- [ ] Leí las fuentes y separé requisitos de ejemplos y opcionales.
- [ ] El frontend demo funciona y no lo presento como backend terminado.
- [ ] Conozco procedencia, unidades, ventanas y limitaciones de los datos.
- [ ] Tengo modelo, claves, relaciones, índices y regla geográfica justificados.
- [ ] Cinco servicios Docker Compose arrancan conjuntamente y conservan datos.
- [ ] El flujo nuevo, repetido y revisado es idempotente y versionado.
- [ ] Nulos, inválidos, cuarentena y eventos sin país tienen tratamiento visible.
- [ ] Las tres operaciones del servicio respetan `CONTRATO-API.md`.
- [ ] Mapa, tabla, filtros y estadísticas consultan datos preparados.
- [ ] Comparación histórica usa los mismos filtros y periodos comparables.
- [ ] Hay al menos tres conclusiones respaldadas por cifras y contexto.
- [ ] Ejecuté las pruebas de aceptación y conservé sus resultados.
- [ ] Replay está aislado, ordenado y etiquetado.
- [ ] Medí tiempo y memoria en tres tamaños y documenté costes/supuestos.
- [ ] Panel publicado accede a API HTTPS; CORS funciona desde otro dispositivo.
- [ ] Cierre y recuperación del túnel y reinicio de servicios fueron probados.
- [ ] Memoria/notebook, diccionario, procedencia, modelo e instrucciones están listos.
- [ ] No entrego secretos, `node_modules`, volúmenes ni grandes binarios.
- [ ] Puedo repetir la demostración y explicar una decisión técnica propia.

## Referencias

- [Enunciado y rúbrica](docs/ENUNCIADO.md)
- [Contrato mínimo del servicio de consulta](docs/CONTRATO-API.md)
- [FAQ del alumnado](docs/FAQ-ALUMNADO.md)
- [README del material inicial](docs/README.md)
- [Fuentes y licencias](docs/FUENTES-Y-LICENCIAS.md)
- [Validación del material base](docs/VALIDACION.md)
