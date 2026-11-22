# Inventario Vivo de Sistemas de IA y Responsabilidad Compartida — Nexova Solutions

- **Última actualización:** `2026-11-21`
- **Responsable de Gobernanza:** `Sergio Molina (CTO)` & `Responsable de Compliance`
- **Marco Regulatorio Aplicable:** **RGPD** (España/UE — notificación a la **AEPD** en **72 horas**), **FIPA** (Florida, EE. UU. — notificación en **30 días**), **FCRA** (EE. UU. si aplica verificación de antecedentes en selección) y **Ley de IA de la UE** (Reglamento UE 2024/1689).

---

## 1. Inventario de Sistemas de IA (Alcance Nexova)

| Componente / Sistema IA | Propietario Interno | Modelo y Proveedor | Datos de Entrada (¿PII / Sensible?) | Retención y Entrenamiento Proveedor | Nivel Riesgo (EU AI Act / Regulación) | Revisión Humana (HITL) | Plan ante Fallos / Contingencia |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **Pipeline de selección asistida (scoring de CVs)** | Javier Almeida (Operaciones de Selección) + Sergio Molina (CTO) | `gpt-4o-mini` (OpenAI API) + reglas deterministas | CVs, historial laboral, habilidades y pretensión salarial (**PII sensible**) | API comercial OpenAI: no entrena con entradas por defecto; retención máx. 30 días para abuso | **Alto Riesgo** (empleo/reclutamiento EU AI Act) + **RGPD / FCRA** | **Sí** (prohibido descartar candidato o cambiar ATS masivo sin humano) | Revisión manual directa por consultores de selección |
| **RAG sobre base de candidatos y conocimiento** | Javier Almeida + Sergio Molina (CTO) | Embeddings locales/OpenAI + `gpt-4o-mini` + **Qdrant** (`nexova_knowledge`) | Consultas internas, fichas de procedimientos y perfiles (**PII si incluye candidatos**) | Qdrant self-hosted en red interna (`127.0.0.1:6333`); OpenAI API sin entrenamiento | **Riesgo Limitado / Alto** (según uso en selección) + **RGPD** (minimización) | **Sí** (solo lectura/síntesis; filtro estricto por `role`/`department`/`tenant_id`) | Respuesta honesta de rechazo (*fallback* sin contexto) |
| **Agente de soporte de primera línea (outsourcing)** | Roberto Díaz (Soporte Externalizado) + Sergio Molina (CTO) | LangGraph + `gpt-4o-mini` (OpenAI) + **FastMCP** (`company_tools`) | Tickets de clientes, nombres, emails y estado de incidencias (**PII clientes**) | API comercial sin entrenamiento; logs locales con redacción | **Riesgo Limitado** (transparencia IA) + **RGPD / FIPA** | **Sí** (obligatorio antes de cerrar tickets sensibles o con queja, y en memoria) | Escalamiento automático a agente humano de soporte |
| **Agente de prospección comercial y flujo RFP** | Megan Clarke (Ventas) + Sergio Molina (CTO) | LangGraph (`rfp_intake`) + `gpt-4o-mini` (OpenAI) | Datos de contacto de prospectos, propuestas y presupuestos (**PII comercial**) | API comercial sin entrenamiento; checkpoints en SQLite (`JsonPlusSerializer`) | **Riesgo Mínimo / Limitado** + **RGPD / FIPA** | **Sí** (prohibido enviar propuesta o contrato comercial sin aprobación humana) | Revisión y redacción manual por Account Manager |

---

## 2. Matriz de Responsabilidad Compartida (Interno vs. Proveedores Terceros)

Usar proveedores externos (**OpenAI**, **Qdrant**) **no transfiere la responsabilidad** legal ni operativa de Nexova:

| Área de Control | Proveedor Externo (OpenAI — *Encargado / Proveedor*) | Nexova Solutions (*Responsable del Tratamiento / Desplegador*) |
| :--- | :--- | :--- |
| **Entrenamiento e infraestructura del modelo** | Entrenamiento base, pesos del modelo, parches y seguridad de la plataforma API | Verifica cláusulas DPA, política de no-entrenamiento y retención; audita actualizaciones de versión |
| **Propósito y base legal del tratamiento** | N/A | Define la base legal (**RGPD**), notifica al usuario que interactúa con IA y clasifica el riesgo (EU AI Act) |
| **Minimización de datos enviados al prompt** | Procesa únicamente el payload recibido | Extrae solo campos necesarios antes de llamar al modelo; omite PII innecesaria (salarios/teléfonos) |
| **Control de acceso, secretos y herramientas** | N/A | Custodia API keys en `.env`/vault (`fail-secure`), aplica `rate limiting`, anti-IDOR y `action_gate` + HITL |
| **Gestión de brechas y notificación legal** | Notifica incidentes de su infraestructura según contrato | Lidera contención, investiga causa raíz y notifica a **AEPD (72h)** o bajo **FIPA (30 días)** |
