"""Núcleo puro del dominio (Clean Architecture, ADR-001).

Frontera dura (CLAUDE.md invariante 2): este paquete NO importa SQLAlchemy,
FastAPI, FastMCP, ni Pydantic-para-HTTP. Sólo biblioteca estándar. La pureza se
audita con import-linter (ver pyproject.toml [tool.importlinter]).
"""
