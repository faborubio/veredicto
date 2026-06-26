# MEMORY.md — Bitácora del proyecto

> Registro cronológico de decisiones significativas y estado. Es la memoria **del proyecto**, versionada en el repo y portable entre sesiones/agentes. Si hay conflicto con la memoria interna de un agente, **gana este archivo**.
> Hub: [`CLAUDE.md`](./CLAUDE.md)
>
> Formato de entrada: fecha · fase · qué se hizo · dónde quedó · próximos pasos.

---

## 2026-06-26 · Fase 1 CERRADA — cableado de entrega + Vista de halcón + auditoría

**Qué se hizo:** completado y cerrado el entregable de Fase 1.

- **Cableado de entrega:** `EvaluarSolicitud` (idempotencia, fija política, snapshot), **buró simulado** (5 escenarios), repos en memoria, **DI con `injector`** (cierra placeholder R3 `binder`), **REST `POST /evaluaciones`** → decisión + rastro. **CI** en GitHub Actions (gate completo en cada push).
- **Vista de halcón de Fase 1** (registrada en `docs/AUDIT.md`). Bloqueantes corregidos en el acto: **EV-01** (RUT módulo 11 + `desde_texto` + enmascarado PII), **golden-file del rastro** (SAD §8.2), **EV-05/EV-06** tests, y **el gate ahora tipa los tests** (`mypy src tests`, local y CI). Diferidos documentados: DTI semánticamente débil (refinar con `cuota_mensual` en política futura), CF-03 enforce al versionar (Fase 2).
- **Auditoría APROBADA** (sign-off Fabián). `CLAUDE.md` → **Fase 2**. `CASES.md`: EV-01/02/03/05/06/07 🟢.

**Dónde quedó:** gate verde local y en CI (ruff · format · mypy 57 src+tests · lint-imports 3/3 · pytest 131). Pendiente OPCIONAL: revisión independiente del motor (subagente fresco o `/code-review ultra`) — control contra M3 (auditor=implementador).

**Próximos pasos (Fase 2 — Configurabilidad):** versionado inmutable de políticas en Postgres (SQLAlchemy + Alembic), API de gestión de reglas (`GestionarReglas`: crear versión con validación CF-01/02/03, activar como evento auditado ADR-008), snapshot de insumos persistido (ADR-004). Reemplazar repos en memoria por SQLAlchemy (cambio de binds en `di.py`). Mapeo entidad↔fila sólo en repos (frontera).

---

## 2026-06-26 · Fase 1 — Motor de evaluación + contrato de Insumos + política consumo v1

**Qué se hizo:** núcleo de Fase 1. Motor determinista funcionando punta a punta (en dominio).

- **Contrato de Insumos** cerrado (`CAMPOS_INSUMO`, 8 campos) + acceso uniforme `valor_y_disponibilidad(campo)`. Derivación de DTI en bps enteros con manejo de ingreso 0 (EV-03, sin división por cero). Disponibilidad por campo (buró parcial/ausente). Extendido `Solicitante` con `ingreso_mensual` y `situacion_laboral` (enum).
- **`MotorEvaluacion.evaluar`** implementado: PURO, hard-stops → scoring entero → bandas. Precedencia determinista documentada: RECHAZADO (hard-stop falla) > REVISION_MANUAL (forzar por dato faltante) > banda de score. Convención: el predicado expresa la condición para que la regla PASE. `EvaluacionRegla` extendido (tipo, disponibilidad, valor_observado, aporte_score, explicación) → rastro auditable real.
- **Política consumo v1** como dato semilla (`infrastructure/seed/politica_consumo.py`): 14 reglas (6 hard-stops + 8 scoring). Decisión de modelado: el scoring por tramos se expande a reglas booleanas con peso fijo y rangos excluyentes (fiel a ADR-002). Thin file (EV-02) = `meses_historial` NO_DISPONIBLE → FORZAR_REVISION. Bandas ≥70/40-69/<40. Umbrales = defaults v1 acordados con el usuario (refinables vía v2, ADR-003).
- **Tests:** 108 totales. Property-test de **determinismo del motor** (el invariante estrella) + score entero en rango. Casos: perfil limpio→APROBADO(85), morosidad→RECHAZADO, buró ausente→REVISION, ingreso 0→RECHAZADO (EV-03), thin file→REVISION (EV-02), empate banda 70→APROBADO (EV-07), contrato CF-03. `CASES.md` actualizado (EV-02/03/07 🟢; EV-04/05/06, CF-01/02/03 🟡).
- **R3 (placeholder `object`):** `Regla.predicado` ahora es `Predicado`; queda pendiente sólo `simular`/`criterio` (Fase 3) y `binder` (DI).

