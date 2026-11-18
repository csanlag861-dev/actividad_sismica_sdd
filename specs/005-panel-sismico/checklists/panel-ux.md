# Panel UX Checklist: Observatorio de Actividad Sísmica

**Purpose**: Revisar la integridad, claridad, consistencia y cobertura de calidad de los requisitos de interfaz del panel.
**Created**: 2026-11-17
**Feature**: [spec.md](../spec.md)

**Note**: Esta checklist custom valida la redacción de requisitos del panel; no es una lista de pruebas de implementación.
**Review Ownership**: Esta checklist es un artefacto de revisión de requisitos propiedad del revisor. Marca un ítem `[x]` solo cuando el revisor determine que el criterio de calidad de requisitos está satisfecho.
**Marker Semantics**: `[x]` significa que el criterio fue revisado y satisfecho en cuanto a la calidad de requisitos. No significa que la implementación esté terminada.

## Requirement Completeness

- [x] CHK001 ¿Están definidos el propósito y el contenido esencial de cada destino de navegación —dashboard, eventos y análisis—? [Completeness, Spec §User Story 1, FR-001]
- [x] CHK002 ¿Se especifican los atributos, unidades y reglas de valores ausentes que deben cubrir la ficha y la tabla? [Completeness, Spec §User Story 2, FR-005, FR-007]
- [x] CHK003 ¿Se enumeran las familias de estadísticas y los campos de comparación que forman el alcance de análisis, sin exigir indicadores no devueltos por la API? [Completeness, Spec §FR-008–FR-009]
- [x] CHK004 ¿Está definida una alternativa textual o tabular para las visualizaciones que dependen del mapa o del color? [Completeness, Spec §FR-007, FR-013]
- [x] CHK029 ¿Se especifica si los filtros compartidos deben conservarse al pasar entre exploración y análisis y cómo se relacionan con los valores visibles en sus formularios? [Completeness, Spec §FR-006, Tasks T043]

## Requirement Clarity

- [x] CHK005 ¿Está cuantificada la correspondencia entre magnitud y tamaño del marcador, incluidos magnitud nula y valores extremos? [Clarity, Spec §FR-004]
- [x] CHK006 ¿Está especificado cómo se asigna un color visible a cada intervalo de profundidad de 10 km, incluido el caso de profundidades negativas, sin atribuirles categorías científicas? [Clarity, Spec §FR-004]
- [x] CHK007 ¿Los requisitos identifican qué resumen concreto del periodo y de los datos debe ofrecer el dashboard, o delimitan explícitamente ese resumen a información disponible en las respuestas? [Gap, Spec §User Story 1, FR-001]
- [x] CHK008 ¿Está clara la diferencia entre el periodo móvil predeterminado de 24 horas y un periodo personalizado, incluidos UTC y los límites inclusivo/exclusivo? [Clarity, Spec §FR-006]
- [x] CHK009 ¿Se define qué contexto de consulta —periodo, filtros y hora de lectura— acompaña a cada resultado retenido tras un fallo? [Clarity, Spec §FR-010–FR-012]
- [x] CHK030 ¿Se aclara que, mientras hay una consulta nueva en curso, los datos retenidos mantienen el contexto de la respuesta que los produjo y no el de los filtros solicitados más recientemente? [Clarity, Spec §FR-010–FR-011, Tasks T042]

## Requirement Consistency

- [x] CHK010 ¿Coinciden los requisitos sobre filtros compartidos en eventos, estadísticas y comparación con el alcance contractual confirmado de `start`, `end`, `min_mag` y `country_id`? [Consistency, Spec §FR-006, FR-009]
- [x] CHK011 ¿Son coherentes entre sí el refresco conjunto de 60 segundos, el cambio de filtros, el reintento explícito y la ausencia de reintentos del transporte? [Consistency, Spec §FR-011–FR-012]
- [x] CHK012 ¿La escala cartográfica de 10 km y las distribuciones estadísticas usan límites semiabiertos compatibles, sin redefinir bins en el frontend? [Consistency, Spec §User Story 2, FR-004, FR-008]
- [x] CHK013 ¿Se distingue consistentemente la responsabilidad del panel de consulta de la obligación académica de documentar tres conclusiones en la memoria/informe? [Consistency, Spec §FR-009, Clarifications, Confirmed scope and constraints]

## Acceptance Criteria Quality

