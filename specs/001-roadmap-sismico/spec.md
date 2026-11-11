# Feature Specification: Roadmap integral del Observatorio sísmico

**Feature Branch**: No creada

**Created**: 2026-11-11

**Status**: Draft

**Input**: User description: "Teniendo en cuenta el proyecto que tengo que construir que está definido en los siguientes archivos: #FAQ-ALUMNADO.md, #ENUNCIADO.md, #CONTRATO-API.md. Quiero que crees un ROADMAP en donde se detallen todos los pasos que tengo que crear desde el principio hasta el final, todos los pasos ordenados. Este roadmap debe recoger todas las tareas que debo hacer, e incluso subtareas si es necesario. Todas y cada una de las cosas que tengo que crear desde la primera tarea hasta el despliegue final y documentacion."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Seguir una ruta de trabajo completa (Priority: P1)

Como estudiante responsable del Observatorio de actividad sísmica, quiero un
roadmap que ordene las tareas y subtareas desde la preparación inicial hasta
la entrega, para saber qué crear, qué debe estar listo antes de avanzar y
cómo comprobar cada resultado.

**Why this priority**: Sin una secuencia y criterios de finalización, es fácil
omitir requisitos o construir componentes que todavía no tienen sus
dependencias disponibles.

**Independent Test**: Una persona puede recorrer el roadmap en orden,
identificar el siguiente trabajo realizable y verificar el resultado de cada
etapa sin consultar instrucciones contradictorias.

**Acceptance Scenarios**:

1. **Given** los tres documentos de referencia del proyecto, **When** el
   estudiante consulta el roadmap, **Then** encuentra fases ordenadas desde la
   preparación hasta la entrega y documentación final.
2. **Given** una tarea con dependencias, **When** el estudiante revisa el
   roadmap, **Then** puede identificar las tareas previas y la evidencia que
   permite darla por terminada.

---

### User Story 2 - Comprobar la cobertura de requisitos (Priority: P2)

Como estudiante, quiero relacionar cada requisito obligatorio y prueba de
aceptación con una tarea del roadmap, para reducir el riesgo de dejar fuera
parte de la rúbrica o del contrato de consulta.

**Why this priority**: La cobertura completa permite detectar omisiones antes
de la implementación y preparar evidencias para la evaluación.

**Independent Test**: Se puede rastrear cada obligación de los documentos
fuente hasta una o más tareas y comprobar su criterio de aceptación.

**Acceptance Scenarios**:

1. **Given** los requisitos de arquitectura, datos, consulta, panel, despliegue y
   entregables, **When** se revisa el roadmap, **Then** cada requisito
   obligatorio aparece en una tarea o subtarea verificable.
2. **Given** las pruebas de aceptación del enunciado, **When** se contrasta
   cada prueba con el roadmap, **Then** todas tienen una fase y un resultado
   esperado asociado.

---

### User Story 3 - Preparar la demostración y la entrega (Priority: P3)

Como estudiante, quiero que el roadmap incluya pruebas finales, publicación,
documentación y preparación de la defensa, para entregar un sistema reproducible
y explicar sus resultados y limitaciones.

**Why this priority**: Una solución funcional sin instrucciones, evidencias ni
preparación de demostración no satisface todos los entregables del proyecto.

**Independent Test**: Al completar las últimas etapas se puede levantar el
sistema siguiendo las instrucciones, comprobar los flujos principales,
acceder al panel publicado y localizar las evidencias exigidas.

**Acceptance Scenarios**:

1. **Given** que las etapas de desarrollo están completas, **When** se siguen
   las tareas finales, **Then** quedan verificados despliegue, tolerancia a
   fallos, documentación, análisis y entregables.
2. **Given** una defensa con datos en vivo no garantizados, **When** se ejecuta
   el procedimiento de demostración, **Then** se puede mostrar actividad
   identificada como reproducción sin confundirla con datos actuales.

### Edge Cases

- Si un requisito de los documentos es opcional, el roadmap lo distingue de
  los requisitos obligatorios y de los ejemplos orientativos.
- Si dos tareas pueden desarrollarse de forma independiente, el orden no debe
  presentarlas como dependencias técnicas obligatorias.
- Si una comprobación falla o un servicio no está disponible, el roadmap
  incluye un punto de diagnóstico y una condición explícita para no dar por
  terminada la etapa.
- Si no hay datos recientes o el servicio de consulta está desconectado durante la demostración,
  las tareas de verificación exigen comunicarlo y usar reproducción aislada
  cuando corresponda.
- Si una estadística histórica tiene filtros o periodo no equivalentes al
  reciente, el trabajo no se considera completo hasta corregir la comparación.
- Si existen datos nulos, inválidos, revisiones atrasadas o eventos sin país,
  las tareas deben conservar el tratamiento definido en los documentos, sin
  inventar valores ni ocultar rechazos.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El roadmap MUST estar redactado en español y organizar el trabajo
  en una secuencia de fases desde la comprensión del encargo hasta la entrega
  y documentación final.