**Dónde quedó:** gate verde (ruff · mypy strict 45 · lint-imports 3/3 · pytest 108). Commits AST (`e8ee775`) + este incremento. **Falta para cerrar Fase 1:** caso de uso `EvaluarSolicitud` (idempotencia + fijar política + snapshot), **buró simulado** con fixtures por escenario, y **REST mínima** (endpoint de evaluación). Luego: Vista de halcón de Fase 1 + auditoría.

**Próximos pasos:** EvaluarSolicitud + BuroSimulado (fixtures: limpio/morosidad/thin file/ingresos no verificables/castigadas) + endpoint REST. Considerar R2 (CI) en este tramo.

---

## 2026-06-26 · Vista de halcón de Fase 0 + proceso institucionalizado

**Qué se hizo:** revisión crítica adversarial de Fase 0 y formalización del proceso.

- **Hallazgos y decisiones** (detalle en `docs/AUDIT.md`): 🔴 **B1** frontera `application ↛ infrastructure` no blindada → **corregido** (nuevo contrato import-linter, 3/3 KEPT). 🟡 **R4** smoke tests sólo en `domain` → **corregido** (`tests/test_imports.py` recorre las 4 capas; 71 tests). 🟡 R2 (CI) y R3 (placeholders `object`) → diferidos/deuda trackeada. M1/M2/M3 → menores.
- **Decisión de diseño:** el **dominio es stdlib-only** (sin Pydantic, ni puro). Se endureció `SAD §5.1` y se agregó `pydantic` a los módulos prohibidos del dominio en import-linter. Más estricto que el SAD original a propósito.
- **Proceso:** la **Vista de halcón** queda como gate obligatorio antes de cada transición de fase (`CLAUDE.md §7` + sección y plantilla en `docs/AUDIT.md`). Es el control independiente contra "auditor = implementador" (M3).

**Dónde quedó:** quality gate verde tras los fixes (ruff ✓ · mypy strict ✓ 47 archivos · lint-imports ✓ 3/3 · pytest ✓ 71). Listo para empezar Fase 1 con la frontera ya blindada. Pendiente commit+push de estos cambios.

**Próximos pasos:** sin cambios respecto al plan de Fase 1 (AST de `Predicado` → contrato de Insumos → reglas reales [validar umbrales con el usuario] → motor → buró simulado → property-test de determinismo → RUT módulo 11). Considerar cerrar R2 (CI con GitHub Actions) temprano en Fase 1.

---

## 2026-06-26 · Fase 0 — Scaffolding implementado (estructura + toolchain + esqueleto de dominio)

**Qué se hizo:** primer código del proyecto. Scaffolding completo de Fase 0.

- **Decisiones tomadas con el usuario** (3): (a) alcance = solo Fase 0 + checkpoint antes de Fase 1; (b) gestor de entorno = **uv**; (c) docs `AUDIT/TROUBLESHOOTING/CASES` movidos a `docs/` para coincidir con SAD §12 (fuente de verdad) — sus back-links `../CLAUDE.md` ahora resuelven bien.
- **Layout:** `src/` con paquetes top-level importables (`domain`, `application`, `infrastructure`, `interfaces`), tal como los referencian README/DEPLOY (`interfaces.rest.app`). No se inventó `veredicto.*`.
- **Dominio puro:** sólo stdlib (`dataclasses`/`enum`/`typing`). Cero Pydantic/ORM en el núcleo. Entidades inmutables (`frozen=True`). Enums del SAD modelados (Categoria, TipoRegla, AnteDatoFaltante, Disponibilidad, MetodoAgregacion, ResultadoDecision). Value objects con guardas anti-`float`/negativos (Monto, Dti en bps, Plazo). Servicios (`MotorEvaluacion`/`MotorSimulacion`) y casos de uso como esqueletos con `NotImplementedError` y TODO(Fase N) citando ADR/CASES. Puertos como `typing.Protocol`.
- **Toolchain (uv):** pyproject con ruff, mypy `strict`, pytest (+hypothesis), **import-linter** con 2 contratos (capas + pureza del dominio). docker-compose (Postgres 16), `.gitignore`, `.env.example`, `.python-version`.
- **Quality gate verde:** ruff ✓ · mypy strict ✓ (42 archivos) · **import-linter 2/2 KEPT** (la frontera dura del dominio se sostiene) · pytest ✓ (29 tests, Python 3.12.13). Tests de Fase 0 = humo + invariantes de VOs + chequeo programático de frontera del dominio.

