# Contrato de interfaz: dashboard de actividad sísmica

## Dashboard

- El mapa presenta eventos recientes con geometrías válidas y una sola representación por `Feature.id`; permite seleccionar un evento para abrir la misma ficha usada en exploración.
- Una tabla accesible alternativa al mapa presenta lugar, fecha/hora UTC, magnitud, profundidad y país; seleccionar una fila abre la ficha correspondiente. Los eventos sin coordenadas válidas no se dibujan, pero sus atributos siguen disponibles en la tabla y ficha.
- Si `metadata.truncated` es `true`, se comunica que mapa y tabla contienen solo los eventos recibidos, no el total completo.
- La serie temporal usa exclusivamente `hourly_counts.buckets`, muestra hora UTC, conteo y contexto efectivo de `period`/`filters`.
- Los resúmenes de magnitud y profundidad presentan bins, recuentos, porcentajes recibidos, unidades, válidos y ausentes. No recalculan distribuciones ni porcentajes en frontend.
- Los gráficos incluyen alternativas textuales o tabulares accesibles con los valores esenciales; la información no depende exclusivamente del color.
- Un resultado vacío se presenta como vacío; error, truncamiento y posible desactualización permanecen distinguibles y atribuidos a su instantánea.
- Eventos y estadísticas son recursos independientes; cada uno conserva su propio periodo y filtros declarados.
- El periodo y los filtros se atribuyen a la respuesta correspondiente: la ventana predeterminada de 24 horas de eventos no se presenta como el periodo estadístico.
- Las distribuciones sin bins válidos muestran la ausencia de valores; un porcentaje nulo se identifica como no disponible, nunca como cero.

## Ficha de evento

La ficha seleccionada por `Feature.id` conserva los atributos existentes e incorpora una sección de trazabilidad:

- Identificador: `Feature.id`.
- Modo y fuente: `properties.traceability.mode` y `.source`.
- Versión: `properties.updated`.
- Fecha de ingesta: `properties.traceability.ingested_at`.
- Ejecución: `properties.traceability.ingestion_run_id`.

Las fechas se muestran en UTC. Las propiedades nulas y el objeto de trazabilidad ausente en una respuesta anterior se presentan como «No disponible», sin inferir datos.

## Marca

Usar el recurso `frontend/public/icon.png` como favicon y marca del encabezado/sidebar global donde ayude a reconocer la aplicación. Mantener proporción y legibilidad en los temas disponibles; la imagen de marca incluye texto alternativo accesible. Evitar repeticiones decorativas por vista. La interfaz mantiene sus temas y adaptabilidad existentes.