- **FR-002**: El roadmap MUST dividir cada fase en tareas y, cuando haga falta,
  subtareas concretas, indicando dependencias y condiciones de finalización.
- **FR-003**: El roadmap MUST cubrir preparación del entorno y material
  proporcionado, entendimiento de fuentes, alcance y procedencia de datos,
  arquitectura y puesta en marcha de los servicios requeridos.
- **FR-004**: El roadmap MUST cubrir extracción reciente e histórica,
  persistencia de originales y metadatos, validación y transformación,
  cuarentena, asignación geográfica, duplicados, revisiones e idempotencia.
- **FR-005**: El roadmap MUST incluir todas las operaciones y reglas
  obligatorias del contrato de consulta, así como su verificación desde el
  panel y el manejo de errores, filtros y datos desactualizados.
- **FR-006**: El roadmap MUST cubrir mapa, tabla, filtros, estadísticas,
  comparación histórica equivalente, conclusiones y tratamiento visible de
  valores ausentes.
- **FR-007**: El roadmap MUST incluir las pruebas funcionales y de aceptación,
  los casos de fallo, reproducción aislada, mediciones de complejidad y
  rendimiento, evaluación de costes y revisión de seguridad de configuración.
- **FR-008**: El roadmap MUST cubrir puesta en marcha reproducible,
  persistencia, publicación del panel, acceso seguro al servicio de consulta, comprobación
  desde otro dispositivo, apagado/recuperación y evidencias de despliegue.
- **FR-009**: El roadmap MUST incluir memoria o notebook, modelo y diccionario
  de datos, registro de procedencia, resultados de calidad, conclusiones,
  costes, limitaciones, instrucciones de entrega y preparación de la defensa.
- **FR-010**: Cada tarea MUST incluir un resultado comprobable o evidencia
  suficiente para decidir si está terminada; las tareas que dependan de otras
  MUST identificar sus prerrequisitos.
- **FR-011**: El roadmap MUST diferenciar requisitos obligatorios, decisiones
  que debe documentar el estudiante y ampliaciones opcionales, sin elevar
  ejemplos del FAQ a requisitos nuevos.
- **FR-012**: El roadmap MUST mantener consistencia con el enunciado, el
  contrato de consulta y el FAQ, y señalar el documento de referencia pertinente
  para los grupos de tareas.

### Key Entities *(include if feature involves data)*

- **Fase del roadmap**: Grupo ordenado de trabajo con un propósito, tareas
  dependientes y una condición de salida.
- **Tarea**: Acción concreta del proyecto con prerrequisitos, subtareas cuando
  sean necesarias y resultado verificable.
- **Requisito de referencia**: Obligación, límite o criterio contenido en el
  enunciado, contrato de consulta o FAQ que debe estar cubierto por tareas.
- **Evidencia de finalización**: Prueba, resultado, documento o demostración
  que confirma que una tarea o requisito está satisfecho.
- **Entregable**: Artefacto, publicación o evidencia que se presenta al final
  del proyecto.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El roadmap contiene fases explícitas que cubren el ciclo completo:
  preparación, construcción, pruebas, despliegue, documentación y entrega.
- **SC-002**: El 100 % de los requisitos obligatorios de arquitectura, datos,
  consulta, análisis, pruebas, despliegue y entregables de los documentos fuente
  puede vincularse a una tarea o subtarea del roadmap.
- **SC-003**: El 100 % de las pruebas de aceptación enumeradas en el enunciado
  aparece asociado a una tarea de prueba y a un resultado esperado.
- **SC-004**: Todas las tareas del roadmap tienen una condición de finalización
  comprobable; todas las dependencias necesarias se presentan antes de la
  tarea dependiente.
- **SC-005**: Un lector puede identificar, sin interpretación adicional, el
  primer paso, el siguiente paso después de cada hito y las evidencias que
  necesita preparar para la evaluación.
- **SC-006**: La revisión del roadmap no encuentra requisitos opcionales
  presentados como obligatorios ni ejemplos de referencia convertidos en
  obligaciones nuevas.

## Assumptions

- El objetivo es producir una hoja de ruta accionable para que el estudiante
  construya el proyecto ya definido, no implementar el sistema ni cambiar sus
  requisitos.
- El enunciado establece la rúbrica y los requisitos; el contrato establece
  las formas de respuesta y comportamiento del servicio de consulta; el FAQ
  los aclara sin añadir obligaciones.
- El roadmap se ordenará por dependencias y puntos de verificación, no por una
  duración o fecha calendario, ya que el usuario no indicó plazo ni modalidad
  de trabajo.
- Se incluirán hitos de validación tras las etapas principales para evitar
  acumular errores hasta el despliegue.
- El roadmap debe describir decisiones y evidencias sin imponer herramientas
  adicionales a las que exigen los documentos de referencia.
