# TROUBLESHOOTING.md — Bitácora de errores y soluciones

> Objetivo: que **ningún error se repita**. Antes de pelear con un problema, busca aquí. Al resolver uno nuevo, regístralo.
> Hub: [`../CLAUDE.md`](../CLAUDE.md)
>
> Formato: **Síntoma → Contexto → Causa raíz → Solución → Regla de prevención.**
> La "regla de prevención" es lo más importante: si es general, considéra subirla a `CLAUDE.md`.

---

## Entradas

<!-- Anexar nuevas entradas ABAJO. Numerar correlativamente. -->

### TS-001 · import-linter falla con "include_external_packages=True" requerido

- **Síntoma:** `lint-imports` aborta: *"The top level configuration must have include_external_packages=True when there are external forbidden modules."*
- **Contexto:** Fase 0. Contrato `forbidden` que prohíbe al dominio importar paquetes externos (sqlalchemy, fastapi, fastmcp, psycopg…) para vigilar la frontera dura (invariante 2).
- **Causa raíz:** import-linter sólo construye el grafo de paquetes externos si se lo pide explícitamente; sin esa bandera no puede evaluar módulos prohibidos que no sean del propio repo.
- **Solución:** `include_external_packages = true` en `[tool.importlinter]` de `pyproject.toml`.
- **Regla de prevención:** todo contrato `forbidden` que liste paquetes de terceros exige `include_external_packages = true`. Documentado junto al contrato.

### TS-002 · Python del sistema 3.11, proyecto exige 3.12

- **Síntoma:** `python --version` = 3.11.5; el proyecto requiere `>=3.12`.
- **Contexto:** Fase 0, primer arranque del entorno en la máquina de desarrollo (Windows).
- **Causa raíz:** el Python global no cumple `requires-python`.
- **Solución:** **uv** gestiona la versión: `uv sync` descarga y usa Python 3.12 en `.venv` sin tocar el Python del sistema. uv se instaló con `pip install --user uv`.
- **Regla de prevención:** no depender del Python global; correr todo con `uv run`. `.python-version` fija 3.12 para el proyecto.

### TS-000 (ejemplo/plantilla)

- **Síntoma:** descripción observable del error (mensaje, comportamiento).
- **Contexto:** fase, módulo, qué se intentaba hacer.
- **Causa raíz:** la causa real, no el síntoma.
- **Solución:** qué se hizo para resolverlo.
- **Regla de prevención:** cómo evitar que vuelva a ocurrir.

---

## Trampas anticipadas (riesgos conocidos, aún no ocurridos)

Estos no son errores que pasaron, sino los que la experiencia dice que pasarán. Cuando ocurra alguno, conviértelo en una entrada `TS-NNN` formal.

- **No-determinismo escondido.** Un `datetime.now()`, un `set` sin orden, o un `dict` cuyo orden de iteración importa, dentro del motor, romperá el property-test de determinismo y la reproducibilidad de auditoría. *Prevención:* el motor recibe el tiempo como parámetro; usar estructuras con orden estable.
- **ORM filtrándose al dominio.** Importar un modelo SQLAlchemy en `domain/` rompe la frontera. *Prevención:* linter de imports; mapeo entidad↔fila sólo en repositorios.
- **Pydantic-HTTP confundido con modelo de dominio.** Reusar el schema de request de FastAPI como entidad de dominio acopla la API al núcleo. *Prevención:* DTOs separados de entidades; traducción explícita en la capa de entrada.
- **Simulación que re-llama al buró.** Si el what-if vuelve a pedir datos al buró en vez de usar el snapshot, deja de ser reproducible. *Prevención:* la simulación lee `snapshot de insumos`, nunca el gateway.
- **Migraciones de Postgres divergentes del modelo.** *Prevención:* migraciones versionadas (Alembic) desde Fase 2; nunca editar el esquema a mano.
- **Descripción de herramienta MCP ambigua.** Si la descripción es vaga, el modelo elige mal qué herramienta llamar. *Prevención:* descripciones específicas y validación de parámetros con errores explícitos.
