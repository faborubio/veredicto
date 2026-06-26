"""Infraestructura: adaptadores concretos que implementan los puertos del dominio.

Aquí —y sólo aquí— viven SQLAlchemy, psycopg y el buró simulado. La traducción
entidad↔fila ocurre en los repositorios; ningún modelo ORM cruza al dominio
(frontera dura, CLAUDE.md invariante 2).
"""
