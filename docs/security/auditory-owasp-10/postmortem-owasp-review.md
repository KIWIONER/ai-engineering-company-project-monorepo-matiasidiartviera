# Postmortem — Revisión de Auditoría OWASP Top 10 y Endurecimiento (Nexova)

- **Fecha:** `2026-11-21`
- **Rama:** `feature/owasp-top10-audit`
- **Disparador:** Rechazo inicial en revisión de Tech Lead (Sandra) sobre la primera entrega del PR.

---

## 1. Resumen del Incidente de Revisión

Aunque la primera entrega había cerrado CORS comodín, `pickle.loads`, IDOR en `/users/`, `SECRET_KEY` hardcoded y patrones de *Prompt Injection*, el PR fue devuelto por **dos brechas críticas de evidencia y autorización**:

1. **Endurecimiento de servidor solo en documentación:** existía una guía (`server-hardening-guide.md`) y endurecimiento de Docker, pero faltaba la **evidencia real aplicada** en un servidor (`sshd -T`, `id`, `stat`, `ufw status verbose`, `ss -tlnp`) porque el Codespace bloqueaba `sudo` (`no new privileges`).
2. **OWASP A01 crítico abierto en la capa agéntica y RAG:**
   - `incidents_get_status` (`mcps/company_tools/tools_incidents.py`) validaba únicamente el scope OAuth `incidents:read`, permitiendo leer cualquier `ticket_id` sin comprobar el `tenant_id`/`branch` propietario.
   - `POST /knowledge/query` (`services/api/routes/knowledge.py` + `data/pipelines/rag.py`) ejecutaba `retrieve(...)` sobre Qdrant sin filtrar por `role`, `department` o `tenant_id` del usuario autenticado (y devolvía `str(exc)` en errores 500).
   - Los *guardrails* (`services/agent/guardrails.py`) bloqueaban frases literales de ataque, pero no ejercían autorización de datos.

---

## 2. Causa Raíz

- **Confusión entre autenticación/scope y autorización por recurso (A01):** validar un token JWT o un scope general (`incidents:read`) no impide el acceso horizontal entre tenants si no se compara la identidad del llamante contra el propietario del recurso.
- **Confianza implícita en el entorno de desarrollo (Codespace):** no haber validado desde el inicio los comandos de hardening sobre el VPS real (`bc-vps-238`) dejó la puerta de infraestructura respaldada solo por texto y no por salidas del sistema operativo.

---

## 3. Acciones de Remediación Ejecutadas

1. **Aislamiento multi-tenant *default-deny* en MCP (`mcps/company_tools/auth.py`, `tools_incidents.py`):**
   - Añadido soporte de `tenant_id` y `role` en `create_access_token`.
   - Implementado `check_tenant_access(auth_info, resource_tenant, tool_name)` dentro de `incidents_get_status` (tanto en la ruta HTTP como en el respaldo TinyDB), bloqueando con `403 Forbidden` cualquier consulta cross-tenant.
2. **Autorización por rol, departamento y tenant en RAG (`data/pipelines/rag.py`, `services/api/routes/knowledge.py`):**
   - Implementado `_is_chunk_authorized(...)` en `retrieve(...)` para filtrar fragmentos según `user_role`, `user_department` y `user_tenant` del `current_user` autenticado.
   - Sanitizado el mensaje de error HTTP 500 en `/knowledge/query` para no filtrar trazas internas.
3. **Pruebas reproducibles de dos tenants (`tests/test_owasp_security_audit.py`):**
   - Añadidos `test_sec06_mcp_incidents_get_status_enforces_two_tenants` (`valencia` vs `miami`) y `test_sec06_rag_knowledge_query_enforces_two_tenants_and_departments` (`soporte/valencia` vs `rrhh/miami`).
   - Verificado con `uv run pytest tests/test_owasp_security_audit.py tests/test_mcp_server.py tests/pipelines/test_rag.py tests/pipelines/test_agent_guardrails.py -v` → **`43 passed`**.
4. **Endurecimiento real aplicado en VPS (`bc-vps-238` · `104.248.36.5`):**
   - Creado usuario no-root `deployuser` con `sudo`, deshabilitado `PermitRootLogin no` vía `/etc/ssh/sshd_config.d/99-hardening.conf`, aplicados permisos `750` (`/opt/nexova/app`, `/var/log/nexova`) y `600` (`/opt/nexova/.env`), y activado `ufw` *default-deny* permitiendo solo `22/tcp` y `443/tcp`.
   - Salidas Antes y Después documentadas en `docs/security/auditory-owasp-10/owasp-top10-audit-report.md` (§3.2).

---

## 4. Lecciones Aprendidas y Reglas Preventivas

- **Regla de Oro A01 para Agentes y RAG:** Ningún *guardrail* textual sustituye a la autorización determinista por `tenant_id`/`role`/`department` en tools MCP y consultas vectoriales.
- **Regla de Evidencia de Infraestructura:** Un cambio de hardening solo se considera cerrado cuando existe salida real verificable (`sshd -T`, `id`, `stat`, `ufw status verbose`, `ss -tlnp`) sobre el servidor objetivo.
