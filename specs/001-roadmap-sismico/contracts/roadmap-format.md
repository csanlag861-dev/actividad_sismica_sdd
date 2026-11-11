# Contract: Formato del ROADMAP

## Propósito y límites

Este contrato define cómo se organiza el documento `ROADMAP.md` solicitado.
No modifica el contrato funcional del sistema, que sigue definido en
[`docs/CONTRATO-API.md`](../../../docs/CONTRATO-API.md).

## Estructura requerida

1. **Introducción y reglas de lectura**: objetivo, leyenda de obligatorio,
   decisión documentable y opcional, y autoridad de los documentos fuente.
2. **Resumen de hitos**: secuencia de principio a fin.
3. **Fases ordenadas**: cada fase contiene objetivo, prerrequisitos, tareas,
   condición de salida y enlaces de referencia.
4. **Tareas y subtareas**: acciones concretas, dependencias, resultado y
   evidencia verificable.
5. **Matriz de cobertura**: mapea pruebas de aceptación, criterios de rúbrica
   y entregables a las fases/tareas correspondientes.
6. **Cierre y entrega**: lista de comprobación final, documentación y
   preparación de la defensa.
7. **Referencias**: enlaces a documentos fuente del repositorio.

## Campos mínimos de una tarea

| Field | Required meaning |
|---|---|
| ID y título | Identificador único y acción breve |
| Tipo | Obligatorio, decisión que debe documentarse o ampliación opcional |
| Depende de | Identificadores previos, o `Ninguna` |
| Pasos/subtareas | Trabajo accionable y suficientemente granular |
| Resultado | Artefacto o capacidad que quedará creada |
| Criterio de finalización | Comprobación observable |
| Evidencia | Consulta, prueba, captura, documento o demostración a conservar |
| Referencia | Sección del enunciado, contrato o FAQ que justifica la tarea |

## Reglas de precedencia

- El roadmap MUST conservar la prioridad normativa: constitución, enunciado,
  contrato para la API y FAQ como aclaración.
- El roadmap MUST marcar como obligatorios únicamente los requisitos
  obligatorios de las fuentes.
- Una tarea MUST aparecer después de sus prerrequisitos reales. La mera
  conveniencia de presentación no se declara dependencia técnica.
- Las tareas independientes pueden indicarse como paralelizables.
- Ninguna tarea puede considerarse terminada solo por haber sido intentada;
  debe satisfacer su criterio y dejar la evidencia indicada.
- Las secciones y tareas deben enlazar a las fuentes existentes mediante
  rutas relativas que resuelvan desde `ROADMAP.md`.

## Áreas mínimas de cobertura

- Lectura del encargo, exploración del material y preparación de entorno.
- Fuentes reciente e histórica, catálogo geográfico, originales y procedencia.
- Infraestructura obligatoria y persistencia; recorrido mínimo de extremo a
  extremo.
- Validación, calidad, cuarentena, revisiones, duplicados e idempotencia.
- Operaciones, filtros, errores, límites y metadatos de consulta definidos por
  el contrato.
- Mapa, tabla, gráficos, comparación y conclusiones.
- Pruebas de aceptación, fallos, recuperación, replay, complejidad y costes.
- Publicación, seguridad de configuración y verificación desde otro
  dispositivo.
- Modelo, diccionario, memoria/notebook, evidencias, entrega y defensa.

## Comprobación del contrato

El documento cumple este contrato si:

1. Todas las áreas mínimas aparecen en tareas identificables.
2. Cada prueba de aceptación del enunciado tiene una tarea y resultado
   asociado.
3. Todos los criterios de la rúbrica y entregables aparecen en la matriz de
   cobertura.
4. Las tareas tienen prerrequisitos y evidencia; el grafo no contiene ciclos.
5. Las opciones se identifican como tales, y los ejemplos no crean requisitos.
6. Los enlaces a las fuentes y entre secciones se resuelven.
