<<<<<<< Updated upstream
# Implementation Plan: Sistemas en Tiempo Real — Streaming de Chat por WebSocket (Parte 2 de 2)

**Nivel de Complejidad:** Nivel 3 (Arquitectura Bidireccional — WebSocket Pub/Sub, Streaming Token-a-Token, Abort Real y Rehidratación)  
**Rama de Trabajo:** `feature/websocket-chat`  
**Documentos de Referencia:** `.github/STRATEGY.md`, `BRIEFING (real-time-communication)`, `AGENTS.md`, `services/agent/graph.py`, `services/api/routes/agent.py`

---

## 1. 📐 PACK 1: ARCHITECT (Ideación y Decisión Técnica)

### 1.1 Árbol de Pensamiento (Tree of Thoughts - ToT)
Se evaluaron tres opciones para lograr streaming token-a-token e interrupción en tiempo real del agente `first_line_support`:

- **Rama A (SSE para salida + `POST /agent/abort` por HTTP separado):**
  - *Ventajas:* Reutiliza SSE de la Parte 1.
  - *Riesgos:* Dos canales separados introducen condiciones de carrera entre el stream de lectura y el endpoint de abort; no cumple el criterio de aceptación de `STRATEGY.md` ("el canal debe ser bidireccional", "SSE ya no alcanza"). **Descartada.**
- **Rama B (Usar LangGraph `interrupt()` HITL para detener respuestas):**
  - *Ventajas:* Mecanismo nativo de grafos.
  - *Riesgos:* Viola explícitamente `STRATEGY.md`: LangGraph `interrupt()` pausa nodos entre transiciones esperando aprobación humana, **no** cancela un stream de tokens en vuelo. **Descartada.**
- **Rama C (WebSocket Bidireccional + Pub/Sub por Sesión `chat.<session_id>` + Cancelación de `asyncio.Task` - Elegida):**
  - *Ventajas:*
    1. Canal único full-duplex: el cliente envía `user_message` e `interrupt_requested` mientras recibe `token_chunk` concurrentemente.
    2. Desacopla al productor (ejecución del grafo `agent_app`) de los consumidores (múltiples clientes WebSocket suscritos a `chat.<session_id>`), permitiendo observadores/supervisores en vivo sin duplicar llamadas al agente.
    3. Al recibir `interrupt_requested`, cancela la `asyncio.Task` en vuelo (`task.cancel()`), abortando genuinamente el stream sin emitir más `token_chunk`, conservando el mensaje parcial como `interrupted` y arrancando un turno nuevo con `new_input`.
    4. No modifica la lógica interna ni las herramientas de `services/agent/graph.py` ni `services/agent/nodes.py`.

---

### 1.2 Análisis del Panel de 3 Expertos

#### 1. UX / Product Specialist
- **Efecto de escritura en vivo:** El asistente muestra un indicador de escritura y va añadiendo cada `token_chunk` conforme llega, sin reemplazar todo el mensaje al final.
- **Control de interrupción natural:** Mientras el agente responde, el usuario puede enviar un nuevo mensaje o pulsar "Interrumpir y redirigir". El mensaje parcial del asistente permanece visible en el historial con un badge `"Interrumpido"` (`status: "interrupted"`), y la respuesta redirigida aparece debajo como un turno nuevo.
- **Reconexión transparente:** Si se pierde la red, la UI muestra `"Reconectando..."` con backoff exponencial, reconecta usando el mismo `session_id` y recibe `session_snapshot` para restaurar la conversación completa sin perder el hilo.

