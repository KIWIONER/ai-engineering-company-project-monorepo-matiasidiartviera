# Informe de Gobernanza y Prácticas Seguras NIST CSF 2.0 — Nexova Solutions

- **Fecha:** `2026-11-21`
- **Rama objetivo:** `feature/nist-security-practices`
- **Marco Regulatorio Aplicable (`nexova-cybersecurity-BRIEFING.md`):**
  - **España / Unión Europea:** **RGPD** (minimización de datos, limitación de propósito, supervisión humana en decisiones automatizadas y notificación a la **AEPD en 72 horas**) + **Ley de IA de la UE** (Reglamento UE 2024/1689 — *scoring* de candidatos clasificado como **Alto Riesgo**).
  - **Estados Unidos (Florida):** **FIPA** (Florida Information Protection Act — notificación en **30 días**) y **FCRA** (Fair Credit Reporting Act, aplicable si Nexova realiza verificación de antecedentes en selección).
- **Documentos relacionados:** [README.md](README.md) (mapa de entradas LLM + `.env.example`), [ai-inventory.md](ai-inventory.md) (inventario completo y responsabilidad compartida).

---

## 1. Roles y Responsabilidades (RACI)

| Rol NIST / Respuesta a Incidentes | Responsable Asignado | Autoridad |
| :--- | :--- | :--- |
| Líder de Gobernanza / Compliance | Responsable de Compliance + Sergio Molina (CTO) | Aprobar inventario vivo, política de datos y aceptación de riesgos |
| Líder de Respuesta a Incidentes | Sergio Molina (CTO) + Equipo SRE | Coordinar contención, rotar claves API/JWT y aislar servicios |
| Oficial de Comunicaciones | Laura Mendoza (CEO) + Legal | Notificar a clientes, **AEPD (72h)** o afectados bajo **FIPA (30d)** |
| Propietarios de Sistemas IA | Javier Almeida (Selección), Roberto Díaz (Soporte), Megan Clarke (Ventas) | Supervisión humana (HITL) y validación operativa de su área |

---

## 2. Evaluación por las 6 Funciones NIST CSF 2.0

| Función NIST | Estado | Controles Implementados (Evidencia en Código / Docs) | Acción Concreta Priorizada | Prioridad |
| :--- | :---: | :--- | :--- | :---: |
| **1. Govern** | **Implementado** | Inventario vivo + matriz de responsabilidad compartida con OpenAI/Qdrant (`ai-inventory.md`), marco RGPD/FIPA/FCRA/EU AI Act y RACI definidos. | Vincular actualización obligatoria de `ai-inventory.md` en cada PR que añada prompts o modelos. | **P1** |
| **2. Identify** | **Implementado** | Mapa de los 6 puntos de entrada externos al LLM (`README.md`), inventario de los 4 sistemas de IA de Nexova y clasificación de riesgo. | Revisar trimestralmente términos de retención/no-entrenamiento de proveedores LLM. | **P1** |
| **3. Protect** | **Implementado** | Secretos sin fallback hardcoded (`services/api/security.py`, `mcps/company_tools/config.py`, `.env.example`); puerta determinista `review_action` (*fail-secure*) y minimización RGPD (`services/agent/action_gate.py`); rate limiting `429` y tope de 4000 chars (`services/api/rate_limiter.py` en `/agent/query` y `/knowledge/query`); aislamiento multi-tenant MCP/RAG y Prompt Injection guardrails (`services/agent/guardrails.py`). | Migrar secretos locales `.env` a Vault/KMS gestionado y mover el rate limiter en memoria a Redis compartido (`GAP-01`, `GAP-02`). | **P0** |
| **4. Detect** | **Implementado (Base)** | Logging forense estructurado de decisiones del agente con redacción de secretos/PII (`agent_audit_logger` en `services/agent/action_gate.py` conectado en `/agent/query`), `GuardrailTracker` (`services/agent/guardrails.py`) y `audit_logger` MCP (`mcps/company_tools/auth.py`). | Conectar logs `[AGENT-AUDIT]` y `[GUARDRAIL]` a alertas calibradas por picos de `429` o bloqueos repetidos (`GAP-03`). | **P1** |
| **5. Respond** | **Documentado** | Plan de contención definido: revocación inmediata de `OPENAI_API_KEY`/`SECRET_KEY`/`MCP_JWT_SECRET`, aislamiento de cuentas y notificación legal dentro de **72h (AEPD / RGPD)** y **30 días (FIPA)**. | Realizar simulacro trimestral de fuga de clave API y notificación regulatoria. | **P1** |
| **6. Recover** | **Documentado** | Objetivos definidos (**RTO: 1 hora** para API/Agente de soporte; **RPO: 15 minutos** para BD de tickets/checkpoints), respaldos de SQLite/Qdrant y retroalimentación mediante postmortem hacia *Identify/Protect*. | Automatizar pruebas mensuales de restauración de copias de seguridad en entorno staging. | **P2** |

