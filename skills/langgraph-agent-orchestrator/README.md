# 🧠 LangGraph Agent Orchestrator Skill

> **Manual de ingeniería y estándar arquitectónico para construir, auditar y desplegar Agentes de IA Híbridos basados en máquinas de estados con LangGraph (RAG Documental + Herramientas Operativas en Tiempo Real).**

---

## 🎯 ¿Qué es esta Skill?

Es un marco de trabajo estandarizado que guía a desarrolladores y agentes de Inteligencia Artificial en la creación de **Agentes de IA Orquestados por Grafos**. 

Sustituye los pipelines lineales rígidos o scripts monolíticos (que actúan como "cajas negras") por una **arquitectura de máquina de estados** explícita, donde cada nodo tiene una única responsabilidad y cada decisión está controlada por aristas condicionales y enrutamiento autónomo.

---

## 🚀 ¿Para qué sirve?

1. **Diferenciación Arquitectónica: Conocimiento vs Datos en Vivo:**
   - **RAG:** Se reserva para manuales, políticas y documentación corporativa relativamente estables.
   - **Tools:** Resuelve consultas operativas en vivo (tickets de soporte, inventario, precios) llamando a APIs existentes en tiempo real, evitando el grave error de indexar datos cambiantes en bases vectoriales.
2. **Enrutamiento Autónomo de Intenciones:**
   - Clasifica la consulta del usuario y bifurca hacia la herramienta adecuada o hacia el recuperador vectorial sin requerir parámetros del usuario.
3. **Eliminar Alucinaciones y Resiliencia Defensiva:**
   - **Rechazo Honesto documental:** Si los fragmentos no superan el umbral de similitud (`min_score < 0.70`), rechaza la consulta sin llamar al LLM.
   - **Fallback Honesto de herramientas:** Si la API externa no responde en 5 segundos (`timeout=5.0s`), se cae la red o el registro no existe, responde honestamente (*"No pude confirmar el estado de ese ticket ahora mismo"*) en vez de lanzar un error 500 o inventar un estado falso.
4. **Abrir la Caja Negra (Trazabilidad Total):**
   - Obliga a que cada corrida genere un `execution_trace` consultable que registra qué nodos se ejecutaron y en qué orden.
5. **Persistencia e Inspección (Checkpointing):**
   - Proporciona soporte nativo para guardar y consultar "fotos" (*snapshots*) del estado tras cada transición mediante identificadores de hilo (`thread_id`).
6. **Evaluación Continua y Determinista:**
   - Establece una suite de evals (`tests/pipelines/test_agent_evals.py`) que validan el comportamiento del grafo, el orden de los nodos, la llamada a tools y la resiliencia ante timeouts.

---

## ⚖️ Comparativa: Pipeline Tradicional vs Agente Orquestado

| Característica | RAG Lineal / Loop Monolítico | Agente Orquestado con esta Skill |
| :--- | :--- | :--- |
| **Control del Flujo** | Línea recta obligatoria (`while` o `query()`). | Máquina de estados con bifurcaciones dinámicas (`StateGraph`). |
| **Datos Operativos** | Intenta meter tickets en vectores (obsoleto). | Consulta APIs en vivo con timeout estricto (`GET`, 5.0s). |
| **Trazabilidad** | Solo devuelve la respuesta final; opaco. | `execution_trace` explícito paso a paso. |
| **Costes y Tokens** | Llama al LLM para todo tipo de consulta. | Salidas rápidas y formateo directo para herramientas operativas. |
| **Resiliencia** | Una excepción rompe el servidor (error 500). | Rutas de fallback honesto ante timeouts o 404. |
| **Auditoría de Errores** | Difícil saber qué paso falló. | Aislamiento por nodo con tests unitarios e inspección de checkpoints. |

---

## 📁 Estructura Estándar que Produce

```text
services/
  agent/
    __init__.py
    state.py        # Esquema mínimo fuertemente tipado (intent, context, tool_data, trace)
    tools.py        # Herramientas de solo lectura (GET) con timeout numérico explícito (5.0s)
    nodes.py        # Nodos desacoplados con responsabilidad única y try/except defensivo
    graph.py        # Ensamblado del StateGraph, routers condicionales y compile()
tests/
  pipelines/
    test_agent_evals.py # Suite de evals sobre trace, rutas RAG, rutas Tool y fallbacks
services/api/routes/
    agent.py        # Endpoint REST seguro con Auth Guard (Depends(get_current_user))
```

---

## 🛠️ ¿Cuándo utilizar esta Skill?

* Cuando necesites orquestar un agente que combine **documentación oficial (RAG)** con **consultas operativas en vivo (APIs/BD)**.
* Cuando el agente deba tomar **decisiones autónomas de enrutamiento** según la intención del usuario.
* Cuando tu cliente o líder técnico exija **auditar y explicar** cada paso de la ejecución (`execution_trace`).
* Cuando se requiera **resiliencia de nivel empresarial**: cero caídas ante timeouts y respuestas honestas ante datos no encontrados.
