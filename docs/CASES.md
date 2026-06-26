# CASES.md — Catálogo de casos borde

> Casos límite y críticos por proceso. Cada caso debe terminar como **test**. Estado: 🔴 sin cubrir · 🟡 identificado, en diseño · 🟢 cubierto por test.
> Hub: [`../CLAUDE.md`](../CLAUDE.md)
>
> Formato: **Caso → Por qué es peligroso → Comportamiento esperado → Estado.**

---

## Proceso: Evaluación de solicitud

| # | Caso | Por qué es peligroso | Comportamiento esperado | Estado |
|---|------|----------------------|--------------------------|--------|
| EV-01 | RUT inválido (dígito verificador incorrecto) | Datos basura entran al motor | Rechazo de validación antes de evaluar; error tipado | 🔴 |
| EV-02 | Solicitante sin historial (*thin file*) | Reglas que asumen historial pueden fallar o aprobar de más | Derivar a `REVISION_MANUAL`, no rechazar ni aprobar automático | 🔴 |
| EV-03 | Ingreso reportado = 0 o nulo | División por cero al calcular DTI | DTI indefinido → hard-stop con razón clara, sin excepción no controlada | 🔴 |
| EV-04 | Buró no responde / timeout | El motor no puede ser puro si depende de I/O | El caso de uso maneja el fallo; el motor sólo recibe datos ya resueltos o marca de "dato no disponible" | 🔴 |
| EV-05 | Monto solicitado fuera de rango de producto | Decisión sin sentido de negocio | Hard-stop de elegibilidad con razón | 🔴 |
| EV-06 | Múltiples hard-stops fallan a la vez | ¿Cuál razón se reporta? | Registrar todas las hard-stops evaluadas hasta el corte; decisión = RECHAZADO | 🔴 |
| EV-07 | Empate exacto en el umbral de banda de score | Ambigüedad aprobado/revisión | Definir comparación determinista (ej. `>=` documentado) y testearla | 🔴 |

## Proceso: Configuración de reglas / políticas

| # | Caso | Por qué es peligroso | Comportamiento esperado | Estado |
|---|------|----------------------|--------------------------|--------|
| CF-01 | Regla con predicado mal formado | Rompe evaluación en runtime | Validación al crear la versión; nunca persistir política inválida | 🔴 |
| CF-02 | Suma de pesos de scoring ≠ esperado | Score sin sentido | Validar coherencia de pesos al versionar | 🔴 |
| CF-03 | Regla referencia un `fuente_dato` inexistente | Falla silenciosa o KeyError | Validar que todo campo referenciado exista en el contrato de insumos | 🔴 |
| CF-04 | Intento de mutar una política ya usada en decisiones | Rompe inmutabilidad y auditoría | Prohibido; sólo se crea nueva versión | 🔴 |
| CF-05 | Dos políticas marcadas "vigentes" en el mismo período | Ambigüedad de qué versión aplica | Invariante: una sola vigente por producto/período | 🔴 |

## Proceso: Simulación (what-if)

| # | Caso | Por qué es peligroso | Comportamiento esperado | Estado |
|---|------|----------------------|--------------------------|--------|
| SI-01 | Población histórica con snapshots incompletos | Simulación no fiel | Excluir y reportar los casos sin snapshot completo, no inventar datos | 🔴 |
| SI-02 | Política candidata introduce un nuevo `fuente_dato` ausente en snapshots viejos | El dato no existía cuando se decidió | Marcar esas reglas como "no evaluables sobre histórico" y reportarlo | 🔴 |
| SI-03 | Población muy grande (rendimiento) | Simulación lenta, mala UX | Medir Big-O; paginar/streamear; no cargar todo en memoria de golpe | 🔴 |
| SI-04 | Simulación con efectos colaterales | Contamina datos productivos | La simulación NO persiste decisiones; es puramente lectura + cómputo | 🔴 |

## Proceso: Capa MCP

| # | Caso | Por qué es peligroso | Comportamiento esperado | Estado |
|---|------|----------------------|--------------------------|--------|
| MC-01 | Solicitud de explicar una decisión inexistente | Error feo hacia el modelo/usuario | Respuesta clara "no encontrada", no stack trace | 🔴 |
| MC-02 | Herramienta MCP devuelve PII completa innecesaria | Fuga de datos sensibles | Minimización: devolver sólo lo necesario para explicar | 🔴 |
| MC-03 | El modelo intenta una operación de escritura vía MCP | Crédito real modificado por lenguaje natural | No exponer escrituras en MVP; herramientas read-only + simulación | 🔴 |
| MC-04 | Parámetro de herramienta con tipo/formato inválido | Llamada que rompe el caso de uso | Validar parámetros y devolver error explicativo al modelo | 🔴 |

---

<!-- Anexar casos nuevos en la sección de proceso que corresponda. Actualizar estado a 🟢 cuando haya test. -->