---

## 3. Acciones Irreversibles y Verificación HITL (`nexova-cybersecurity-BRIEFING.md` §5)

| Acción Irreversible (Briefing §5) | ¿Requiere Confirmación Humana? | Mecanismo Determinista en Código |
| :--- | :---: | :--- |
| Descartar (rechazar) a un candidato automáticamente | **Sí** | `discard_candidate` en `CONFIRM_ACTIONS` (`services/agent/action_gate.py`) → `review_action()` devuelve `"confirm"` + `build_hitl_confirmation_message()` |
| Enviar una propuesta comercial o contrato | **Sí** | `send_commercial_proposal` en `CONFIRM_ACTIONS` (`services/agent/action_gate.py`) → devuelve `"confirm"` (además de flujo HITL en `rfp_intake`) |
| Marcar ticket de soporte como resuelto con queja o dato sensible | **Sí** | `resolve_sensitive_ticket` en `CONFIRM_ACTIONS` (`services/agent/action_gate.py`) → devuelve `"confirm"` |
| Modificar estado de candidato en el ATS de forma masiva | **Sí** | `bulk_update_ats` en `CONFIRM_ACTIONS` + `BULK_THRESHOLD = 10` (`services/agent/action_gate.py`) → devuelve `"confirm"` |

---

## 4. Brechas Pendientes (Riesgo y Mitigación Propuesta)

| ID | Brecha No Corregida en este Ciclo | Riesgo / Impacto | Mitigación Propuesta |
| :--- | :--- | :--- | :--- |
| `GAP-01` | Secretos gestionados mediante `.env` en disco en lugar de Vault/KMS cloud | Si se compromete el host, las claves en `.env` requieren rotación manual inmediata. | Migrar `SECRET_KEY`, `MCP_JWT_SECRET` y `OPENAI_API_KEY` a AWS Secrets Manager / HashiCorp Vault con rotación automática. |
| `GAP-02` | `SlidingWindowRateLimiter` en memoria local del proceso | En despliegues con múltiples réplicas/workers de FastAPI, la cuota no se comparte entre réplicas. | Respaldar el contador de ventana deslizante en **Redis** (`redis:6379`) aprovechando el contenedor ya existente en `docker-compose.yml`. |
| `GAP-03` | Sin envío automatizado de alertas a SIEM / Slack desde `[AGENT-AUDIT]` | Detección dependiente de inspección manual de logs. | Configurar agregador de logs con umbral de alerta ante >10 bloqueos `jailbreak` o `429` en 5 minutos. |

---

## 5. Evidencia Reproducible (Fase 4)

- **Suite de pruebas NIST + Guardrails (`uv run pytest tests/test_nist_security_practices.py tests/pipelines/test_agent_guardrails.py -v`):**
  - **Resultado:** **`20 passed`**:
    - `test_nist_action_gate_fail_secure_and_hitl_irreversible`: valida las 4 acciones irreversibles del Briefing §5 (`confirm`), umbral `BULK_THRESHOLD` y rechazo *fail-secure* (`denied`) de acciones desconocidas/sin `type`/path traversal/cross-tenant.
    - `test_nist_rgpd_data_minimization`: valida `minimize_user_context` omitiendo `pretension_salarial` y `telefono`.
    - `test_nist_rate_limiting_returns_429_and_rejects_oversized_prompt`: valida `429 Too Many Requests` en `POST /agent/query` y rechazo de entradas sobredimensionadas.
    - `test_nist_forensic_logging_and_prompt_injection_via_endpoint`: valida bloqueo de Prompt Injection vía `POST /agent/query`, registro en `agent_audit_logger` (`user_id`, `model`, `verdict="denied"`) y redacción `[REDACTED]` de `api_key` y `Bearer`.
- **Escaneo Estático (`bash skills/security-audit-suite/scripts/quick_security_scan.sh .`):**
  - `Posibles Claves Hardcodeadas / Claves Privadas`: `[OK] Sin coincidencias.`
