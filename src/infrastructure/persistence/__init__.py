"""Adaptadores de persistencia (SQLAlchemy 2.0 + PostgreSQL).

Repositorios que implementan los puertos del dominio y mapean entidad↔fila.
Migraciones con Alembic desde Fase 2 (TROUBLESHOOTING.md: nunca editar el esquema
a mano). En Fase 1 se puede empezar con repos en memoria (fakes) para los tests
de casos de uso (SAD §8.2).
"""
