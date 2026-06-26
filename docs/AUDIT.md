# AUDIT.md — Auditorías por fase

> Compuerta de calidad: **no se avanza de fase sin una entrada de auditoría con sign-off aquí.**
> Hub: [`../CLAUDE.md`](../CLAUDE.md) · Arquitectura: [`../SAD.md`](../SAD.md)

---

## Checklist base (aplica a toda fase)

Marcar cada ítem antes de cerrar una fase:

- [ ] **Vista de halcón corrida y registrada** (revisión crítica adversarial; ver más abajo y `CLAUDE.md §7`). Cada hallazgo con decisión explícita.
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

## Vista de halcón — qué es y cómo se corre

> Gate **obligatorio antes de cada transición de fase**, distinto del checklist. El
> checklist es mecánico ("¿se hizo X?"); la vista de halcón es **adversarial**:
> busca activamente lo que está mal o frágil. Es el control independiente que evita
> que "auditor = implementador" se autovalide.

**Qué se caza activamente:**
1. **Fugas de frontera** — ¿alguna capa importa hacia afuera? ¿está *blindado* por linter, no sólo "no pasa hoy"?
2. **Violaciones de invariantes** (`CLAUDE.md §2`) — `float` en scoring, I/O o reloj en el dominio, mutación de inmutables, `eval`.
3. **No-determinismo escondido** — `set`/`dict` con orden relevante, `datetime.now()`, azar.
4. **Contradicciones con el SAD** — el código contradice una ADR o el SAD quedó desactualizado respecto a una decisión real.
5. **Sobre-ingeniería** — abstracción o scaffolding por delante de la necesidad de la fase.
6. **Tipos/placeholders débiles** — `object`/`Any` que anulan el tipado estricto; rastrear a qué fase se resuelven.
7. **Huecos de test** — caminos sin cubrir, casos de `CASES.md` sin test.

**Salida:** lista de hallazgos categorizados **🔴 Bloqueante / 🟡 Recomendado / 🟢 Menor**, y para cada uno una **decisión explícita**: *corregir ahora* / *diferir a Fase N* / *aceptar como deuda*. Los bloqueantes se cierran antes del sign-off.

---

## Plantilla de entrada de auditoría

```
### [Fecha] · Auditoría de cierre — Fase N: <nombre>

**Resultado:** APROBADA / APROBADA CON OBSERVACIONES / RECHAZADA

**Checklist:** (pegar checklist base con marcas reales)

**Vista de halcón (revisión crítica):**
- 🔴 Bloqueante: <hallazgo> → decisión: corregir ahora / ...
- 🟡 Recomendado: <hallazgo> → decisión: ...
- 🟢 Menor / deuda: <hallazgo> → decisión: ...

**Observaciones / deuda aceptada:**
- ...

**Acciones antes de avanzar:**
- ...

**Sign-off:** <responsable> — <fecha>
```

---

## Registro de auditorías

<!-- Anexar nuevas auditorías ABAJO, en orden cronológico. -->

### 2026-06-26 · Auditoría de cierre — Fase 1: Motor + rastro

**Resultado:** APROBADA

**Checklist:**

- [x] **Vista de halcón corrida y registrada** (abajo); bloqueantes cerrados.
- [x] Entregable Fase 1 (`SAD §13`): evaluación determinista hard-stops + scoring, rastro, REST mínima, tests + property-test de determinismo. Demostrable: `POST /evaluaciones` → decisión + rastro.
- [x] **Fronteras intactas:** import-linter 3/3 KEPT; `application ↛ infrastructure` blindada; composition root en infra (`di.py`).
- [x] **Invariantes:** motor puro (sin I/O/reloj/azar/float), scoring entero, entidades inmutables, idempotencia (ADR-010), versión de política fijada por request (ADR-008).
- [x] **Property-test de determinismo** verde (el invariante estrella) + golden-file del rastro (SAD §8.2).
- [x] Casos borde: EV-01/02/03/05/06/07 🟢; CF-01/02/03 🟡 (validación al versionar → Fase 2). `CASES.md` actualizado.
- [x] Errores registrados en `TROUBLESHOOTING.md` (TS-003: gate local debe espejar CI).
- [x] `MEMORY.md` actualizado · `CLAUDE.md` → Fase 2 · sin secretos/PII (RUT enmascarable, §8.1).
- [x] **CI verde** en GitHub Actions (ruff + format + mypy src/tests + lint-imports + pytest).

**Calidad (gate):** ruff ✓ · ruff format ✓ · mypy --strict ✓ (57, src+tests) · lint-imports ✓ (3/3) · pytest ✓ (131).

