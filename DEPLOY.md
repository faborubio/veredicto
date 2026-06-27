# DEPLOY.md — Runbook de despliegue

> Despliegue por fases: primero local (costo ~USD 0), luego remoto opcional.
> Hub: [`./CLAUDE.md`](./CLAUDE.md) · Arquitectura de despliegue: [`./SAD.md §7`](./SAD.md#7-vista-de-despliegue)

---

## Fase local (portafolio · ~USD 0)

### Componentes

- **PostgreSQL** en Docker (o free tier Neon/Supabase).
- **API REST** (uvicorn) en local.
- **Servidor MCP** en transporte `stdio` — sin servidor que mantener.
- **Host MCP:** Claude Desktop, que arranca el servidor MCP como subproceso.

### Pasos

```bash
# 1. Base de datos
docker compose up -d db
alembic upgrade head

# 2. Verificar la API (opcional)
uvicorn interfaces.rest.app:app --reload
# probar en http://localhost:8000/docs

# 3. Servidor MCP local (stdio): no se "levanta" suelto;
#    lo arranca el host. Verificar con el MCP Inspector:
npx @modelcontextprotocol/inspector python -m interfaces.mcp.server
```

> ⚠️ **El MCP necesita `VEREDICTO_PERSISTENCIA=sql` para ver decisiones reales.**
> Por defecto el server levanta la persistencia **en memoria** (`ModuloMemoria`),
> que en un proceso nuevo arranca con el repositorio de decisiones **vacío** —
> `consultar_decision` / `explicar_decision` / `rastro_auditoria` devolverán
> `no_encontrada`. Para consultar decisiones reales, el MCP debe apuntar a la
> **misma Postgres que escribe REST** (`VEREDICTO_PERSISTENCIA=sql` + `DATABASE_URL`).
> `listar_reglas` y `simular_cambio_regla` sí operan sobre la política sembrada aun
> en memoria. La cobertura de protocolo (initialize/list/call) está en
> `tests/test_mcp_protocol_e2e.py`; este `npx` es el smoke manual del transporte stdio.

### Conectar a Claude Desktop

Agregar el servidor a la configuración de MCP del host (ejemplo conceptual):

```json
{
  "mcpServers": {
    "veredicto": {
      "command": "python",
      "args": ["-m", "interfaces.mcp.server"],
      "env": { "DATABASE_URL": "postgresql://..." }
    }
  }
}
```

Reiniciar Claude Desktop; las herramientas (`consultar_decision`, `explicar_decision`, `simular_cambio_regla`, etc.) deberían aparecer disponibles.

### Checklist de salud (local)

- [ ] Postgres responde y migraciones aplicadas.
- [ ] `pytest` verde.
- [ ] MCP Inspector lista las herramientas sin error.
- [ ] Claude Desktop ve las herramientas y `explicar_decision` devuelve un rastro legible.

---

## Fase remota (opcional · ~USD 10–20/mes)

> No abordar hasta que la fase local esté auditada (`AUDIT.md`). Agrega auth/TLS/operación que no aportan al núcleo del valor.

### Componentes

- **Cómputo:** VPS chico (Hetzner ~USD 4 / DigitalOcean ~USD 6) o AWS (Lightsail / ECS Fargate; free tier inicial).
- **Transporte MCP:** Streamable HTTP (reemplaza al SSE legacy), alineado con el **núcleo stateless** de la spec MCP 2026-07-28 → escalable detrás de un balanceador.
- **Auth:** OAuth 2.1 (la spec clasifica al servidor MCP remoto como OAuth Resource Server, con descubrimiento vía `.well-known`). Auto-hospedado o free tier de Auth0/Clerk/WorkOS.
- **Dominio + TLS:** dominio ~USD 10–15/año; TLS gratis (Let's Encrypt o tras el balanceador).
- **Base de datos:** Postgres gestionado (free tier o RDS pequeño).
- **Contenedor:** imagen Docker; registry Docker Hub (free) o ECR.

### Nota de latencia (Chile)

Los VPS baratos de Hetzner están en Europa/EE.UU. Para un demo da igual; para clientes chilenos reales preferir una región cercana (ej. AWS São Paulo). Hetzner además exige verificación de identidad antes de activar la cuenta.

### Workflow de apertura async (si se construye Fase 5)

SQS/SNS para desacoplar etapas del ciclo de apertura de crédito (solicitud → evaluación → aprobación → desembolso → cierre), con idempotencia por etapa. S3 para artefactos/documentos.

---

## Variables de entorno (previstas)

| Variable | Descripción |
|----------|-------------|
| `DATABASE_URL` | Cadena de conexión a PostgreSQL. |
| `ENV` | `local` / `staging` / `prod`. |
| `LOG_LEVEL` | Nivel de logging. |
| `BURO_MODE` | `simulado` (siempre, en este proyecto). |
| `MCP_TRANSPORT` | `stdio` (local) / `http` (remoto). |

> Nunca commitear valores reales. Usar `.env` local (gitignored) y secretos del proveedor en remoto.