#### 2. Dev Lead / Software Architect
- **Gestor Pub/Sub y Sesiones (`services/api/ws_chat_manager.py`):**
  - Entidad `ChatSession` alineada al BRIEFING: `session_id`, `agent_id="first_line_support"`, `user_id`, `client_id`, `status` (`"active" | "interrupted" | "closed"`), `created_at` y lista ordenada de mensajes (`message_id`, `role`, `content`, `status`, `created_at`).
  - Canal `chat.<session_id>` con conjunto de suscriptores (`WebSocket` / `asyncio.Queue`), garantizando broadcast único por sesión sin duplicar ejecuciones del agente.
  - Control de tarea activa (`active_task: asyncio.Task`) por sesión: cuando llega `interrupt_requested`, se cancela la tarea activa, se espera su cierre limpio, se marca el mensaje parcial como `interrupted`, se publica `generation_interrupted` y se lanza un turno nuevo si `new_input` está presente.
- **Adaptador de Streaming para `agent_app` (`services/api/routes/agent.py`):**
  - Invoca `agent_app.astream(initial_state, config={"configurable": {"thread_id": session_id}}, stream_mode=["messages", "updates"])` sin alterar `services/agent/`.
  - Si un nodo emite `AIMessageChunk` nativos, se transmiten token a token; si un nodo determinista/RAG (`generate_answer`, `format_tool_answer`, `honest_refusal`, `tool_fallback`) entrega el texto completo en `updates`, el adaptador lo divide en tokens y lo emite progresivamente con puntos de suspensión `await asyncio.sleep(...)` para que `task.cancel()` aborte instantáneamente entre tokens.

#### 3. Security & Compliance Specialist (Auth Guard Standard)
- **Autenticación en Handshake WebSocket:**
  - Extrae el JWT desde `?token=...` en la URL del handshake (y opcionalmente soporta un primer frame `{ "event": "auth", "data": { "token": "..." } }` si no vino en query string).
  - Valida el JWT con la misma lógica/clave de `services/api/routes/auth.py` (`decode_access_token` / `SECRET_KEY`). Si falta o es inválido, cierra inmediatamente el socket con código `1008` (Policy Violation) antes de emitir `session_snapshot` o aceptar eventos.
- **Exigencia de `session_id`:** Requerido en el handshake (`/agent/ws/{session_id}` o `?session_id=...`).
=======
# Implementation Plan — Prácticas Seguras en la Integración de IA y Marco NIST CSF 2.0 (Nexova)

