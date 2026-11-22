# Inventario de Sistemas de IA y Superficie de Entradas — `<Empresa>`

- **Última actualización:** `AAAA-MM-DD`
- **Responsable de Gobernanza:** `<Nombre / Rol>`

---

## 1. Inventario Vivo de Sistemas de IA

| Función / Sistema IA | Propietario Interno | Modelo y Proveedor | Datos de Entrada (¿PII / Sensible?) | Retención y Entrenamiento Proveedor | Nivel Riesgo (EU AI Act / Regulación) | Revisión Humana (HITL) | Plan ante Fallos / Contingencia |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| `<ej. Scoring de CVs>` | `<Operaciones + CTO>` | `<gpt-4o-mini · OpenAI>` | `<CVs, historial laboral (PII)>` | `<No entrena vía API; retención 30d>` | `<Alto Riesgo · RGPD / FCRA>` | `Sí (antes de descartar)` | `<Revisión manual por consultor>` |

---

## 2. Matriz de Responsabilidad Compartida (Control Interno vs. Tercero)

| Área de Control | Proveedor Externo (Encargado) | Equipo Interno (Responsable / Desplegador) |
| :--- | :--- | :--- |
| Entrenamiento e infraestructura del modelo | Posee pesos, hosting y parches del modelo | Verifica términos de no-entrenamiento y DPA |
| Selección de propósito y datos enviados | N/A | Decide propósito legal, minimiza PII y filtra contexto |
| Secretos, acceso y herramientas (MCP/RAG) | N/A | Custodia API keys en env/vault, aplica anti-IDOR y HITL |
| Notificación al usuario y brechas | Notifica incidentes propios según contrato | Informa uso de IA y notifica a autoridad (ej. AEPD 72h / FIPA 30d) |

---

## 3. Mapa de Puntos de Entrada Externos al LLM

Lista cada origen desde el que texto externo entra en la ventana de contexto de un modelo:

| Punto de Entrada | Origen del Texto | Archivo / Endpoint | Riesgo Principal | Control Mitigador |
| :--- | :--- | :--- | :--- | :--- |
| `<Chat de soporte>` | `<Usuario autenticado>` | `<POST /agent/chat>` | `<Prompt Injection directa / costo>` | `<Delimitación + rate limit + action_gate>` |
| `<Base de conocimiento>` | `<Chunks Qdrant>` | `<POST /knowledge/query>` | `<Inyección indirecta / fuga cross-tenant>` | `<Filtro role/tenant + isolate_external_chunks>` |
