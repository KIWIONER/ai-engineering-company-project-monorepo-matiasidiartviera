# 🧠 LangGraph Agent Orchestrator Skill

> **Manual de ingeniería y guía operativa para construir, auditar y desplegar Agentes de IA basados en máquinas de estados con LangGraph.**

---

## 🎯 ¿Qué es esta Skill?

Es un marco de trabajo estandarizado que guía a desarrolladores y agentes de Inteligencia Artificial en la creación de **Agentes de IA Orquestados por Grafos**. 

Sustituye los pipelines lineales rígidos o scripts monolíticos (que actúan como "cajas negras") por una **arquitectura de máquina de estados** explícita, donde cada nodo tiene una única responsabilidad y cada decisión está controlada por aristas condicionales.

---

## 🚀 ¿Para qué sirve?

1. **Eliminar Alucinaciones:** Implementa guardias condicionales que evalúan la calidad de los documentos antes de generar una respuesta. Si no hay información suficiente o la consulta es inválida, bifurca inmediatamente hacia un **rechazo honesto** sin gastar tokens del LLM.
2. **Abrir la Caja Negra (Trazabilidad Total):** Obliga a que cada corrida genere un `execution_trace` consultable que registra qué nodos se ejecutaron y en qué orden.
3. **Persistencia e Inspección (Checkpointing):** Proporciona soporte nativo para guardar y consultar "fotos" (*snapshots*) del estado tras cada transición mediante identificadores de hilo (`thread_id`).
4. **Evaluación Continua y Determinista:** Establece una metodología de tests (`evals`) que validan el comportamiento del grafo, el orden de los nodos y el anclaje a las políticas corporativas sin depender de llamadas costosas en vivo.
5. **Base Sólida para Agentes con Herramientas (Tools):** Prepara la arquitectura para que en fases avanzadas se puedan conectar herramientas (bases de datos SQL, APIs externas, envíos de correo) simplemente agregando nuevos nodos al grafo sin tocar el resto del sistema.

---

## ⚖️ Comparativa: Pipeline Tradicional vs Agente Orquestado

| Característica | RAG Lineal / Loop Ingenuo | Agente Orquestado con esta Skill |
| :--- | :--- | :--- |
| **Control del Flujo** | Línea recta obligatoria (`while` o `query()`). | Máquina de estados con bifurcaciones dinámicas (`StateGraph`). |
| **Trazabilidad** | Solo devuelve la respuesta final; opaco. | `execution_trace` explícito paso a paso. |
| **Costes y Tokens** | Llama al LLM incluso si no hay datos. | Salidas rápidas que ahorran llamadas ante consultas vacías o sin contexto. |
| **Auditoría de Errores** | Difícil saber qué paso falló. | Aislamiento por nodo con tests unitarios e inspección de checkpoints. |
| **Escalabilidad** | Agregar capacidades nuevas rompe el flujo. | Agregar herramientas consiste únicamente en conectar un nodo nuevo. |

---

## 📁 Estructura Estándar que Produce

```text
services/
  <agent-name>/
    __init__.py
    state.py        # Esquema mínimo fuertemente tipado (TypedDict)
    nodes.py        # Nodos desacoplados con responsabilidad única
    graph.py        # Ensamblado del StateGraph, routers condicionales y compile()
tests/
  pipelines/
    test_agent_evals.py # Suite de evals sobre trace, bifurcaciones y anclaje
services/api/routes/
    <agent-name>.py # Endpoint REST seguro con Auth Guard (Depends(get_current_user))
```

---

## 🛠️ ¿Cuándo utilizar esta Skill?

* Cuando necesites convertir un prototipo RAG en un sistema de **grado de producción**.
* Cuando tu cliente o líder técnico exija **auditar y explicar** por qué el agente respondió lo que respondió.
* Cuando el agente deba tomar **decisiones condicionales** antes de responder (ej. verificar permisos, validar entradas o usar herramientas específicas).
* Cuando quieras asegurar que las respuestas estén estrictamente ancladas a manuales y políticas corporativas sin inventar datos.