**Dónde quedó:** **Fase 0 CERRADA Y AUDITADA (APROBADA, sign-off Fabián 2026-06-26).** Docker Desktop arrancado, `docker compose up -d db` → `veredicto-db` (postgres:16-alpine) **healthy**. Auditoría completa en `docs/AUDIT.md`. `CLAUDE.md` avanzado a **Fase 1**. Primer commit de git realizado.

**Próximos pasos (checkpoint → Fase 1):** 1) levantar Postgres y confirmar health. 2) Diseñar el AST de `Predicado` (Comparacion/Combinacion, `evaluar` puro, `campos_referenciados`, serialización). 3) Definir el "contrato de Insumos" (conjunto cerrado de `fuente_dato`). 4) Implementar `MotorEvaluacion` (hard-stops → scoring entero → bandas `>=`) + rastro. 5) Buró simulado con fixtures por escenario. 6) **Property-test de determinismo** (Hypothesis) — el invariante estrella. 7) RUT con validación módulo 11 (EV-01).

---

## [Fecha] · Fase 0 — Revisión crítica del SAD (v0.1 → v0.2)

**Qué se hizo:** revisión "ojo de halcón" del SAD y aplicación de 11 correcciones de fondo:
1. Corregido el diagrama de despliegue (MCP NO pasa por REST; ambos son adaptadores hermanos sobre casos de uso).
2. Manejo explícito de datos faltantes: disponibilidad por insumo + `ante_dato_faltante` por regla (ADR-009).
3. Versionado simplificado: la **política** es la única unidad atómica versionada; la regla no se versiona por separado (ADR-003).
4. Motor convertido en **intérprete estable**; toda la semántica (pesos, agregación, bandas) vive como dato en la política (ADR-008).
5. `ConfiguracionScoring` incorporada al modelo de `Politica`.
6. `REVISION_MANUAL` modelada hasta el override humano vía `DecisionFinal` (ADR-011); el flujo de revisión queda fuera de alcance.
7. Idempotencia de solicitudes vía `idempotency_key` (ADR-010).
8. Scoring con **enteros**, no `float` (determinismo real entre entornos) (ADR-006).
9. Activación de política como evento auditado + fijación de versión por request (anti-TOCTOU) (ADR-008).
10. Tensión retención vs. minimización de PII nombrada y resuelta (base legal + retención + pseudonimización) (§8.1).
11. Firma de simulación alineada: `simular_cambio_regla(politica_candidata, poblacion)`.

**Además:** sincronizados los invariantes en `CLAUDE.md` (ahora 12) para no contradecir al SAD.

**Dónde quedó:** SAD en v0.2, internamente consistente (sin referencias obsoletas; 11 ADRs secuenciales). Sigue sin código.

**Próximos pasos:** spec de Fase 1 (motor + rastro). Definir contrato de `Insumos` con disponibilidad, las ~8-10 reglas reales de la política de consumo, y el modelo de `Predicado` y `RastroDecision`.

---

## [Fecha de inicio] · Fase 0 — Scaffolding

**Qué se definió:**
- Arquitectura completa documentada en `SAD.md` (estructura arc42, 7 ADRs).
- Decisión núcleo: motor de evaluación como función pura; reglas como datos versionados; snapshot de insumos para reproducibilidad; MCP como adaptador delgado paralelo a REST.
- Sistema de documentación viva establecido: `CLAUDE.md` (hub), `MEMORY.md` (bitácora), `AUDIT.md`, `TROUBLESHOOTING.md`, `CASES.md`, `README.md`, `DEPLOY.md`.
- Alcance del portafolio: fases 1–4. Fase 5 (AWS/ML/MCP remoto) opcional.

**Dónde quedó:**
- Documentación base creada. Sin código aún.

**Próximos pasos (Fase 0 → 1):**
- Crear estructura de paquetes `domain/ application/ infrastructure/ interfaces/`.
- Levantar Postgres en Docker.
- Configurar `injector`, pytest, linter de fronteras de imports.
- Definir las primeras ~8-10 reglas reales de una política de consumo chileno (DTI, verificación de ingresos, morosidad, etc.).

---

<!-- Anexar nuevas entradas ARRIBA de esta línea, más reciente primero. -->