**Vista de halcón (revisión crítica):**
- 🔴 **EV-01 — RUT sin validar** (datos basura al motor). → **corregido ahora:** dígito verificador módulo 11 en `Rut` + `desde_texto` + enmascarado PII; fixtures con RUTs válidos.
- 🟡 **Sin golden-file del rastro** (SAD §8.2 lo pide). → **corregido ahora:** `test_golden_rastro_perfil_limpio`.
- 🟡 **EV-05/EV-06 sin test dedicado.** → **corregido ahora.**
- 🟡 **El gate no tipaba los tests** (CI sólo `mypy src`). → **corregido ahora:** `mypy src tests` local y en CI.
- 🟡 **DTI semánticamente débil:** `deuda_total/ingreso_mensual` no es carga financiera (cuota/ingreso); los umbrales no son significativos contra esa métrica. → **diferido:** refinar con input `cuota_mensual` en una versión futura de política (ADR-003). Documentado en `insumos.py`.
- 🟡 **CF-03 no se enforce al construir `Politica`** (sólo testeado en la semilla). → **diferido a Fase 2** (GestionarReglas + validación al versionar).
- 🟢 `ante_dato_faltante` inalcanzable en R1/R2/R5 (campos siempre disponibles): cosmético. Mapeo de errores REST grueso (`PoliticaInexistente`→409): refinar en Fase 2. Warning de Starlette (httpx): cosmético.

**Nota de independencia (M3):** decisión del proyecto (2026-06-26) — **NO se usará revisión independiente externa** (subagente fresco ni `/code-review ultra`). La Vista de halcón (autocrítica adversarial) es el único control de cierre. M3 aceptado como deuda consciente; no volver a ofrecer revisión independiente en cierres futuros.

**Acciones antes de avanzar:** completadas (bloqueantes cerrados + sign-off).

**Sign-off:** Fabián (corporativo@caucorp.com) — 2026-06-26

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

**Calidad (gate):** `ruff check` ✓ · `ruff format` ✓ · `mypy --strict` ✓ (47 archivos) · `lint-imports` ✓ (3/3) · `pytest` ✓ (71).

**Vista de halcón (revisión crítica — añadida 2026-06-26):**
- 🔴 **B1 — frontera `application ↛ infrastructure` no blindada.** El linter sólo protegía a `domain`; nada impedía que un caso de uso importara un repo concreto (no se violaba, pero no estaba blindado). → **Decisión: corregir ahora.** Agregado contrato `forbidden` con `source_modules=["application"]` (3/3 contratos KEPT).
- 🟡 **R2 — sin CI.** El quality gate no corre en cada push. → **Decisión: diferir** (pendiente `.github/workflows/ci.yml` con uv; no bloquea Fase 1).
- 🟡 **R3 — placeholders `object`** (`predicado`, `simular`→, `criterio`, `binder`) anulan mypy-strict puntualmente. → **Decisión: deuda trackeada.** `predicado`/`binder` → Fase 1; `simular`/`criterio` → Fase 3.
- 🟡 **R4 — smoke tests sólo recorrían `domain`.** → **Decisión: corregir ahora.** Añadido `tests/test_imports.py` que importa todos los módulos de las 4 capas (71 tests totales).
- 🟢 **M1 — tiempo/vigencia como `str` ISO crudo, sin validar.** → diferir (posible VO `Momento` en fase futura, manteniendo determinismo).
- 🟢 **M2 — esqueletos vacíos un pelo por delante del alcance de Fase 0.** → aceptado (fijan la frontera).
- 🟢 **M3 — auditor = implementador.** → mitigado: la Vista de halcón queda como gate independiente y obligatorio (`CLAUDE.md §7`).
- ⚖️ **Decisión de diseño — dominio stdlib-only.** Se endureció el SAD §5.1: el dominio NO usa Pydantic (ni puro). `pydantic` añadido a los módulos prohibidos del dominio en import-linter.

**Hallazgos (sesión):**
- Discrepancia de rutas de docs resuelta: `AUDIT/TROUBLESHOOTING/CASES` movidos a `docs/` para coincidir con `SAD §12`.
- `README` actualizado de `pip` a `uv` (decisión de tooling).

**Observaciones / deuda aceptada:**
- **Docker Postgres:** RESUELTO en esta sesión — `docker compose up -d db` levantó `veredicto-db` (postgres:16-alpine) y el healthcheck reporta `healthy`.
- Servicios/casos de uso/adaptadores son esqueletos con `NotImplementedError` y TODO(Fase N): es lo esperado en scaffolding.

**Acciones antes de avanzar a Fase 1:** completadas (Postgres healthy + sign-off).

**Sign-off:** Fabián (corporativo@caucorp.com) — 2026-06-26
