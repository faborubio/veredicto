# MEMORY.md — Bitácora del proyecto

> Registro cronológico de decisiones significativas y estado. Es la memoria **del proyecto**, versionada en el repo y portable entre sesiones/agentes. Si hay conflicto con la memoria interna de un agente, **gana este archivo**.
> Hub: [`CLAUDE.md`](./CLAUDE.md)
>
> Formato de entrada: fecha · fase · qué se hizo · dónde quedó · próximos pasos.

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
