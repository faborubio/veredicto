# AUDIT.md — Auditorías por fase

> Compuerta de calidad: **no se avanza de fase sin una entrada de auditoría con sign-off aquí.**
> Hub: [`../CLAUDE.md`](../CLAUDE.md) · Arquitectura: [`../SAD.md`](../SAD.md)

---

## Checklist base (aplica a toda fase)

Marcar cada ítem antes de cerrar una fase:

- [ ] El entregable cumple lo definido para la fase en `SAD.md §13`.
- [ ] **Fronteras de arquitectura intactas:** `domain/` no importa SQLAlchemy/FastAPI/FastMCP. (Verificado con linter de imports.)
- [ ] **Invariantes respetados** (ver `CLAUDE.md §2`). En particular: determinismo del motor.
- [ ] Tests verdes; cobertura del dominio alta.
- [ ] Property-test de determinismo pasa (desde Fase 1 en adelante).
- [ ] Casos borde de la fase registrados en `CASES.md` y cubiertos por tests.
- [ ] Errores encontrados registrados en `TROUBLESHOOTING.md` con regla de prevención.
- [ ] `MEMORY.md` actualizado.
- [ ] `CLAUDE.md` refleja la nueva fase actual.
- [ ] Sin secretos ni PII en el repo/logs.

---

## Plantilla de entrada de auditoría

```
### [Fecha] · Auditoría de cierre — Fase N: <nombre>

**Resultado:** APROBADA / APROBADA CON OBSERVACIONES / RECHAZADA

**Checklist:** (pegar checklist base con marcas reales)

**Hallazgos:**
- ...

**Observaciones / deuda aceptada:**
- ...

**Acciones antes de avanzar:**
- ...

**Sign-off:** <responsable> — <fecha>
```

---

## Registro de auditorías

<!-- Anexar nuevas auditorías ABAJO, en orden cronológico. -->

### 2026-06-26 · Auditoría de cierre — Fase 0: Scaffolding

**Resultado:** APROBADA

**Checklist:**

- [x] El entregable cumple lo definido para la fase en `SAD.md §13` (estructura de capas, sistema de docs, esqueleto de dominio, Docker+Postgres). *Postgres: ver observación.*
- [x] **Fronteras de arquitectura intactas:** `domain/` no importa SQLAlchemy/FastAPI/FastMCP. Verificado con **import-linter** (`lint-imports`): 2 contratos `KEPT` (capas + pureza del dominio), 49 archivos / 89 dependencias analizadas.
- [x] **Invariantes respetados** (`CLAUDE.md §2`): dominio puro sólo-stdlib, sin `float` en VOs de scoring/monto, entidades inmutables. Determinismo del motor: aún sin motor (Fase 1).
- [x] Tests verdes; cobertura del dominio: 29 tests pasan (humo + invariantes de VOs + chequeo de frontera). Python 3.12.13.
- [N/A] Property-test de determinismo: aplica **desde Fase 1** (aún no hay motor).
- [x] Casos borde de la fase: Fase 0 no introduce procesos nuevos; los casos de `CASES.md` quedan referenciados como TODO(Fase N) en el código que los tocará.
- [x] Errores encontrados registrados en `TROUBLESHOOTING.md` (TS-001 import-linter, TS-002 Python 3.11→3.12) con regla de prevención.
- [x] `MEMORY.md` actualizado (entrada 2026-06-26).
- [x] `CLAUDE.md` actualizado a **Fase 1** tras el sign-off de esta auditoría.
- [x] Sin secretos ni PII en el repo/logs (`.env` gitignored, `.env.example` con placeholders).

**Calidad (gate):** `ruff check` ✓ · `ruff format` ✓ · `mypy --strict` ✓ (42 archivos) · `lint-imports` ✓ (2/2) · `pytest` ✓ (29).

**Hallazgos:**
- Discrepancia de rutas de docs resuelta: `AUDIT/TROUBLESHOOTING/CASES` movidos a `docs/` para coincidir con `SAD §12`.
- `README` actualizado de `pip` a `uv` (decisión de tooling).

**Observaciones / deuda aceptada:**
- **Docker Postgres:** RESUELTO en esta sesión — `docker compose up -d db` levantó `veredicto-db` (postgres:16-alpine) y el healthcheck reporta `healthy`.
- Servicios/casos de uso/adaptadores son esqueletos con `NotImplementedError` y TODO(Fase N): es lo esperado en scaffolding.

**Acciones antes de avanzar a Fase 1:** completadas (Postgres healthy + sign-off).

**Sign-off:** Fabián (corporativo@caucorp.com) — 2026-06-26
