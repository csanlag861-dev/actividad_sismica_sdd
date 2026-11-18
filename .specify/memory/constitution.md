<!--
Sync Impact Report
Version change: 1.0.0 → 1.1.0
Modified sections: Restricciones del proyecto (bibliotecas cartográficas del frontend)
Reason: Alinear la restricción anterior de Leaflet con la decisión aprobada para el mapa 2D (MapLibre GL JS), el complemento opcional deck.gl y la vista de globo 3D especializada con CesiumJS.
Affected documents: specs/007-exploracion-sismica-avanzada/spec.md; specs/007-exploracion-sismica-avanzada/plan.md; docs/README.md; docs/VALIDACION.md; docs/FUENTES-Y-LICENCIAS.md; docs/CONTRATO-API.md; frontend/angular.json; frontend/package.json. The Leaflet references in docs/ENUNCIADO.md and docs/FAQ-ALUMNADO.md remain unchanged and the approved feature-specific deviation is recorded in plan.md.
Required evidence: build y pruebas del frontend; contratos y pruebas de paginación/comparación; prueba de despliegue de recursos estáticos, atribución cartográfica y limpieza de las vistas WebGL.
Follow-up TODOs: ninguna.
-->

# Observatorio de actividad sísmica Constitution

## Core Principles

### I. Cumplimiento de los documentos de referencia
El alcance, los requisitos y los criterios de aceptación DEBEN seguir
el [enunciado](../../docs/ENUNCIADO.md). La API DEBE respetar el
[contrato de API](../../docs/CONTRATO-API.md). El
[FAQ del alumnado](../../docs/FAQ-ALUMNADO.md) aclara esos documentos, pero no
añade requisitos ni sustituye al enunciado o a la rúbrica. Toda desviación
DEBE justificarse y documentarse. Esta jerarquía evita requisitos implícitos
y mantiene alineadas implementación y evaluación.

### II. Procedencia y calidad explícitas de los datos
El sistema DEBE conservar la procedencia y los originales necesarios para
explicar las transformaciones, validar los datos antes de usarlos y registrar
de forma duradera los rechazos con su motivo. DEBE conservar nulos como
desconocidos, distinguir los tiempos de ocurrencia, actualización e ingesta y
tratar los datos en UTC con unidades documentadas. No DEBE inventar valores,
atribuir un país por proximidad ni presentar datos sintéticos como reales.
Estas reglas hacen los resultados auditables y evitan precisión o calidad
aparentes que los datos no sustentan.

### III. Procesamiento idempotente y revisiones correctas
El procesamiento DEBE tolerar reenvíos: una misma versión no puede aumentar
el número de eventos ni repetir efectos persistidos. El estado actual DEBE
reflejar únicamente la versión más reciente conocida, sin que una revisión
antigua sustituya una posterior; las versiones observadas deben conservarse.
Las escrituras y confirmaciones DEBEN seguir el orden transaccional definido
en el enunciado. Las agregaciones DEBEN reflejar cambios de versiones y no
contar cada mensaje como un evento nuevo. Así se preservan recuentos y
resultados correctos ante reintentos, fallos y datos tardíos.

### IV. Contratos interoperables y exposición segura
La API DEBE responder conforme al contrato, representar los datos espaciales
en GeoJSON válido y expresar valores desconocidos como `null`, no como valores
numéricos ficticios. El panel DEBE consultar la API del proyecto y mostrar
errores o desactualización sin presentarlos como resultados válidos. La
arquitectura DEBE mantener separados los servicios exigidos por el enunciado.
Credenciales y secretos NO DEBEN incluirse en el frontend, el repositorio ni
las respuestas públicas; solo se expondrá la API de consulta. Esto permite la
integración entre servicios sin divulgar recursos internos.

### V. Análisis reproducible y conclusiones proporcionadas
Las estadísticas DEBEN indicar periodo, filtros, unidades y valores ausentes.
Las comparaciones DEBEN usar periodos y filtros equivalentes, y las
agregaciones por hora se basarán en el tiempo de ocurrencia UTC. Los
resultados, mediciones y conclusiones DEBEN apoyarse en consultas o código y
en evidencias reproducibles; los datos sintéticos de prueba deben estar
identificados y separados del análisis real. El proyecto NO DEBE presentar
recuentos como predicción sísmica ni como evaluación de riesgo. Esto evita
conclusiones engañosas y hace verificable el análisis.

## Restricciones del proyecto

- Productor, Kafka, consumidor, PostgreSQL y API FastAPI DEBEN ejecutarse
  como cinco servicios separados en Docker Compose. El frontend es Angular
  y se publica como SPA; MapLibre GL JS es la biblioteca cartográfica 2D
  principal. deck.gl es un complemento opcional para visualizaciones
  geoespaciales avanzadas y CesiumJS se reserva para la experiencia de globo
  3D especializada. El acceso HTTPS público a la API sigue el mecanismo
  indicado en el enunciado.
- La recogida reciente y la carga histórica DEBEN conservar sus diferencias
  de frecuencia y procedencia. La desaparición de un evento de un feed móvil
  no es motivo suficiente para borrarlo del almacenamiento histórico.
- Los eventos que no puedan asignarse a un país DEBEN conservarse como
  «Sin país asignado». Los datos inválidos no deben aparecer como puntos
  válidos inventados.
- Los errores de consulta o de almacenamiento DEBEN comunicarse
  explícitamente. Una respuesta vacía, cero eventos o datos antiguos no
  pueden sustituir silenciosamente a un error.
- Las funciones opcionales y la complejidad adicional DEBEN justificarse; no
  se exigirán herramientas o servicios que los documentos de referencia no
  requieran.

## Flujo de desarrollo y revisión

Cada cambio DEBE comprobarse frente a los documentos de referencia y a las
pruebas de aceptación aplicables. La revisión DEBE cubrir, según el alcance,
duplicados y revisiones, valores nulos e inválidos, integración geográfica,
coherencia de filtros y manejo de errores de API o desconexión. Las
mediciones DEBEN indicar el procedimiento, los tamaños de entrada y el
entorno. La memoria o notebook DEBE distinguir observaciones de datos,
decisiones de tratamiento, limitaciones y resultados.

## Governance

Esta constitución y los tres documentos de referencia rigen las decisiones
del proyecto. Para enmendarla, se DEBE registrar la razón del cambio, los
principios y documentos afectados, y las pruebas o evidencias necesarias.
Los cambios que alteren requisitos también DEBEN actualizar el documento
afectado y comprobar la coherencia de los demás. Cuando una modificación
rompa contratos o datos existentes, la propuesta DEBE describir la migración
o justificar por qué no es necesaria.

La versión sigue SemVer: MAJOR para cambios incompatibles en principios o
reglas; MINOR para principios, secciones o requisitos nuevos o materialmente
ampliados; PATCH para aclaraciones y correcciones sin cambio normativo. Cada
revisión de una entrega o cambio DEBE verificar el cumplimiento de los
principios, los contratos, los controles de calidad y las evidencias
aplicables; las excepciones deben quedar justificadas y documentadas.

**Version**: 1.1.0 | **Ratified**: TODO(RATIFICATION_DATE): confirmar la fecha original de aprobación | **Last Amended**: 2026-11-18
