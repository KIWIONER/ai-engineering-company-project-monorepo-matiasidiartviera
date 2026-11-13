"""
services/agent/graph.py
Construcción, enrutamiento condicional y compilación del grafo del agente de soporte con LangGraph.
Orquesta RAG y herramientas externas (Tool de Incidentes) con checkpointing en memoria.
"""

from typing import Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from services.agent.state import AgentState
from services.agent.nodes import (
    validate_input_node,
    classify_intent_node,
    incident_tool_node,
    format_tool_answer_node,
    tool_fallback_node,
    retrieve_node,
    honest_refusal_node,
    generate_answer_node,
)

def route_after_validation(state:AgentState)-> str:
    """
    Arista condicional 1:
    Si hay error de validación (pregunta vacía), enruta al rechazo honesto.
    Si la pregunta es válida, avanza a clasificar la intención.
    """
    if state.get("error"):
        return "honest_refusal"
    return "classify_intent"

def route_after_intent(state:AgentState)-> str:
    """
    Arista condicional 2 (Enrutamiento autónomo):
    Si la pregunta es sobre tickets/incidencias, enruta a la tool externa.
    Si es sobre políticas/procedimientos, enruta al RAG.
    """
    if state.get("intent") == "incident_tool":
        return "incident_tool"
    return "retrieve"

def route_after_tool(state: AgentState)-> str:
    """
    Arista condicional 3 (Resiliencia de Tool):
    Si la tool recuperó datos reales del incidente, formatea la respuesta.
    Si la tool falló, agotó el timeout o el ticket no existe, activa la ruta de fallback.
    """
    if state.get("tool_data") is not None:
        return "format_tool_answer"
    return "tool_fallback"

def route_after_retrieval(state:AgentState) -> str:
    """
    Arista condicional 4 (RAG):
    Si se encontraron documentos relevantes sobre el umbral, genera respuesta.
    Si no hay contexto suficiente, enruta al rechazo honesto.
    """
    context = state.get("context", [])
    if context and len(context) > 0:
        return "generate_answer"
    return "honest_refusal"


def create_agent_graph(checkpointer:Optional[MemorySaver] = None):
    """
    Crea, conecta y compila el StateGraph del agente con RAG y Tools externas.
    La compilación falla en build-time si la topología tiene inconsistencias.
    """
    workflow= StateGraph(AgentState)

    # 1. Registrar nodos con responsabilidad única
    workflow.add_node("validate_input", validate_input_node)
    workflow.add_node("classify_intent", classify_intent_node)
    workflow.add_node("incident_tool", incident_tool_node)
    workflow.add_node("format_tool_answer", format_tool_answer_node)
    workflow.add_node("tool_fallback", tool_fallback_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("honest_refusal", honest_refusal_node)
    workflow.add_node("generate_answer", generate_answer_node)

     # 2. Conectar punto de entrada
    workflow.add_edge(START, "validate_input")
    # 3. Aristas condicionales de enrutamiento
    workflow.add_conditional_edges(
        "validate_input",
        route_after_validation,
        {
            "classify_intent": "classify_intent",
            "honest_refusal": "honest_refusal",
        },
    )
    workflow.add_conditional_edges(
        "classify_intent",
        route_after_intent,
        {
            "incident_tool": "incident_tool",
            "retrieve": "retrieve",
        },
    )
    workflow.add_conditional_edges(
        "incident_tool",
        route_after_tool,
        {
            "format_tool_answer": "format_tool_answer",
            "tool_fallback": "tool_fallback",
        },
    )
    workflow.add_conditional_edges(
        "retrieve",
        route_after_retrieval,
        {
            "generate_answer": "generate_answer",
            "honest_refusal": "honest_refusal",
        },
    )

    # 4. Conectar salidas hacia el final
    workflow.add_edge("honest_refusal", END)
    workflow.add_edge("generate_answer", END)
    workflow.add_edge("format_tool_answer", END)
    workflow.add_edge("tool_fallback", END)

    # 5. Compilar con checkpointer para persistencia y auditoría de estados
    active_checkpointer = checkpointer if checkpointer is not None else MemorySaver()
    compiled_app = workflow.compile(checkpointer=active_checkpointer)
    
    return compiled_app

# Instancia compilada por defecto
default_checkpointer = MemorySaver()
agent_app = create_agent_graph(checkpointer=default_checkpointer)

def run_agent(question: str, thread_id: str = "default-thread") -> AgentState:
    """
    Función de ejecución conveniente para correr una pregunta contra el grafo.
    Devuelve el estado final con su respuesta y execution_trace completo.
    """
    initial_state: AgentState = {
        "question": question,
        "intent": None,
        "context": [],
        "tool_data": None,
        "answer": "",
        "error": None,
        "execution_trace": [],
    }
    config = {"configurable": {"thread_id": thread_id}}
    final_state = agent_app.invoke(initial_state, config=config)
    return final_state