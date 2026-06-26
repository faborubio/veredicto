"""Entidades del dominio.

Modeladas como dataclasses inmutables (`frozen=True`) cuando representan hechos
auditables (DecisionMotor, Politica, RastroDecision): editar = crear una versión
nueva, nunca mutar (ADR-003, ADR-004).
"""
