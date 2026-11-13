# Implementation Plan: Agente de Soporte con LangGraph — Parte 2: Herramientas Fuera del RAG

## 📌 Resumen Ejecutivo
Extensión del agente de soporte con LangGraph para incorporar herramientas externas (`tools`) en tiempo real desacopladas del RAG documental, con enrutamiento autónomo de intenciones y resiliencia ante fallos.

## 🏛️ Decisiones de Arquitectura
1. **Tool de Incidentes en Tiempo Real (`services/agent/tools.py`):**
   - Función tipada `get_incident_ticket(ticket_identifier: str, timeout: float = 5.0) -> Optional[Dict[str, Any]]`.
   - Consulta los registros reales de `TinyDB` (`incidents` table) con 94 incidentes reales, sin datasets falsos.
   - Solo lectura (`GET`), con timeout explícito y numérico de `5.0` segundos.
2. **Estado Extendido (`services/agent/state.py`):**
   - Agregados campos `intent: Optional[str]` y `tool_data: Optional[Dict[str, Any]]`.
3. **Nodos y Aristas Condicionales (`services/agent/nodes.py`, `services/agent/graph.py`):**
   - `classify_intent_node`: Enruta autónomamente a `incident_tool` (tickets) o `retrieve` (documentos RAG).
   - `incident_tool_node`: Ejecuta la consulta protegida con `try...except`.
   - `format_tool_answer_node`: Formatea la respuesta con datos reales.
   - `tool_fallback_node`: Mensaje honesto si el ticket no existe o la tool falla (*"No pude confirmar el estado de ese ticket ahora mismo"*).
4. **Endpoint REST (`services/api/routes/agent.py`):**
   - Protegido con **Auth Guard Standard** (`get_current_user`).
   - Retorna `execution_trace`, `intent` y `tool_data` para auditoría total.
5. **Suite de Evaluación (`tests/pipelines/test_agent_evals.py`):**
   - 11 evals verificando routing de tickets, routing de RAG, fallbacks y timeouts.

---

## 📋 Resumen de Cambios Realizados

### 1. Herramienta Externa de Tickets (`services/agent/tools.py`):
- Implementada función tipada `get_incident_ticket(ticket_identifier: str, timeout: float = 5.0)`.
- Lee datos reales del gestor de incidentes en TinyDB (94 registros históricos reales).
- Estrictamente de **solo lectura** (`GET`) con timeout explícito y numérico de 5.0 segundos.

### 2. Estado Extendido (`services/agent/state.py`):
- Agregados los campos `intent: Optional[str]` y `tool_data: Optional[Dict[str, Any]]`.

### 3. Nodos y Aristas Condicionales (`services/agent/nodes.py`, `services/agent/graph.py`):
- `classify_intent_node`: Enruta autónomamente según la pregunta del usuario (`incident_tool` vs `retrieve`).
- `incident_tool_node`: Ejecuta la consulta protegido con `try...except` ante `TimeoutError` o caídas.
- `format_tool_answer_node`: Redacta la respuesta basada en datos fácticos reales del ticket.
- `tool_fallback_node`: Ruta honesta ante tickets inexistentes o fallos de red (*"No pude confirmar el estado de ese ticket ahora mismo"*).

### 4. Endpoint REST (`services/api/routes/agent.py`):
- Protegido por defecto con **Auth Guard Standard** (`get_current_user`).
- Retorna `execution_trace`, `intent` y `tool_data` para auditoría completa.

### 5. Suite de Evals y Calidad (`tests/pipelines/test_agent_evals.py`):
- 11 evals automatizados pasando al 100%.

