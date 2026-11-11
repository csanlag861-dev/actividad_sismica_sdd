# Quickstart: Validar el roadmap del Observatorio sísmico

Esta guía valida que `ROADMAP.md` sea una ruta completa y utilizable. No
ejecuta ni despliega la aplicación.

## Prerrequisitos

- Acceso a la raíz del repositorio.
- Un visor Markdown.
- Disponibilidad de `ROADMAP.md`, [ENUNCIADO.md](../../docs/ENUNCIADO.md),
  [CONTRATO-API.md](../../docs/CONTRATO-API.md),
  [FAQ-ALUMNADO.md](../../docs/FAQ-ALUMNADO.md) y
  [README.md](../../docs/README.md).

## Escenario 1: recorrido de principio a fin

1. Abre `ROADMAP.md` y localiza el primer paso.
2. Sigue las fases en el orden indicado.
3. En una fase intermedia, comprueba los prerrequisitos, las subtareas y la
   evidencia de salida.
4. Localiza la fase final de publicación, documentación, entrega y defensa.

**Resultado esperado**: se entiende qué realizar después de cada hito y cómo
comprobarlo, sin depender de un plazo no especificado.

## Escenario 2: trazabilidad de requisitos

1. Revisa las cinco áreas de la rúbrica del enunciado: extracción, calidad,
   modelado, análisis y reflexión.
2. Comprueba que cada prueba de aceptación del enunciado tenga fase/tarea y
   resultado esperado: evento nuevo, duplicado, revisión nueva, revisión
   antigua, magnitud nula, coordenada inválida, evento marítimo, reinicio de
   consumidor, túnel cerrado, recuperación del túnel y replay histórico.
3. Comprueba que la matriz incluya los entregables: instrucciones y
   configuración, procedencia, modelo, análisis, mediciones/costes,
   aceptación y evidencias de reproducción.
4. Contrasta los filtros, valores nulos, truncamiento, errores y metadatos de
   consulta con el contrato.

**Resultado esperado**: 100 % de los requisitos obligatorios, pruebas de
aceptación y entregables referenciados se vinculan a trabajo y evidencia.

## Escenario 3: comprobar límites y paralelismo

1. Comprueba que los requisitos del FAQ no contradigan al enunciado.
2. Identifica tareas opcionales y decisiones que el estudiante debe justificar.
3. Comprueba que no se impongan herramientas o trabajos expresamente
   opcionales, como un generador automático o panel de calidad.
4. Verifica que el frontend de apoyo pueda trabajarse en paralelo donde no
   dependa de la API, pero que las pruebas integrales aparezcan después de
   disponer de datos y servicio de consulta.

**Resultado esperado**: ninguna ampliación se presenta como obligatoria y las
dependencias declaradas corresponden a bloqueos reales.

## Escenario 4: revisar enlaces y claridad

1. Abre todos los enlaces relativos de `ROADMAP.md`.
2. Comprueba que cada tarea use un verbo de acción y nombre un resultado.
3. Comprueba que cada tarea obligatoria incluya criterio de salida y evidencia.
4. Comprueba que las tareas estén ordenadas sin ciclos de dependencia.

**Resultado esperado**: enlaces resolubles, instrucciones accionables y
criterios de finalización verificables.

## Criterio global de aprobación

El roadmap está listo para utilizarse si pasan los cuatro escenarios y ningún
requisito obligatorio queda sin cobertura. Si falla una comprobación, corrige
el contenido del roadmap antes de usarlo como checklist de implementación.
