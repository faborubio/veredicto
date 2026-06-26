# CLAUDE.md — Hub de contexto del proyecto

> **Este archivo se lee PRIMERO en cada sesión nueva.** Es el steering file del proyecto.
> Después de leerlo, lee el final de [`MEMORY.md`](./MEMORY.md) para saber dónde quedamos.

---

## 1. Qué es este proyecto

**Veredicto** — motor de decisión de crédito **determinista, auditable, explicable y configurable**, más una **capa MCP** que permite a Riesgo/Operaciones interrogar y simular el motor en lenguaje natural vía Claude. Dominio: crédito de consumo chileno.

Fuente de verdad de la arquitectura: [`SAD.md`](./SAD.md). **No tomes decisiones de arquitectura sin consultarlo.**

---

## 2. Invariantes inquebrantables

Estas reglas NO se rompen. Si una tarea parece exigir romperlas, detente y plantéalo.

1. **El motor de evaluación es una función pura con scoring entero.** Sin I/O, sin `datetime.now()`, sin azar, sin estado mutable, **sin `float` en el scoring** (pesos/score/umbrales son `int`). El tiempo y los datos externos entran como parámetros explícitos. (ADR-006)
2. **`domain/` no importa nada de fuera.** Ni SQLAlchemy, ni FastAPI, ni FastMCP, ni Pydantic-para-HTTP. Las dependencias apuntan hacia adentro. (ADR-001)
3. **Las reglas son datos, nunca código.** Predicado como árbol estructurado, jamás `eval()`. (ADR-002)
4. **La política es la unidad atómica versionada e inmutable.** Editar = nueva versión de política completa. Cada decisión referencia sólo la versión de política. Las reglas NO se versionan por separado (su `id` es procedencia). (ADR-003)
5. **El motor es un intérprete estable; la semántica vive en la política.** Pesos, método de agregación y umbrales de banda son dato en la política, no código. Fijar la versión de política basta para reproducir. (ADR-008)
6. **Cada decisión persiste el snapshot completo de insumos** (incluida la disponibilidad de cada dato). Sin esto la simulación es falsa. (ADR-004)
7. **El motor nunca asume que un dato está presente.** Disponibilidad explícita (`DISPONIBLE/NO_DISPONIBLE/PARCIAL`); cada regla declara su `ante_dato_faltante`. (ADR-009)
8. **Toda solicitud es idempotente.** Misma `idempotency_key` → misma decisión, sin duplicar. (ADR-010)
9. **La versión de política se fija al inicio del request** (evita TOCTOU). La activación de política es un evento auditado. (ADR-008)
10. **`REVISION_MANUAL` se modela hasta el override humano.** `DecisionFinal` vincula la decisión del motor con la decisión humana, para no romper el rastro. (ADR-011)
11. **La capa MCP no contiene lógica de negocio.** Es un adaptador delgado sobre casos de uso. Por defecto read-only + simulación; nada de escrituras de crédito real vía MCP. (ADR-005)
12. **Nunca tragar excepciones en silencio.** Errores de dominio tipados, traducidos en las capas de entrega.

---

## 3. Fronteras de arquitectura (capas)

```
interfaces/      → REST (FastAPI) y MCP (FastMCP). Adaptadores de entrega.
application/     → casos de uso. Orquestan dominio + puertos.
domain/          → núcleo puro: entidades, value objects, motor, puertos.
infrastructure/  → adaptadores: repos SQLAlchemy, gateway buró simulado.
```

Regla de dependencia: `interfaces → application → domain ← infrastructure`. El dominio no conoce a nadie hacia afuera.

---

## 4. Stack

Python 3.12+ · Pydantic v2 · FastAPI · SQLAlchemy 2.0 · PostgreSQL · `injector` · FastMCP · pytest + Hypothesis · Docker.

---

## 5. Fase actual

**FASE 2 — Configurabilidad.** (Actualizar este campo al cambiar de fase.)
> Fase 1 cerrada y auditada el 2026-06-26 (`docs/AUDIT.md`, APROBADA): motor determinista + rastro + REST mínima + CI. 131 tests verdes.
> Fase 0 cerrada y auditada el 2026-06-26: scaffolding + toolchain (uv) + Postgres.

Hoja de ruta completa en [`SAD.md` §13](./SAD.md#13-hoja-de-ruta-por-fases).
No se avanza de fase sin auditoría registrada en [`docs/AUDIT.md`](./docs/AUDIT.md).

---

## 6. Manifiesto de documentos — "lee esto cuando…"

| Documento | Léelo cuando… |
|-----------|---------------|
| [`SAD.md`](./SAD.md) | …necesites entender o cambiar la arquitectura. Fuente de verdad. |
| [`MEMORY.md`](./MEMORY.md) | …inicies sesión: te dice dónde quedamos. Y al cerrar: anexa el avance. |
| [`docs/AUDIT.md`](./docs/AUDIT.md) | …completes una fase. Corre la auditoría antes de avanzar. |
| [`docs/TROUBLESHOOTING.md`](./docs/TROUBLESHOOTING.md) | …te topes con un error (revisa si ya pasó) o resuelvas uno nuevo (regístralo). |
| [`docs/CASES.md`](./docs/CASES.md) | …diseñes o pruebes un proceso: revisa los casos borde y agrega los nuevos. |
| [`README.md`](./README.md) | …necesites instalar/correr el proyecto. |
| [`DEPLOY.md`](./DEPLOY.md) | …vayas a desplegar (fase remota). |

---

## 7. Protocolo de sesión

**Al iniciar:**
1. Leer este archivo (invariantes + fase actual).
2. Leer el final de `MEMORY.md`.
3. Leer `docs/CASES.md` y `docs/TROUBLESHOOTING.md` de la fase actual.

**Al cerrar:**
1. Anexar avance a `MEMORY.md`.
2. Registrar errores nuevos en `docs/TROUBLESHOOTING.md`.
3. Anexar casos borde nuevos a `docs/CASES.md`.
4. Si se cerró una fase: **correr la Vista de halcón** (revisión crítica adversarial, ver `docs/AUDIT.md`), cerrar los hallazgos 🔴 bloqueantes, y recién entonces auditar y registrar el sign-off en `docs/AUDIT.md`. No se avanza de fase sin esto.

**Antes de empezar una fase nueva:** confirmar que la Vista de halcón de la fase anterior está registrada con sus hallazgos resueltos o explícitamente diferidos.

---

## 8. Estilo de trabajo esperado

Feedback directo y crítico, sin adulación. Si algo es sobre-ingeniería, dilo. Si una decisión contradice el SAD o un invariante, señálalo antes de implementar. Profundo y angosto sobre ancho y superficial.
