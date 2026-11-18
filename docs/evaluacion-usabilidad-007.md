# Protocolo de evaluación de usabilidad (spec 007)

**Estado:** preparado; pendiente de ejecutar con diez participantes reales.
Este documento define la prueba SC-003 y SC-006 de
[`spec.md`](../specs/007-exploracion-sismica-avanzada/spec.md). No contiene ni
simula resultados humanos.

## Preparación

1. La persona responsable debe disponer de diez participantes voluntarios y
   de un entorno accesible desde el dispositivo en el que harán la tarea.
2. Usa la fixture determinista y claramente identificada exigida por
   [`quickstart.md`](../specs/007-exploracion-sismica-avanzada/quickstart.md).
   Si contiene eventos sintéticos, la interfaz debe decir de forma visible
   **DATOS SINTÉTICOS DE PRUEBA — NO SON TERREMOTOS REALES**. No reutilices
   datos de producción como si fueran una fixture ni publiques una fixture en
   una API pública sin aislarla.
3. Antes de invitar participantes, comprueba los datos esperados y apunta en
   la hoja del evaluador (no visible a los participantes):
   - identificador del evento más reciente por `event_time`;
   - un evento objetivo que requiera cambiar de página en la tabla;
   - dos grupos de comparación con periodo y población conocidos;
   - los nombres exactos que la pantalla muestra para esos periodos y
     poblaciones.
4. Verifica que la ruta de evaluación funciona de principio a fin, que la
   fixture contiene suficientes registros para paginar, y que comparación y
   mapa están disponibles. Si falla una condición, corrígela antes de
   empezar; no cuentes errores del entorno como fallos del participante.
5. Obtén participación voluntaria e informa brevemente del objetivo. No
   solicites ni registres nombres, correo, edad, centro, audio, vídeo, imagen
   de pantalla u otros datos personales. No es necesario grabar. Conserva
   únicamente los resultados agregados de las diez tareas.

## Guion idéntico para cada participante

La persona facilitadora puede leer:

> Estamos comprobando si la interfaz permite completar estas tareas sin
> ayuda. Los datos se identifican como fixture de prueba y no representan
> necesariamente terremotos reales. Participar es voluntario. No registraremos
> información personal ni grabaciones. Puedes dejar la prueba en cualquier
> momento. Durante las tareas no te daré indicaciones.

No expliques dónde están los controles ni cómo interpretar la página. Lee las
tareas literalmente:

### SC-003: localizar el evento más reciente

Abre la vista con el mapa y espera a que termine de mostrarse. En ese instante,
inicia el cronómetro y di:

> ¿Qué evento está señalado como el más reciente? Indica el identificador o el
> lugar que aparece en su ficha.

Detén el cronómetro cuando responda. Es éxito solo si identifica el evento
correcto **en menos de 10 segundos** y sin ayuda. Si pide ayuda, responde
«Haz lo que te parezca más natural» sin orientar y cuenta el intento como no
superado si no completa la tarea correctamente dentro del umbral.

### SC-006: paginación y contexto de comparación

Di:

> Encuentra el evento `[IDENTIFICADOR OBJETIVO]` usando la paginación de la
> tabla. Después, mirando la comparación que está preparada, dime qué periodos
> y qué poblaciones se están comparando.

Es éxito solo si completa las dos partes correctamente y sin ayuda:

1. llega al evento indicado mediante los controles de paginación;
2. explica correctamente el periodo y la población de los grupos de
   comparación mostrados.

El criterio no fija un límite de tiempo para SC-006; no añadas uno al decidir
si la persona tuvo éxito. Si la persona no lo completa o necesita ayuda, es
un intento no superado.

## Registro agregado

No rellenes ni conserves resultados vinculados a cada persona. Al terminar,
registra solo:

| Métrica agregada | Resultado |
|---|---:|
| Participantes que iniciaron | __ / 10 |
| SC-003 correcto en menos de 10 segundos y sin ayuda | __ / 10 |
| SC-006 completado correctamente y sin ayuda | __ / 10 |
| Incidencias del entorno que invalidaron una sesión | __ (describir sin datos personales) |

SC-003 cumple con al menos **9/10** éxitos. SC-006 cumple con al menos **9/10**
éxitos. Si una sesión se invalida por un fallo técnico, corrige el entorno y
haz un intento de reemplazo para completar diez pruebas válidas; documenta el
número de sesiones invalidadas sin identificar a nadie. Publica el método y
los resultados agregados en la memoria y en `docs/VALIDACION.md`, junto con
fecha, dispositivo/navegador y configuración del entorno.

Mide cada intento SC-003 con cronómetro para aplicar el umbral, pero no guardes
una lista de tiempos individuales; conserva únicamente el total que pasó.

## Pendiente

El proyecto no dispone de participantes ni puede ejecutar por sí solo esta
evaluación humana. La prueba permanece pendiente hasta que una persona
responsable reúna a diez voluntarios y ejecute este protocolo. No sustituyas
la evaluación por pruebas automatizadas, capturas, participantes simulados o
resultados estimados.
