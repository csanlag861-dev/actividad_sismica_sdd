# Plan Review Checklist: Dashboard de actividad y trazabilidad sísmica

**Purpose**: Revisar la completitud, claridad y coherencia de los requisitos y decisiones de diseño del plan anterior.
**Created**: 2026-11-17
**Feature**: [spec.md](../spec.md) · [plan.md](../plan.md)

**Note**: Esta checklist evalúa la calidad de lo especificado, no el estado de la implementación.
**Review Ownership**: Checklist de requisitos propiedad del revisor. Marcar `[x]` solo cuando el criterio de calidad del requisito haya sido revisado y satisfecho.
**Marker Semantics**: `[x]` indica que el requisito está suficientemente definido; no significa que la funcionalidad esté implementada.

## Requirement Completeness

- [ ] CHK001 ¿El alcance del dashboard define qué resumen horario y qué distribuciones deben aparecer, además del mapa y la ficha? [Completeness, Spec §FR-001–FR-004]
- [ ] CHK002 ¿Se especifica qué atributos de la ficha son datos sísmicos y cuáles son metadatos de trazabilidad? [Completeness, Spec §FR-007–FR-009]
- [ ] CHK003 ¿El contrato documenta el significado y la disponibilidad de cada campo nuevo de trazabilidad, incluido el caso de fuente o ejecución desconocida? [Completeness, Spec §FR-008–FR-009]
- [ ] CHK004 ¿Los requisitos delimitan con claridad que los gráficos presentan los agregados existentes y no introducen cálculos o indicadores nuevos? [Scope, Spec §FR-004–FR-006; Plan §Summary]

## Requirement Clarity

- [ ] CHK005 ¿La ubicación y jerarquía del mapa, la actividad horaria y los resúmenes dentro del dashboard están descritas con suficiente precisión para evitar interpretaciones de diseño incompatibles? [Clarity, Spec §FR-001–FR-004; Plan §Summary]
- [ ] CHK006 ¿Está definida una convención inequívoca para atribuir periodo y filtros a cada visualización cuando las respuestas de eventos y estadísticas no coinciden? [Clarity, Spec §FR-003, FR-006]
- [ ] CHK007 ¿La regla para convertir la fuente persistida en una etiqueta pública segura identifica los valores permitidos y el tratamiento de cualquier otro valor? [Clarity, Spec §FR-008; Plan §Constraints]
- [ ] CHK008 ¿El formato de fecha y la zona horaria de cada campo de trazabilidad son explícitos y coherentes con los campos existentes del contrato? [Clarity, Spec §FR-007–FR-009; Plan §Constitution Check]

## Requirement Consistency

- [ ] CHK009 ¿La ficha usa de forma consistente el identificador de feature y su fecha `updated` existentes, sin crear una segunda identidad o versión contradictoria? [Consistency, Spec §FR-007–FR-008; Plan §Structure Decision]
- [ ] CHK010 ¿La regla de compatibilidad para respuestas antiguas concuerda entre contrato, modelo de datos, interfaz y validación del cliente? [Consistency, Spec §FR-008, FR-010; Plan §Constraints]
- [ ] CHK011 ¿La exclusión del payload original, hashes y secretos es coherente en requisitos, contrato de respuesta y decisiones de exposición? [Consistency, Spec §FR-008; Plan §Constraints]

## Acceptance Criteria Quality

- [ ] CHK012 ¿Los criterios de éxito permiten juzgar objetivamente la fidelidad de conteos, bins, unidades, porcentajes y ausentes respecto de la respuesta estadística? [Measurability, Spec §SC-002–SC-003]
- [ ] CHK013 ¿Los criterios de éxito definen cómo reconocer que la ficha expone la trazabilidad disponible sin revelar datos excluidos? [Measurability, Spec §SC-004]

## Scenario and Edge Case Coverage

- [ ] CHK014 ¿Los requisitos distinguen explícitamente, para cada recurso del dashboard, carga, vacío válido, error parcial y última lectura desactualizada? [Coverage, Spec §FR-005, FR-010; Edge Cases]
- [ ] CHK015 ¿Se define la presentación cuando un evento no tiene trazabilidad o contiene solo algunos campos de procedencia? [Coverage, Spec §FR-007–FR-008; Edge Cases]

## Non-Functional Requirements and Assumptions

- [ ] CHK016 ¿Las exigencias de accesibilidad especifican alternativas para gráficos/mapa y los requisitos de teclado y texto alternativo para la marca? [Accessibility, Spec §FR-011–FR-012]
- [ ] CHK017 ¿Se define el comportamiento esperado si el recurso del logo no está disponible o no resulta legible en alguno de los temas o tamaños? [Edge Case, Gap, Spec §FR-012]
- [ ] CHK018 ¿La ausencia de objetivos propios de rendimiento, disponibilidad y volumen queda delimitada como una decisión consciente para este alcance? [Assumption, Plan §Technical Context]

## Notes

- Marcar los elementos solo después de revisar si el plan y la especificación expresan requisitos completos, claros, consistentes y medibles.
- Los elementos `[ ]` señalan oportunidades de aclaración documental, no fallos de código.
- `/speckit-implement` lee el estado de las checklists como referencia y no debe cambiar sus marcadores.
- Los identificadores son secuenciales para facilitar comentarios de revisión.
