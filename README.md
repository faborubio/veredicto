# Veredicto

> *Motor de decisión de crédito determinista, auditable y explicable — con una capa MCP para interrogarlo en lenguaje natural.*

<p>
  <a href="https://github.com/faborubio/veredicto/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/faborubio/veredicto/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.12+-3776AB?logo=python&logoColor=white">
  <img alt="Tests" src="https://img.shields.io/badge/tests-182%20passing-2ea44f">
  <img alt="mypy" src="https://img.shields.io/badge/mypy-strict-blue">
  <img alt="ruff" src="https://img.shields.io/badge/lint-ruff-261230?logo=ruff&logoColor=white">
  <img alt="arquitectura" src="https://img.shields.io/badge/arquitectura-Clean%20%2B%20DDD-6e5494">
  <a href="./LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-yellow"></a>
</p>

Motor de decisión de crédito de consumo (dominio chileno) construido sobre **Clean Architecture**: un núcleo de dominio puro y determinista, reglas como datos versionados, rastro de auditoría completo por decisión, simulación *what-if* sobre población histórica, y una **capa MCP** que permite a un analista preguntarle a Claude *"¿por qué se rechazó la solicitud X?"* o *"simula bajar el tope de DTI a 40%"*.

> **Proyecto de portafolio** orientado a demostrar Clean Architecture, Specification-Driven Development, testing riguroso (incl. property-based) y adopción de IA/MCP en un dominio fintech realista. No maneja dinero ni datos reales.

---

## Por qué existe

Prestar plata con responsabilidad exige tres cosas que un CRUD con `if/else` no da:

- **Explicar** *por qué* se tomó cada decisión, en términos que un humano (o un regulador) entienda.
- **Reproducir** una decisión meses después, idéntica, aunque las reglas hayan cambiado.
- **Simular** el impacto de un cambio de política *antes* de aplicarlo.

El valor de este proyecto está justamente ahí: en el rastro de auditoría, el versionado inmutable de reglas y la simulación de impacto — no en el flujo feliz.

## Capacidades

| Capacidad | Qué hace |
|-----------|----------|
| **Evaluación + rastro** | Evalúa una solicitud contra una política → decisión (`APROBADO` / `RECHAZADO` / `REVISION_MANUAL`) + rastro de cada regla evaluada. |
| **Reglas como datos** | Las reglas son árboles de predicados versionados, nunca código (`eval` prohibido). Configurables sin desplegar. |
| **Versionado inmutable** | Editar una política = crear una nueva versión completa. Cada decisión referencia la versión exacta que la produjo → reproducibilidad real. |
| **Simulación what-if** | Reevalúa la población histórica con una política candidata y reporta los *flips* de decisión, sin tocar producción. |
| **Capa MCP** | 5 herramientas read-only + simulación expuestas a Claude vía FastMCP. Sin escrituras de crédito por lenguaje natural. |

## Principios de diseño (invariantes)

Lo que hace al motor confiable son sus restricciones, sostenidas por tests y por un linter de fronteras:

