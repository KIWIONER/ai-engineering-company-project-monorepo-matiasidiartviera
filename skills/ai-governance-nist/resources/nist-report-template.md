# Informe de Gobernanza y Prácticas Seguras NIST CSF 2.0 — `<Empresa>`

- **Fecha:** `AAAA-MM-DD`
- **Rama / Commit:** `<rama>` (`<sha>`)
- **Marco Regulatorio Aplicable:** `<Citar normativa específica de BRIEFING.md: ej. RGPD (AEPD 72h), FIPA (30 días), FCRA, Ley de IA UE>`

---

## 1. Resumen Ejecutivo y Roles (RACI)

| Rol NIST / Incidente | Responsable Asignado | Autoridad |
| :--- | :--- | :--- |
| Líder de Gobernanza / Compliance | `<Nombre / CTO / Legal>` | Aprobar políticas, inventario y aceptación de riesgos |
| Líder de Respuesta a Incidentes | `<Nombre / SRE / CTO>` | Coordinar contención, revocar claves y aislar servicios |
| Oficial de Comunicaciones | `<Nombre / Legal / CEO>` | Notificar a clientes y autoridades dentro del plazo legal |

---

## 2. Evaluación por las 6 Funciones NIST CSF 2.0

| Función NIST | Estado Actual | Controles Implementados (Evidencia) | Brecha / Acción Priorizada | Prioridad |
| :--- | :---: | :--- | :--- | :---: |
| **1. Govern** | `Parcial / Completo` | `<Política, RACI, marco regulatorio y terceros>` | `<Acción concreta>` | `P1` |
| **2. Identify** | `Parcial / Completo` | `<Inventario de IA + mapa de entradas LLM>` | `<Acción concreta>` | `P1` |
| **3. Protect** | `Parcial / Completo` | `<Secretos env, action_gate, HITL, rate limiting, prompt isolation>` | `<Acción concreta>` | `P0` |
| **4. Detect** | `Parcial / Completo` | `<Logging forense de agente, GuardrailTracker, alertas>` | `<Acción concreta>` | `P1` |
| **5. Respond** | `Parcial / Completo` | `<Runbook de contención, rotación de claves, plazos 72h/30d>` | `<Acción concreta>` | `P1` |
| **6. Recover** | `Parcial / Completo` | `<RTO/RPO definidos, pruebas de restore, postmortem>` | `<Acción concreta>` | `P2` |

---

## 3. Acciones Irreversibles y Verificación HITL

| Acción Irreversible (según `BRIEFING.md`) | ¿Requiere Confirmación Humana? | Mecanismo en Código / Evidencia |
| :--- | :---: | :--- |
| `<ej. Descartar candidato>` | `Sí` | `<action_gate / LangGraph interrupt + test>` |

---

## 4. Brechas Pendientes (Riesgo y Mitigación Propuesta)

| ID | Brecha No Corregida en este Ciclo | Riesgo / Impacto | Mitigación Propuesta y Plazo |
| :--- | :--- | :--- | :--- |
| `GAP-01` | `<ej. Vault gestionado KMS en lugar de .env local>` | `<Exposición si se compromete el host>` | `<Migrar a AWS Secrets Manager / Vault en próximo sprint>` |

---

## 5. Evidencia Reproducible de Pruebas

- **Prompt Injection:** `<comando pytest y resultado>`
- **Rate Limiting:** `<comando/test que demuestra HTTP 429>`
- **Logging y Puerta de Acciones (`action_gate`):** `<comando/test que demuestra denied / confirm / allowed + log>`