- [x] CHK014 ¿Los criterios de éxito permiten evaluar objetivamente el uso del dashboard, la selección de eventos y la lectura de la comparación dentro de los límites temporales indicados? [Measurability, Spec §Success Criteria]
- [x] CHK015 ¿Los criterios de éxito cubren la consistencia de periodo/filtros y diferencian de forma medible vacío, truncamiento, error y posible desactualización? [Acceptance Criteria, Spec §SC-002–SC-004]

## Scenario Coverage

- [x] CHK016 ¿Las historias cubren los recorridos principal, alternativo tabular, consulta vacía, fallo y recuperación sin presentar datos antiguos como actuales? [Coverage, Spec §User Story 1–4, Edge Cases]
- [x] CHK017 ¿Se especifica qué ocurre con una respuesta tardía de filtros previos o con fallos parciales entre consultas independientes de eventos y estadísticas? [Coverage, Gap, Spec §FR-010–FR-012]
- [x] CHK018 ¿Se cubren las tareas esenciales para teclado, pantallas móviles y cambios de tema en los criterios de aceptación, además de mencionarlas como restricciones? [Coverage, Spec §FR-002, FR-013, SC-005]
- [x] CHK031 ¿Los requisitos explican qué periodo y filtros se atribuyen por separado a eventos y estadísticas cuando sus respuestas independientes no declaran el mismo contexto efectivo? [Coverage, Clarity, Spec §FR-006, FR-010–FR-012, SC-002, Tasks T044]

## Edge Case Coverage

- [x] CHK019 ¿Los requisitos definen el mensaje y la acción disponible para un intervalo inválido, un filtro rechazado o una respuesta malformada? [Coverage, Edge Case, Spec §FR-006, Edge Cases]
- [x] CHK020 ¿Se documenta cómo presentar el truncamiento y sus metadatos declarados por la API, y cómo evitar inferencias globales a partir de una muestra sin inventar un mecanismo de paginación? [Clarity, Spec §FR-010, Assumptions]
- [x] CHK021 ¿Se especifica el tratamiento de un país nulo en mapa, tabla, estadística y filtro sin inferir un país por proximidad? [Consistency, Spec §FR-005–FR-008, Edge Cases]

## Non-Functional Requirements

- [x] CHK022 ¿Los requisitos de accesibilidad concretan qué elementos son operables por teclado, cómo se identifica el foco y cómo se comunica la información sin depender del color? [Completeness, Spec §FR-013]
- [x] CHK023 ¿El alcance responsive identifica condiciones verificables para escritorio, tablet y móvil sin ocultar información esencial? [Measurability, Spec §FR-013, SC-005]
- [x] CHK024 ¿Se explicita si no hay objetivos de latencia, volumen, disponibilidad o carga visual para que no se interpreten como garantías implícitas? [Assumption, Spec §Success Criteria, Assumptions]

## Dependencies & Assumptions

- [x] CHK025 ¿Están identificados como dependencias el contrato API, la configuración pública sin secretos, el catálogo geográfico local y la cartografía externa con atribución? [Dependency, Spec §FR-003–FR-004, Assumptions]
- [x] CHK026 ¿Se distinguen los datos reales del servicio de las muestras sintéticas y se excluye su mezcla silenciosa en los requisitos? [Completeness, Spec §FR-003, Assumptions]

## Ambiguities & Conflicts

- [x] CHK027 ¿Se evita que términos como «resumen», «legible», «responsive» o «sin ocultar información esencial» sean la única base de aceptación sin ejemplos o criterios observables? [Ambiguity, Spec §User Story 1, FR-002, FR-013]
- [x] CHK028 ¿Se declara explícitamente que subregión, tipo de magnitud, selección de años y módulos opcionales quedan fuera hasta contar con requisitos y contrato aprobados? [Scope, Spec §Confirmed scope, Optional proposals]

## Notes

- Marca un ítem `[x]` solo después de que una revisión confirme la calidad del requisito correspondiente.
- Mantén sin marcar los ítems que necesiten aclaración, corrección o evaluación adicional.
- `/speckit-implement` lee el estado de las checklists como señal de revisión y no debe cambiar sus marcadores.
- `checklists/requirements.md` tiene un ciclo de mantenimiento independiente de esta checklist custom.
- Añade observaciones del revisor junto al ítem pertinente; conserva IDs globalmente secuenciales.
- Revisión completada contra `spec.md`, `contracts/panel-ui.md`, `docs/CONTRATO-API.md` y la implementación relacionada; los marcadores aprobados certifican calidad de requisitos, no completitud del código.