- **El motor de evaluación es una función pura con scoring entero** — sin I/O, sin reloj, sin azar, sin `float`. El tiempo y los datos externos entran como parámetros. Un *property-test* (Hypothesis) verifica el determinismo.
- **El dominio no importa nada de afuera** — ni SQLAlchemy, ni FastAPI, ni FastMCP. Las dependencias apuntan hacia el núcleo, blindado con [import-linter](https://github.com/seddonym/import-linter) en CI.
- **Cada decisión persiste el snapshot completo de sus insumos** (incluida la disponibilidad de cada dato) → la simulación es fiel, no una aproximación.
- **La capa MCP no contiene lógica de negocio** — es un adaptador delgado sobre los casos de uso; read-only + simulación por defecto.

Detalle completo y ADRs en [`SAD.md`](./SAD.md); lista de invariantes en [`CLAUDE.md §2`](./CLAUDE.md).

## Arquitectura

Clean Architecture en cuatro capas, con la regla de dependencia apuntando al núcleo:

```
interfaces/      REST (FastAPI) + MCP (FastMCP)        ← adaptadores de entrega
application/     casos de uso (orquestan dominio + puertos)
domain/          núcleo PURO: entidades, motor, puertos  ← no conoce a nadie hacia afuera
infrastructure/  repos SQLAlchemy, buró simulado, DI    ← adaptadores de salida

dependencias:  interfaces → application → domain ← infrastructure
```

## Stack

Python 3.12+ · FastAPI · Pydantic v2 · SQLAlchemy 2.0 · PostgreSQL · `injector` · FastMCP · pytest + Hypothesis · Docker. Toolchain con **uv**.

## Ejemplo

Evaluar una solicitud:

```bash
curl -X POST http://localhost:8000/evaluaciones \
  -H "Content-Type: application/json" \
  -d '{
    "idempotency_key": "sol-001",
    "rut_numero": 16894365, "rut_dv": "2",
    "ingreso_mensual": 1200000,
    "situacion_laboral": "DEPENDIENTE",
    "producto": "consumo",
    "monto": 2000000, "plazo": 24
  }'
```

Respuesta — decisión + rastro auditable (recortado; el rastro trae una entrada por regla):

```json
{
  "resultado": "APROBADO",
  "score": 85,
  "politica_id": "consumo",
  "politica_version": 1,
  "rastro": [
    {
      "regla_id": "R1-monto-rango",
      "tipo": "HARD_STOP",
      "resultado": "PASA",
      "fuente_dato": "monto",
      "disponibilidad": "DISPONIBLE",
      "aporte_score": 0,
      "explicacion": "Monto solicitado 2000000 CLP debe estar entre 500.000 y 20.000.000."
    }
  ]
}
```

Vía MCP, el mismo motor responde en lenguaje natural a través de Claude:

> **Analista:** ¿por qué se aprobó la solicitud `sol-001`?
> **Claude** (usando `explicar_decision`): Aprobada con score 85. Pasó todos los hard-stops (monto y plazo en rango, sin morosidad ni deudas castigadas, ingreso y DTI bajo el tope) y sumó puntaje por DTI bajo e historial suficiente.

## Cómo correr (local · ~USD 0)

```bash
# 1. Sincronizar entorno — uv descarga Python 3.12 y resuelve dependencias
uv sync --extra dev

# 2. Quality gate (lo mismo que corre CI)
uv run ruff check . && uv run ruff format --check .
uv run mypy src tests
uv run lint-imports
uv run pytest               # 182 tests (omite integración con -m "not integration")

# 3. Base de datos + migraciones
docker compose up -d db
uv run alembic upgrade head

# 4. API REST — docs interactivas en http://localhost:8000/docs
uv run uvicorn interfaces.rest.app:app --reload

# 5. Servidor MCP (stdio) — lo arranca el host MCP (Claude Desktop / Inspector)
uv run python -m interfaces.mcp.server
```

> La persistencia se elige por entorno: en memoria por defecto, o Postgres con
> `VEREDICTO_PERSISTENCIA=sql`. El servidor MCP necesita `VEREDICTO_PERSISTENCIA=sql`
> (la misma BD que escribe REST) para consultar decisiones reales.

Endpoints REST: `POST /evaluaciones` · `GET /politicas/{producto}/vigente` · `GET /politicas/{producto}/{version}` · `POST /politicas` · `POST /politicas/activar` · `POST /simulaciones`.
Herramientas MCP: `consultar_decision` · `explicar_decision` · `rastro_auditoria` · `listar_reglas` · `simular_cambio_regla`.

Conexión con Claude Desktop y despliegue remoto opcional: [`DEPLOY.md`](./DEPLOY.md).

## Estado

**Portafolio completo — fases 1–4 cerradas y auditadas.** Las cinco capacidades del SAD funcionan punta a punta: evaluación + rastro, configurabilidad versionada (Postgres + Alembic), simulación what-if, y capa MCP read-only + simulación. **182 tests** verdes (incl. integración con Postgres real vía testcontainers) · CI verde · `mypy --strict` · fronteras blindadas (import-linter 3/3).

Cada fase pasó una **auditoría de cierre** con *Vista de halcón* (revisión adversarial) registrada en [`docs/AUDIT.md`](./docs/AUDIT.md). Fase 5 (cloud / MCP remoto / observabilidad) es opcional y queda fuera del alcance del portafolio. Hoja de ruta en [`SAD.md §13`](./SAD.md#13-hoja-de-ruta-por-fases).

## Documentación del proyecto

Este repo usa un sistema de **documentación viva** para continuidad de contexto entre sesiones:

| Documento | Para qué |
|-----------|----------|
| [`CLAUDE.md`](./CLAUDE.md) | Hub / steering. Se lee primero. Invariantes y fase actual. |
| [`SAD.md`](./SAD.md) | Arquitectura (fuente de verdad). 11 ADRs. |
| [`MEMORY.md`](./MEMORY.md) | Bitácora de decisiones y estado. |
| [`docs/AUDIT.md`](./docs/AUDIT.md) | Auditorías por fase + Vista de halcón. |
| [`docs/TROUBLESHOOTING.md`](./docs/TROUBLESHOOTING.md) | Errores y reglas de prevención. |
| [`docs/CASES.md`](./docs/CASES.md) | Casos borde por proceso, cada uno con su test. |
| [`DEPLOY.md`](./DEPLOY.md) | Runbook de despliegue. |

## Nota

Proyecto educativo / de portafolio. El buró de crédito es un adaptador **simulado**; no maneja dinero real ni datos productivos. Licencia [MIT](./LICENSE).
</content>
