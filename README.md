# Veredicto

> *Motor de decisión de crédito explicable y auditable, con capa MCP.*

Motor de decisión de crédito **determinista, auditable, explicable y configurable**, con una **capa MCP** que permite consultar y simular el motor en lenguaje natural a través de Claude. Dominio: crédito de consumo chileno.

> **Proyecto de portafolio** orientado a demostrar Clean Architecture, Specification-Driven Development, testing riguroso y adopción de IA/MCP en un dominio fintech realista.

---

## Por qué existe

Prestar plata con responsabilidad exige poder responder *por qué* se tomó cada decisión, reproducirla meses después y simular cambios de política antes de aplicarlos. Este proyecto modela esas tres capacidades —explicabilidad, auditabilidad y simulación what-if— sobre una arquitectura limpia y testeable.

No es un CRUD con `if/else`. El valor está en el rastro de auditoría, el versionado inmutable de reglas y la simulación de impacto.

## Capacidades

- Evaluar una solicitud contra una política de reglas → decisión + **rastro de auditoría** completo.
- **Reglas como datos versionados** (no código): configurables sin desplegar.
- **Simulación what-if:** medir el impacto de un cambio de regla sobre población histórica.
- **Capa MCP:** preguntar a Claude "¿por qué se rechazó la solicitud X?" o "simula bajar el DTI a 40%".

## Stack

Python 3.12+ · FastAPI · Pydantic v2 · SQLAlchemy 2.0 · PostgreSQL · `injector` · FastMCP · pytest + Hypothesis · Docker.

## Arquitectura

Clean Architecture en cuatro capas (`domain / application / infrastructure / interfaces`), con regla de dependencia hacia el núcleo. Detalle completo en [`SAD.md`](./SAD.md).

```
interfaces/      REST (FastAPI) + MCP (FastMCP)
application/     casos de uso
domain/          núcleo puro: entidades, motor, puertos
infrastructure/  repos SQLAlchemy, buró simulado
```

## Cómo correr (fase local)

> Gestión de entorno con **uv**. La estructura y el toolchain existen desde Fase 0;
> los endpoints REST y las migraciones llegan en Fase 1+.

```bash
# 1. Sincronizar entorno (uv descarga Python 3.12 y resuelve dependencias)
uv sync --extra dev

# 2. Quality gate (frontera del dominio incluida)
uv run ruff check .
uv run mypy src
uv run lint-imports
uv run pytest

# 3. Levantar Postgres (requiere Docker corriendo)
docker compose up -d db

# 4. API REST (health check disponible en /health)
uv run uvicorn interfaces.rest.app:app --reload

# 5. Migraciones (Alembic, desde Fase 2)
# uv run alembic upgrade head
```

Servidor MCP (stdio) y conexión con Claude Desktop: ver [`DEPLOY.md`](./DEPLOY.md).

## Documentación del proyecto

Este repo usa un sistema de **documentación viva** para continuidad de contexto entre sesiones:

| Documento | Para qué |
|-----------|----------|
| [`CLAUDE.md`](./CLAUDE.md) | Hub / steering. Se lee primero. Invariantes y fase actual. |
| [`SAD.md`](./SAD.md) | Arquitectura (fuente de verdad). |
| [`MEMORY.md`](./MEMORY.md) | Bitácora de decisiones y estado. |
| [`docs/AUDIT.md`](./docs/AUDIT.md) | Auditorías por fase. |
| [`docs/TROUBLESHOOTING.md`](./docs/TROUBLESHOOTING.md) | Errores y prevención. |
| [`docs/CASES.md`](./docs/CASES.md) | Casos borde por proceso. |
| [`DEPLOY.md`](./DEPLOY.md) | Despliegue. |

## Estado

**Fases 1–4 (el portafolio) implementadas.** Fases 0–3 cerradas y auditadas; Fase 4 (capa MCP) funcionalmente completa, pendiente de su auditoría de cierre. Las cinco capacidades del SAD funcionan: evaluación + rastro, configurabilidad versionada, simulación what-if y capa MCP read-only. **181 tests** verdes (incl. integración con Postgres) · CI verde. Hoja de ruta y detalle por fase en [`SAD.md §13`](./SAD.md#13-hoja-de-ruta-por-fases) y [`docs/AUDIT.md`](./docs/AUDIT.md). Fase 5 (cloud/observabilidad) es opcional, fuera del alcance del portafolio.

Endpoints REST: `POST /evaluaciones`, `GET /politicas/{producto}/vigente`, `POST /politicas`, `POST /politicas/activar`, `POST /simulaciones`. Servidor MCP: `python -m interfaces.mcp.server`.

## Nota

Proyecto educativo / de portafolio. El buró de crédito es un adaptador **simulado**; no maneja dinero real ni datos productivos.