> **Rama objetivo:** `feature/nist-security-practices` *(crear desde `main` tras mergear el PR anterior)*  
> **Nivel de Complejidad (`code-refinement-suite`):** **Nivel 4/5 (Sistema Cognitivo/Agéntico, Gobernanza Viva y Cumplimiento Multi-Jurisdicción)**  
> **Skills Aplicadas:**
> - [code-refinement-suite/SKILL.md](file:///workspaces/ai-engineering-company-project-monorepo-matiasidiartviera/skills/code-refinement-suite/SKILL.md)
> - [ai-governance-nist/SKILL.md](file:///workspaces/ai-engineering-company-project-monorepo-matiasidiartviera/skills/ai-governance-nist/SKILL.md)
> - [security-audit-suite/SKILL.md](file:///workspaces/ai-engineering-company-project-monorepo-matiasidiartviera/skills/security-audit-suite/SKILL.md)
> **Referencias Rectoras:**
> - [STRATEGY.md](file:///workspaces/ai-engineering-company-project-monorepo-matiasidiartviera/.github/STRATEGY.md)
> - [nexova-cybersecurity-BRIEFING.md](file:///workspaces/ai-engineering-company-project-monorepo-matiasidiartviera/docs/nexova-cybersecurity-BRIEFING.md)

---

## 1. PACK 1: ARCHITECT — Ideación, Gobernanza en Tiempo de Diseño y Threat Modeling

### 1.1 Contexto Regulatorio y Alcance Real en Nexova
Nexova opera entre **Valencia (España)** y **Miami (EE. UU.)**, procesando datos personales de candidatos (CVs, historial, pretensión salarial), clientes de outsourcing y prospectos comerciales:
- **España / UE:** **RGPD** (minimización, limitación de propósito, supervisión humana en decisiones automatizadas y notificación a la **AEPD en 72 horas**) + **Ley de IA de la UE** (scoring de candidatos = **Alto Riesgo**).
- **EE. UU. (Florida):** **FIPA** (notificación en **30 días**) y **FCRA** (si aplica *background check* en selección).
- **4 Sistemas de IA en Inventario:**
  1. Pipeline de selección asistida (scoring de CVs).
  2. RAG sobre base de candidatos / conocimiento (`data/pipelines/rag.py`, `POST /knowledge/query`).
  3. Agente de soporte de primera línea (`services/agent/`, `POST /agent/query`, `mcps/company_tools/`).
  4. Agente de prospección comercial y flujos RFP (`data/pipelines/rfp_intake/`).

### 1.2 Análisis Tree of Thoughts (ToT) — Arquitectura de Contención y Gobernanza
- **Opción A (Solo informe NIST + prompts más estrictos):** Cumple el papel, pero falla en producción: un `system prompt` no detiene inyecciones ni controla costos ni valida salidas. *Descartada.*
- **Opción B (Bloquear cada acción con HITL indiscriminado):** Genera fatiga de aprobación ("aprobar todo sin leer") y degrada la experiencia. *Descartada.*
- **Opción C (Elegida — Contención Determinista + Gobernanza Viva NIST):**
  1. **Mapa previo de superficie LLM + Inventario vivo** (con responsables internos y control de terceros: OpenAI / Qdrant).
  2. **Puerta determinista `action_gate` (`review_action`) *fail-secure*:** separa acciones reversibles (`allowed`) de irreversibles o masivas > `BULK_THRESHOLD` (`confirm` → HITL con detalle concreto) y rechaza cualquier acción/argumento desconocido (`denied`).
  3. **Protección de disponibilidad y costos:** *rate limiting* verificable (`429`) en `POST /agent/query` y `POST /knowledge/query` + tope de longitud de entrada.
  4. **Minimización RGPD + Logging forense:** extraer solo campos permitidos antes de invocar al modelo y registrar decisión, modelo, usuario y herramienta invocada redactando secretos/PII cruda.

### 1.3 Threat Modeling & FMEA Inicial (Basado en lectura del repo)
- **`.env.example`:** No documenta explícitamente `OPENAI_API_KEY` / `LLM_API_KEY` / `QDRANT_URL` usados en `data/pipelines/rag.py:30-34`.
- **Agotamiento de recursos (`services/api/routes/agent.py:71`, `knowledge.py:66`):** Endpoints que disparan LLMs sin *rate limiting* por usuario ni validación de tamaño máximo de entrada.
- **Validación de salida antes de ejecutar acciones (`services/agent/`):** Existe `GuardrailTracker` y HITL en `memory_evaluator.py`, pero falta una puerta unificada `review_action(action)` que clasifique explícitamente las **4 acciones irreversibles del Briefing §5** (descartar candidato, enviar propuesta/contrato, resolver ticket con queja/PII, cambio masivo ATS).
- **Trazabilidad forense:** Falta un registro estructurado uniforme que capture *qué acción tomó el agente, con qué modelo, para qué usuario y por qué*, sin filtrar PII/credenciales.

---

## 2. PACK 2: PLANNER — Invariantes y Edge Cases Críticos

### 2.1 Invariantes de Seguridad por Diseño
1. **No confiar en entradas ni salidas del modelo:** Toda salida del LLM (texto, argumentos de tool, acciones propuestas) pasa por validación determinista externa al modelo antes de ejecutarse.
2. **Fail-Secure en Puerta de Acciones:** Cualquier acción sin `type`, no registrada en `SAFE_ACTIONS`/`CONFIRM_ACTIONS` o con argumentos fuera de dominio devuelve `"denied"`.
3. **HITL con Detalle Concreto (Briefing §5):** Las 4 acciones irreversibles exigen confirmación humana explícita mostrando recurso afectado, destinatario e impacto (nunca un "¿Proceder?" genérico).
4. **Responsabilidad Compartida Explícita:** Usar OpenAI/proveedores no transfiere la responsabilidad de Nexova como *Desplegador* / *Responsable del tratamiento*.

### 2.2 Edge Cases Críticos Exigidos en Pruebas (Regla de Diseño 3)
1. **Prompt Injection (Directa e Indirecta, Briefing §4):**
   - CV con texto oculto manipulando scoring + ticket malicioso de soporte cross-tenant → neutralizados determinísticamente.
2. **Puerta `action_gate` (*Default-Deny*):**
   - Acción desconocida (`drop_table`), acción sin `type` (`{}`), acción reversible masiva (`records > BULK_THRESHOLD`) y las 4 acciones irreversibles del Briefing §5 → deben devolver `"denied"` o `"confirm"`, nunca `"allowed"`.
3. **Rate Limiting y Agotamiento:**
   - Ráfaga de peticiones autenticadas sobre `POST /agent/query` / `POST /knowledge/query` superando la cuota por ventana → responde `429 Too Many Requests` sin invocar al modelo.
4. **Confirmaciones HITL con Mensaje Completo:**
   - Contradicciones (`"Sí. Pero mejor no"` / `"Sí. No estoy seguro"`) → denegadas por defecto.
>>>>>>> Stashed changes

---

### 1.3 Threat Modeling & FMEA

<<<<<<< Updated upstream
| Amenaza / Modo de Fallo | Riesgo / Impacto | Severidad | Mitigación Técnica |
| :--- | :--- | :---: | :--- |
| **Acceso sin JWT al WebSocket** | Cualquiera lee o interactúa con sesiones de soporte de clientes. | Crítica | Validación estricta del mismo JWT de `auth.py` en el handshake; cierre inmediato (`1008`) antes de enviar `session_snapshot`. |
| **Tokens "zombies" tras interrupción** | Llegan `token_chunk` de la respuesta vieja mezclados con la nueva. | Alta | Cancelación explícita de `asyncio.Task` + verificación de `generation_id` / `message_id` antes de publicar en `chat.<session_id>`, y espera (`await`) a que la tarea anterior termine antes de iniciar el nuevo turno. |
| **Desincronización tras caída de red** | Al reconectar, el chat aparece vacío y se pierde el contexto. | Alta | Emisión automática de `session_snapshot` al completar el handshake con todo el historial (`messages`, incluyendo mensajes `interrupted`) y uso del mismo `session_id` como `thread_id` de LangGraph. |
| **Múltiples observadores duplicando al agente** | 2 pestañas abiertas en la misma sesión ejecutan 2 veces al agente. | Alta | Productor único desacoplado en `ChatSessionManager`: solo la recepción de `user_message` / `interrupt_requested` dispara el productor, que publica en `chat.<session_id>` hacia todos los sockets suscritos. |

---

## 2. 📝 PACK 2: PLANNER (Contrato de Datos y Flujo)

### 2.1 Contrato WebSocket (`BRIEFING` Parte 2)

#### Entidad `ChatSession`
```python
class ChatSession(BaseModel):
    session_id: str
    agent_id: str = "first_line_support"
    user_id: str
    client_id: Optional[str] = None
    status: Literal["active", "interrupted", "closed"] = "active"
    created_at: str
```

#### Eventos Cliente → Servidor
- `user_message`:
  ```json
  {"event": "user_message", "data": {"session_id": "chat_0157", "text": "..."}}
  ```
- `interrupt_requested`:
  ```json
  {"event": "interrupt_requested", "data": {"session_id": "chat_0157", "new_input": "en realidad mi pregunta era sobre la factura"}}
  ```

#### Eventos Servidor → Cliente
- `session_snapshot` (al conectar/reconectar):
  ```json
  {"event": "session_snapshot", "data": {"session_id": "chat_0157", "messages": []}}
  ```
- `token_chunk`:
  ```json
  {"event": "token_chunk", "data": {"session_id": "chat_0157", "token": "Claro", "sequence": 4}}
  ```
- `generation_interrupted`:
  ```json
  {"event": "generation_interrupted", "data": {"session_id": "chat_0157", "message_id": "msg_0321", "status": "interrupted"}}
  ```
- `generation_completed`:
  ```json
  {"event": "generation_completed", "data": {"session_id": "chat_0157", "message_id": "msg_0322"}}
  ```

### 2.2 Diagrama de Secuencia (Streaming + Interrupción)

```mermaid
sequenceDiagram
    autonumber
    actor Cliente as UI Chat (Next.js)
    participant WS as WebSocket Endpoint (/agent/ws/{session_id})
    participant PubSub as ChatSessionManager (chat.<session_id>)
    participant Agent as agent_app (LangGraph)

    Cliente->>WS: Connect WS (?token=JWT)
    WS->>WS: Verifica JWT y session_id
    WS->>PubSub: subscribe(session_id)
    PubSub-->>Cliente: {"event": "session_snapshot", "data": {"session_id": ..., "messages": [...]}}

    Cliente->>WS: {"event": "user_message", "data": {"session_id": ..., "text": "Hola"}}
    WS->>PubSub: start_generation(text) -> Task
    PubSub->>Agent: astream(state, thread_id=session_id)
    loop Token a token
        Agent-->>PubSub: token
        PubSub-->>Cliente: {"event": "token_chunk", "data": {"session_id": ..., "token": ..., "sequence": n}}
    end

    Note over Cliente,PubSub: Usuario interrumpe a mitad de respuesta
    Cliente->>WS: {"event": "interrupt_requested", "data": {"session_id": ..., "new_input": "sobre mi factura"}}
    WS->>PubSub: interrupt_and_redirect(new_input)
    PubSub->>PubSub: task.cancel() -> aborta stream inmediatamente
    PubSub->>PubSub: Marca mensaje parcial status="interrupted"
    PubSub-->>Cliente: {"event": "generation_interrupted", "data": {"session_id": ..., "message_id": "msg_1", "status": "interrupted"}}
    PubSub->>Agent: Nuevo turno con new_input (thread_id=session_id)
    Agent-->>PubSub: Nuevos tokens
    PubSub-->>Cliente: token_chunk ... -> generation_completed
```

---

## 3. 💻 PACK 3: CODER (Mapa de Implementación Paso a Paso)

1. **Backend — Auth helper + Gestor Pub/Sub (`services/api/ws_chat_manager.py`):**
   - Modelo `ChatSession` y `ChatMessage` con los campos exactos del BRIEFING.
   - `ChatSessionManager` con canales `chat.<session_id>`, registro de múltiples suscriptores WebSocket, historial en memoria para `session_snapshot`, y cancelación segura de `asyncio.Task` para abort real.
2. **Backend — Endpoint WebSocket en `services/api/routes/agent.py`:**
   - Reutilizar/exponer validación JWT en `services/api/routes/auth.py` (si no existe función pública reutilizable para WS).
   - Añadir `@router.websocket("/ws/{session_id}")` en `services/api/routes/agent.py` conectado al `ChatSessionManager` y `agent_app`.
3. **Pruebas Automatizadas (`tests/api/test_websocket_chat.py`):**
   - Test 1: Rechazo sin JWT válido.
   - Test 2: Handshake con `session_id` devuelve `session_snapshot`.
   - Test 3: Flujo `user_message` → múltiples `token_chunk` → `generation_completed`.
   - Test 4: Flujo `interrupt_requested` a mitad de respuesta → aborta generación (`generation_interrupted` con `status="interrupted"`), no emite más tokens del turno viejo, conserva mensaje parcial y arranca nuevo turno con `new_input`.
   - Test 5: Reconexión con el mismo `session_id` restaura el historial completo en `session_snapshot`.
   - Test 6: Múltiples clientes suscritos a `chat.<session_id>` reciben los mismos eventos sin duplicar invocaciones al agente.
4. **Frontend — Hook + Interfaz de Chat en Tiempo Real (`uis/backoffice/src/hooks/useSupportChatWS.ts` y `uis/backoffice/src/app/support-chat/page.tsx` o integración en `knowledge`):**
   - Cliente WebSocket con `?token=...`, `session_id` persistente, streaming token-a-token en vivo, control de interrupción/redirección dejando visible el mensaje marcado como `interrupted`, y reconexión exponencial con rehidratación automática desde `session_snapshot`.
   - Enlace de navegación desde el Backoffice para acceder directamente al Chat de Soporte en Vivo.

---

## 4. 🛡️ PACK 4: AUDITOR (Verificación y Preguntas de Diseño PR)

- **Comandos de verificación:**
  - `uv run pytest tests/api/test_websocket_chat.py -v`
  - `cd uis/backoffice && npx tsc --noEmit`
- **Protocolo Git:**
  - Rama `feature/websocket-chat` desde `main`.
  - ⚠️ **Regla Inviolable:** NUNCA realizar `git push` automático sin consentimiento explícito del usuario.

---

## 🗺️ Mapa de Trabajo por Fases (Roadmap)

### Fase 1: Gestor Pub/Sub y Sesiones WebSocket (`services/api/ws_chat_manager.py`)
- [ ] 1.1 Definir modelos Pydantic del contrato (`ChatSession`, `ChatMessage`) alineados al BRIEFING de Nexova (`agent_id="first_line_support"`, `status`: `active | interrupted | closed`).
- [ ] 1.2 Implementar `ChatSessionManager` con canales Pub/Sub `chat.<session_id>` desacoplando al productor del agente de múltiples consumidores WebSocket.
- [ ] 1.3 Implementar historial por sesión y generación de `session_snapshot` para rehidratación en reconexión.
- [ ] 1.4 Implementar cancelación de tarea en vuelo (`asyncio.Task.cancel()`) para abortar genuinamente la generación ante `interrupt_requested`, marcando el mensaje parcial como `interrupted` y lanzando el nuevo turno con `new_input`.

### Fase 2: Endpoint WebSocket y Adaptador LangGraph (`services/api/routes/agent.py`)
- [ ] 2.1 Validar el mismo JWT del backoffice en el handshake WebSocket (`?token=...` o primer frame `auth`) usando `get_current_user` de `services/api/routes/auth.py` (cierre `1008` si falta o es inválido).
- [ ] 2.2 Exigir `session_id` en la ruta `/agent/ws/{session_id}` y usarlo como `thread_id` en LangGraph `agent_app.astream(...)`.
- [ ] 2.3 Implementar adaptador de streaming token-a-token para `agent_app` (sin modificar `services/agent/graph.py` ni sus herramientas) emitiendo `token_chunk`, `generation_completed` y `generation_interrupted`.

### Fase 3: Pruebas Automatizadas (`tests/api/test_websocket_chat.py`)
- [ ] 3.1 Verificar rechazo del handshake sin JWT válido.
- [ ] 3.2 Verificar emisión de `session_snapshot` al conectar con `session_id`.
- [ ] 3.3 Verificar flujo `user_message` → `token_chunk` (secuenciales) → `generation_completed`.
- [ ] 3.4 Verificar flujo `interrupt_requested` a mitad de stream → abort real (`generation_interrupted` con `status="interrupted"`, cero tokens residuales, conservación del mensaje parcial y nuevo turno reflejando `new_input`).
- [ ] 3.5 Verificar reconexión con el mismo `session_id` restaurando el hilo completo y difusión Pub/Sub a múltiples observadores sin duplicar invocaciones al agente.

### Fase 4: Interfaz de Chat en Tiempo Real (`uis/backoffice/`)
- [ ] 4.1 Crear hook `uis/backoffice/src/hooks/useSupportChatWS.ts` con `WebSocket`, `?token=...`, `session_id` persistente, reconexión con backoff exponencial y rehidratación desde `session_snapshot`.
- [ ] 4.2 Crear vista de chat de soporte (`uis/backoffice/src/app/support-chat/page.tsx`) con renderizado de tokens en vivo, botón/flujo de interrupción y redirección en mitad de respuesta, y badge visible de `interrupted`.
- [ ] 4.3 Añadir enlace de navegación en el Backoffice y validar compilación TypeScript (`cd uis/backoffice && npx tsc --noEmit`).

### Fase 5: Auditoría Final y Protocolo Git (PACK 4)
- [ ] 5.1 Verificar que `services/agent/` (lógica interna y herramientas) permanece intacto y no se mezclan payloads RFP/SSE de la Parte 1.
- [ ] 5.2 Ejecutar `uv run pytest tests/api/test_websocket_chat.py -v` y `npx tsc --noEmit` tras el último cambio.
- [ ] 5.3 Solicitar consentimiento explícito del usuario antes de realizar `git push` hacia `feature/websocket-chat`.
=======
### Fase 0: Preparación de Rama y Mapeo Previo (Antes de tocar código)
- [ ] Confirmar merge del PR `feature/owasp-top10-audit` en `main`, hacer `git pull` y crear la rama `git switch -c feature/nist-security-practices`.
- [x] Revisar `.env.example` y verificar en todo el monorepo que no existan API keys ni credenciales hardcoded (`quick_security_scan.sh`).
- [x] Crear carpeta de entrega `docs/security/nist-security-practices/` y redactar el mapa de **todos los puntos donde un LLM recibe input externo** (usuario, documentos RAG/Qdrant, respuestas MCP, archivos CVs/RFPs) en `README.md` / inventario.

### Fase 1: Inventario Vivo de IA y Responsabilidad Compartida (`Govern` + `Identify`)
- [x] Completar `docs/security/nist-security-practices/ai-inventory.md` usando `skills/ai-governance-nist/resources/ai-inventory-template.md` con los 4+ componentes de Nexova, responsable interno asignado, proveedor/modelo, política de retención/no-entrenamiento, nivel de riesgo (EU AI Act Alto Riesgo en scoring), revisión humana y plan ante fallos.
- [x] Documentar la matriz de responsabilidad compartida (Nexova como Desplegador / Responsable vs. Proveedores como Encargados).

### Fase 2: Seguridad por Diseño en Backend y Agentes (`Protect` + `Detect`)
- [x] Actualizar `.env.example` documentando de forma segura las variables de IA (`OPENAI_API_KEY`, `LLM_API_KEY`, `LLM_MODEL`, `QDRANT_URL`) sin valores reales.
- [x] Implementar puerta determinista de validación de acciones (`services/agent/action_gate.py` con `review_action`, `SAFE_ACTIONS`, `CONFIRM_ACTIONS` para las 4 acciones irreversibles del Briefing §5 y `BULK_THRESHOLD`) + validación de argumentos.
- [x] Implementar wrapper de minimización de datos (RGPD) y **logging forense estructurado** (`services/agent/audit_logger.py` o integración en `services/agent/nodes.py`) registrando qué acción tomó el agente, usuario, modelo y motivo, redactando PII/secretos.
- [x] Implementar **rate limiting verificable** (`429 Too Many Requests`) + límite de longitud de entrada en `POST /agent/query` (`services/api/routes/agent.py`) y `POST /knowledge/query` (`services/api/routes/knowledge.py`).
- [x] Verificar/asegurar en código que ninguna de las 4 acciones irreversibles del Briefing §5 puede ejecutarse sin confirmación humana explícita.

### Fase 3: Informe NIST CSF 2.0 Completo (`Govern`..`Recover`)
- [x] Redactar `docs/security/nist-security-practices/nist-csf-report.md` usando `skills/ai-governance-nist/resources/nist-report-template.md`, cubriendo las **6 funciones NIST** (*Govern, Identify, Protect, Detect, Respond, Recover*) con al menos una acción concreta y priorizada por función.
- [x] Citar explícitamente el marco regulatorio de `nexova-cybersecurity-BRIEFING.md`: **RGPD (AEPD 72h)**, **FIPA (Florida 30 días)**, **FCRA** (si aplica *background check*) y **Ley de IA de la UE**.
- [x] Documentar cada brecha no corregida en este ciclo con su riesgo y mitigación propuesta.

### Fase 4: Verificación, Pruebas Reproducibles y Compuerta Pre-Push (`PACK 4: AUDITOR`)
- [x] Crear/ampliar suite de tests `tests/test_nist_security_practices.py` verificando: Prompt Injection (§4), Rate Limiting (`429`), `action_gate` (*fail-secure* + 4 acciones irreversibles HITL), minimización de contexto y logging forense verificable.
- [x] Ejecutar `uv run pytest tests/test_nist_security_practices.py tests/test_owasp_security_audit.py tests/pipelines/test_agent_guardrails.py -v` y `bash skills/security-audit-suite/scripts/quick_security_scan.sh .`.
- [x] Preparar descripción del PR enlazando el test de Prompt Injection y explicando brechas pendientes y por qué (solicitar consentimiento explícito antes de `git push`).
>>>>>>> Stashed changes

---

## ⚙️ Métodos Aplicados (Code Refinement Suite)
<<<<<<< Updated upstream

1. **Tree of Thoughts (ToT):** Comparativa formal entre SSE+HTTP abort, LangGraph HITL `interrupt()`, y WebSocket bidireccional con Pub/Sub + cancelación de `asyncio.Task`.
2. **Panel de 3 Expertos (UX, Dev Lead, Security):** Equilibrio entre escritura en vivo + visibilidad de mensajes `interrupted`, desacoplamiento productor/consumidor en `chat.<session_id>`, y validación JWT estricta en handshake.
3. **Threat Modeling & FMEA:** Mitigación de acceso no autorizado (`1008`), tokens zombies tras interrupción (`task.cancel()` + espera explícita), pérdida de contexto en reconexión (`session_snapshot`), y duplicación de agente ante múltiples observadores.
4. **Chain of Verification (CoVe) & Wiring Check:** Contrastado contra `services/agent/graph.py`, `services/agent/nodes.py`, `data/pipelines/rag.py`, y `services/api/routes/auth.py`.
5. **Test-Driven Refinement (TDD):** Pruebas automatizadas de contrato WebSocket (`token_chunk`, `generation_interrupted`, `generation_completed`, `session_snapshot`) y reconexión antes de cerrar el ciclo.

=======
- **Tree of Thoughts (ToT) & Design-Time Governance:** Se evaluaron alternativas antes de elegir contención determinista fuera del modelo (`action_gate` + *rate limiting* + minimización RGPD + logging forense) alineada con `ai-governance-nist`.
- **Step-Back & Invariantes:** Se fijaron invariantes *fail-secure* sobre los dos flujos no confiables (entrada al modelo y salida del modelo) y responsabilidad compartida Nexova/proveedores.
- **Chain of Verification (CoVe) & TDD:** Cada control nuevo (rate limit `429`, `review_action`, logging y Prompt Injection) será verificado contra el código real y demostrado con tests reproducibles en `uv run pytest`.
- **Adversarial Red Teaming & Security Gate:** Validación pre-push con `security-audit-suite` (`quick_security_scan.sh`), pruebas de contradicción HITL y verificación de cero credenciales hardcoded.
>>>>>>> Stashed changes
